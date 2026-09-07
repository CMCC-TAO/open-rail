import logging
import os
import threading
import time
from multiprocessing import shared_memory
from typing import Any, Dict, Optional, Union

import numpy as np


class SharedMemoryManager:
    """Own producer shared-memory slots and provide isolated reader caches."""

    def __init__(self, ring_size: int = 3) -> None:
        self.logger = logging.getLogger(__name__)
        self._ring_size = ring_size
        self._lock = threading.Lock()
        self._slots: Dict[str, Dict[str, Any]] = {}
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

    def _create_or_resize_slot(self, camera_name: str, slot_index: int, shape: tuple, dtype: np.dtype):
        camera_entry = self._slots.setdefault(
            camera_name, {"slots": [None] * self._ring_size, "next_index": 0}
        )
        slot = camera_entry["slots"][slot_index]
        required_nbytes = int(np.prod(shape, dtype=np.int64)) * int(np.dtype(dtype).itemsize)

        if slot is not None:
            if tuple(slot["shape"]) == tuple(shape) and np.dtype(slot["dtype"]) == np.dtype(dtype):
                return slot
            old_shm = slot.get("shm")
            if old_shm is not None:
                self._stale_blocks.append(old_shm)

        shm_obj = shared_memory.SharedMemory(
            create=True,
            size=required_nbytes,
            name=self._safe_shm_name(camera_name, slot_index),
        )
        new_slot = {
            "shm": shm_obj,
            "name": shm_obj.name,
            "shape": tuple(shape),
            "dtype": np.dtype(dtype),
        }
        camera_entry["slots"][slot_index] = new_slot
        return new_slot

    def init_pool(self, camera_shape: Dict[str, Union[tuple, list]]) -> None:
        """Create producer slots using shapes obtained from real camera frames."""
        if not isinstance(camera_shape, dict):
            return
        with self._lock:
            for camera_name, shape_value in camera_shape.items():
                if not str(camera_name).startswith("cam.") or shape_value is None:
                    continue
                shape = tuple(int(value) for value in shape_value)
                if len(shape) < 2:
                    continue
                if len(shape) == 2:
                    shape = (shape[0], shape[1], 1)
                for slot_index in range(self._ring_size):
                    self._create_or_resize_slot(camera_name, slot_index, shape, np.uint8)

    def encode_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Copy camera arrays into producer slots and return transport descriptors."""
        if not isinstance(observation, dict):
            return observation
        nested = isinstance(observation.get("obs"), dict)
        obs = observation["obs"] if nested else observation
        if not isinstance(obs, dict):
            return observation

        encoded_obs = dict(obs)
        transformed = False
        with self._lock:
            for camera_name, frame in obs.items():
                if not str(camera_name).startswith("cam.") or not isinstance(frame, np.ndarray):
                    continue
                if frame.ndim < 2:
                    self.logger.warning("Invalid frame ndim for %s: %s", camera_name, frame.ndim)
                    continue

                camera_entry = self._slots.setdefault(
                    camera_name, {"slots": [None] * self._ring_size, "next_index": 0}
                )
                slot_index = int(camera_entry["next_index"])
                slot = self._create_or_resize_slot(camera_name, slot_index, tuple(frame.shape), frame.dtype)
                shm_frame = np.ndarray(slot["shape"], dtype=slot["dtype"], buffer=slot["shm"].buf)
                shm_frame[...] = frame
                encoded_obs[camera_name] = {
                    "transport": "shm",
                    "name": slot["name"],
                    "shape": list(frame.shape),
                    "dtype": str(frame.dtype),
                    "slot_index": slot_index,
                    "timestamp_ns": time.time_ns(),
                }
                camera_entry["next_index"] = (slot_index + 1) % self._ring_size
                transformed = True

        if not transformed:
            return observation
        encoded_observation = dict(observation)
        if nested:
            encoded_observation["obs"] = encoded_obs
        else:
            encoded_observation.update(encoded_obs)
        return encoded_observation

    @staticmethod
    def decode_observation(
        step_state: Dict[str, Any],
        shm_cache: Dict[str, Any],
        copy: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Attach and copy frames using the cache owned by one reader."""
        logger = logging.getLogger(__name__)
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
        with self._lock:
            slots = [slot for entry in self._slots.values() for slot in entry.get("slots", []) if slot]
            slots.extend(self._stale_blocks)
            for slot in slots:
                shm_obj = slot.get("shm") if isinstance(slot, dict) else slot
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
            self._slots.clear()

    def close(self) -> None:
        if self._closed:
            return
        self.release()
        self._closed = True
