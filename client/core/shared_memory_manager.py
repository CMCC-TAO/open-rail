import logging
import os
import threading
import time
from multiprocessing import shared_memory
from typing import Any, Dict, Optional, Union

import numpy as np


class _CameraMetadata:
    """Immutable camera metadata and producer-owned ring buffers."""

    __slots__ = ("name", "shape", "dtype", "shm", "buffers", "next_index")

    def __init__(self, name, shape, dtype, shm, buffers):
        self.name = name
        self.shape = shape
        self.dtype = dtype
        self.shm = shm
        self.buffers = buffers
        self.next_index = 0


class FramePacket:
    """Fixed-capacity observation packet for the local producer/consumer queue."""

    __slots__ = (
        "camera_metadata", "camera_slots", "camera_timestamps",
        "camera_count", "field_keys", "field_values", "field_count", "nested",
        "outer_keys", "outer_values", "outer_count"
    )

    def __init__(self, camera_metadata, field_capacity):
        self.camera_metadata = camera_metadata
        self.camera_slots = [0] * len(camera_metadata)
        self.camera_timestamps = [0] * len(camera_metadata)
        self.camera_count = 0
        self.field_keys = [None] * field_capacity
        self.field_values = [None] * field_capacity
        self.field_count = 0
        self.nested = False
        self.outer_keys = [None] * field_capacity
        self.outer_values = [None] * field_capacity
        self.outer_count = 0

    def reset(self, nested, outer_items=()):
        self.camera_count = 0
        self.field_count = 0
        self.nested = nested
        self.outer_count = 0
        for key, value in outer_items:
            if self.outer_count >= len(self.outer_keys):
                break
            self.outer_keys[self.outer_count] = key
            self.outer_values[self.outer_count] = value
            self.outer_count += 1

    def to_observation_descriptors(self):
        """Build the legacy descriptor mapping only for recording/IPC."""
        result = {
            self.outer_keys[index]: self.outer_values[index]
            for index in range(self.outer_count)
        }
        if self.nested:
            nested = {}
            for index in range(self.field_count):
                nested[self.field_keys[index]] = self.field_values[index]
            result["obs"] = nested
            obs = nested
        else:
            obs = result
            # Flat observations (no "obs" key) must keep their non-camera fields
            # too, otherwise values such as ref_timestamp / obs.state would be
            # dropped when the packet crosses a process boundary.
            for index in range(self.field_count):
                obs[self.field_keys[index]] = self.field_values[index]

        for index in range(self.camera_count):
            camera = self.camera_metadata[index]
            slot_index = self.camera_slots[index]
            obs[camera.name] = {
                "transport": "shm",
                "name": camera.shm[slot_index].name,
                "shape": list(camera.shape),
                "dtype": str(camera.dtype),
                "slot_index": slot_index,
                "timestamp_ns": self.camera_timestamps[index],
            }
        return result


class SharedMemoryManager:
    """Own producer shared-memory slots and provide isolated reader caches."""

    def __init__(self, ring_size: int = 3) -> None:
        self.logger = logging.getLogger(__name__)
        self._ring_size = ring_size
        # Initialization may be called by setup code, but the runtime producer
        # is single-threaded and must not contend on a global lock per frame.
        self._init_lock = threading.Lock()
        self._camera_metadata: tuple[_CameraMetadata, ...] = ()
        self._camera_by_name: Dict[str, _CameraMetadata] = {}
        self._field_capacity = 16
        self._packet_template = None
        self._stale_blocks = []
        self._closed = False

    @staticmethod
    def disable_shared_memory_tracking_in_process() -> None:
        """Prevent attach-only readers from registering producer-owned blocks."""
        try:
            from multiprocessing import resource_tracker

            original_register = resource_tracker.register
            original_unregister = resource_tracker.unregister

            def register(name, resource_type):
                if resource_type == "shared_memory":
                    return
                return original_register(name, resource_type)

            def unregister(name, resource_type):
                if resource_type == "shared_memory":
                    return
                return original_unregister(name, resource_type)

            resource_tracker.register = register
            resource_tracker.unregister = unregister
        except Exception:
            pass

    def _safe_shm_name(self, camera_name: str, slot_index: int) -> str:
        return f"vla_{os.getpid()}_{camera_name.replace('.', '_')}_{slot_index}_{time.time_ns()}"

    def _create_slot(self, camera_name: str, slot_index: int, shape: tuple, dtype: np.dtype):
        required_nbytes = int(np.prod(shape, dtype=np.int64)) * int(np.dtype(dtype).itemsize)

        shm_obj = shared_memory.SharedMemory(
            create=True,
            size=required_nbytes,
            name=self._safe_shm_name(camera_name, slot_index),
        )
        return shm_obj

    def init_pool(
        self,
        camera_shape: Dict[str, Union[tuple, list]],
        camera_dtypes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create producer slots using shapes obtained from real camera frames."""
        if not isinstance(camera_shape, dict):
            return
        with self._init_lock:
            if self._camera_metadata:
                return
            metadata = []
            for camera_name, shape_value in camera_shape.items():
                if not str(camera_name).startswith("cam.") or shape_value is None:
                    continue
                shape = tuple(int(value) for value in shape_value)
                if len(shape) < 2:
                    continue
                dtype = np.dtype(
                    (camera_dtypes or {}).get(camera_name, np.uint8)
                )
                shm_slots = []
                buffers = []
                for slot_index in range(self._ring_size):
                    shm_obj = self._create_slot(camera_name, slot_index, shape, dtype)
                    shm_slots.append(shm_obj)
                    buffers.append(np.ndarray(shape, dtype=dtype, buffer=shm_obj.buf))
                camera_metadata = _CameraMetadata(
                    camera_name, shape, dtype, shm_slots, buffers
                )
                metadata.append(camera_metadata)

            self._camera_metadata = tuple(metadata)
            self._camera_by_name = {item.name: item for item in metadata}
            self._packet_template = FramePacket(self._camera_metadata, self._field_capacity)

    def encode_observation(self, observation: Dict[str, Any]) -> Dict[str, Any] | FramePacket:
        """Copy frames into preallocated slots and return a fixed-capacity packet."""
        if not isinstance(observation, dict):
            return observation
        nested = isinstance(observation.get("obs"), dict)
        obs = observation["obs"] if nested else observation
        if not isinstance(obs, dict):
            return observation

        if not self._camera_metadata:
            return observation

        packet = FramePacket(self._camera_metadata, self._field_capacity)
        outer_items = ((key, value) for key, value in observation.items() if key != "obs") if nested else ()
        packet.reset(nested, outer_items)
        for key, value in obs.items():
            camera = self._camera_by_name.get(str(key))
            if camera is not None and isinstance(value, np.ndarray):
                if tuple(value.shape) != camera.shape or np.dtype(value.dtype) != camera.dtype:
                    self.logger.warning("Camera shape/dtype changed for %s; frame skipped", key)
                    continue
                slot_index = camera.next_index
                camera.buffers[slot_index][...] = value
                packet.camera_slots[packet.camera_count] = slot_index
                packet.camera_timestamps[packet.camera_count] = time.time_ns()
                packet.camera_count += 1
                camera.next_index = (slot_index + 1) % self._ring_size
            elif packet.field_count < len(packet.field_keys):
                packet.field_keys[packet.field_count] = key
                packet.field_values[packet.field_count] = value
                packet.field_count += 1
        return packet

    @staticmethod
    def decode_observation(
        step_state: Dict[str, Any],
        shm_cache: Dict[str, Any],
        copy: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Attach and copy frames using the cache owned by one reader."""
        logger = logging.getLogger(__name__)
        if isinstance(step_state, FramePacket):
            decoded_obs = {}
            for index in range(step_state.camera_count):
                camera = step_state.camera_metadata[index]
                slot_index = step_state.camera_slots[index]
                decoded_obs[camera.name] = camera.buffers[slot_index]
            for index in range(step_state.field_count):
                decoded_obs[step_state.field_keys[index]] = step_state.field_values[index]
            result = {
                step_state.outer_keys[index]: step_state.outer_values[index]
                for index in range(step_state.outer_count)
            }
            if step_state.nested:
                result["obs"] = decoded_obs
                return result
            return decoded_obs
        if not isinstance(step_state, dict):
            return step_state
        nested = isinstance(step_state.get("obs"), dict)
        obs = step_state["obs"] if nested else step_state
        if not isinstance(obs, dict):
            return step_state

        decoded_obs = dict(obs)
        for camera_name, payload in obs.items():
            if not str(camera_name).startswith("cam."):
                continue
            if not (isinstance(payload, dict) and payload.get("transport") == "shm"):
                continue
            shm_name = payload.get("name")
            shape = payload.get("shape")
            dtype_str = payload.get("dtype")
            if not shm_name or shape is None or dtype_str is None:
                logger.warning("Invalid shm descriptor for %s", camera_name)
                return None
            try:
                shm_obj = shm_cache.get(shm_name)
                if shm_obj is None:
                    shm_obj = shared_memory.SharedMemory(name=shm_name)
                    shm_cache[shm_name] = shm_obj
                frame_view = np.ndarray(tuple(shape), dtype=np.dtype(dtype_str), buffer=shm_obj.buf)
                decoded_obs[camera_name] = frame_view.copy() if copy else frame_view
            except FileNotFoundError:
                logger.warning("Shared memory block not found for %s: %s", camera_name, shm_name)
                return None
            except Exception:
                logger.exception("Failed to decode shm frame for %s", camera_name)
                return None

        decoded_state = dict(step_state)
        if nested:
            decoded_state["obs"] = decoded_obs
        else:
            decoded_state.update(decoded_obs)
        return decoded_state

    @staticmethod
    def close_reader(shm_cache: Dict[str, Any]) -> None:
        """Close one reader's cache without affecting other readers or the owner."""
        for shm_obj in shm_cache.values():
            try:
                shm_obj.close()
            except Exception:
                pass
        shm_cache.clear()

    def release(self) -> None:
        """Close and unlink producer-owned blocks; reader caches are independent."""
        with self._init_lock:
            slots = [shm_obj for item in self._camera_metadata for shm_obj in item.shm]
            slots.extend(self._stale_blocks)
            for shm_obj in slots:
                if shm_obj is None:
                    continue
                try:
                    shm_obj.close()
                except Exception:
                    pass
                try:
                    shm_obj.unlink()
                except FileNotFoundError:
                    pass
                except Exception:
                    self.logger.exception("Failed to unlink shared memory block")
            self._stale_blocks.clear()
            self._camera_metadata = ()
            self._camera_by_name.clear()
            self._packet_template = None

    def close(self) -> None:
        if self._closed:
            return
        self.release()
        self._closed = True
