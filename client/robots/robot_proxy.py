"""Subprocess robot proxy.

Runs the concrete ``RobotBody`` (and therefore the vendor SDK) in a dedicated
subprocess so that the observation / control workload no longer competes for the
GIL with the VLA client threads (image encoding, inference, visualization).

Call chain::

    Web/API -> VLAClient -> RobotProxy (main process)
        -> IPC (shared memory for images + queues for everything else)
        -> _RobotWorker (subprocess) -> concrete RobotBody / SDK

Transport:
    * images  : written by the worker into ``SharedMemoryManager`` slots; only the
                picklable descriptors cross the process boundary and the main
                process attaches to the same blocks (zero-copy views).
    * other   : ``obs.state`` and ``current_state`` travel through a queue.
    * commands: control / manual / arbitrary method calls travel through a queue
                and are executed by the worker (synchronous RPC).
"""

from __future__ import annotations

import atexit
import logging
import multiprocessing as mp
import queue
import signal
import threading
import time
from multiprocessing import shared_memory
from typing import Any, Dict, Optional, Tuple

import numpy as np

from client.core.shared_memory_manager import FramePacket, SharedMemoryManager

logger = logging.getLogger(__name__)

# Command tuple layout: (kind, cmd_id, method_name, args, kwargs)
_CMD_STOP = 'stop'

# Maps RobotType values to the module exposing the concrete ``RobotBody``.
_ROBOT_MODULES: Dict[str, str] = {
    'a2d': 'client.robots.a2d.body_robot',
    'mock': 'client.robots.mock.body_robot',
    'ti5_t170c': 'client.robots.ti5_t170c.body_robot',
    'navi_wa2': 'client.robots.navi_wa2.body_robot',
}

# Small wait used when the observation queue is empty inside the worker loop.
_IDLE_SLEEP_S = 0.0005

# Queues owned by the proxy; each one holds three semaphores that must be
# released on shutdown (see RobotProxy._close_queues).
_QUEUE_ATTRS = ('_obs_queue', '_cmd_queue', '_resp_queue', '_ready_queue')


def _normalize_robot_type(robot_type) -> str:
    """Accept a RobotType enum, a plain string, or 'RobotType.A2D'-like values."""
    value = getattr(robot_type, 'value', robot_type)
    value = str(value)
    if '.' in value:
        value = value.rsplit('.', 1)[-1]
    value = value.strip().lower()
    if value not in _ROBOT_MODULES:
        raise ValueError(f'Unsupported robot type: {robot_type!r} '
                         f'(supported: {sorted(_ROBOT_MODULES)})')
    return value


def _create_robot_body(robot_type: str, config, robot_module: Optional[str] = None):
    """Instantiate the concrete RobotBody inside the worker subprocess.

    Args:
        robot_type: key of ``_ROBOT_MODULES``.
        config: robot specific configuration subtree.
        robot_module: optional dotted module path overriding the built-in mapping.
            Useful for robot implementations that are not registered yet.
    """
    module_name = robot_module or _ROBOT_MODULES[robot_type]
    module = __import__(module_name, fromlist=['RobotBody'])
    return module.RobotBody(config)


class _RobotWorker:
    """Subprocess side: owns the real robot and serves commands/observations."""

    def __init__(self, robot_type, config, obs_queue, cmd_queue, resp_queue,
                 ready_queue, shm_ring_size, robot_module=None):
        self._robot_type = robot_type
        self._config = config
        self._robot_module = robot_module
        self._obs_queue = obs_queue
        self._cmd_queue = cmd_queue
        self._resp_queue = resp_queue
        self._ready_queue = ready_queue
        self._shm_ring_size = shm_ring_size

        self._robot = None
        self._shm: Optional[SharedMemoryManager] = None
        self._stop = False

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def run(self) -> None:
        try:
            self._robot = _create_robot_body(
                self._robot_type, self._config, self._robot_module
            )
        except BaseException as exc:  # noqa: BLE001 - reported back to the parent
            logger.exception('Robot creation failed in worker subprocess')
            self._ready_queue.put(('error', exc))
            return

        try:
            self._ready_queue.put(('ready', self._collect_metadata()))
        except BaseException as exc:  # noqa: BLE001
            logger.exception('Failed to publish robot metadata')
            self._ready_queue.put(('error', exc))
            return

        try:
            self._loop()
        finally:
            self._cleanup()

    def _collect_metadata(self) -> Dict[str, Any]:
        """Snapshot everything the parent proxy must expose locally."""
        robot = self._robot
        methods = set()
        for name in dir(robot):
            if name.startswith('__'):
                continue
            if callable(getattr(robot, name, None)):
                methods.add(name)
        return {
            'robot_type': self._robot_type,
            'class_name': type(robot).__name__,
            'module': type(robot).__module__,
            'config': robot.config,
            'action_layout': dict(getattr(robot, 'action_layout', {}) or {}),
            'action_dim': int(getattr(robot, 'action_dim', 0)),
            'state_dim': int(getattr(robot, 'state_dim', 0)),
            'joint_indices': list(getattr(robot, 'joint_indices', []) or []),
            'step_indices': list(getattr(robot, 'step_indices', []) or []),
            'methods': sorted(methods),
        }

    def _cleanup(self) -> None:
        """Always release the robot and the shared memory, even on interrupt.

        ``except BaseException`` is deliberate: a second Ctrl-C during shutdown
        must not skip the shared memory release and leak the blocks.
        """
        try:
            if self._robot is not None:
                self._robot.close()
        except BaseException:  # noqa: BLE001 - cleanup must not be interrupted
            logger.exception('Robot close failed in worker subprocess')
        try:
            if self._shm is not None:
                self._shm.release()
                self._shm = None
        except BaseException:  # noqa: BLE001
            logger.exception('Shared memory release failed in worker subprocess')

    # ------------------------------------------------------------------
    # main loop
    # ------------------------------------------------------------------
    def _loop(self) -> None:
        """Serve commands and publish observations until stopped.

        Ctrl-C is delivered to the whole foreground process group, so the worker
        gets a KeyboardInterrupt too. It must be handled here: KeyboardInterrupt
        derives from BaseException, so it is neither caught by ``except Exception``
        nor by the command error path, and would otherwise abort the loop with a
        traceback while the robot is still open.
        """
        try:
            while not self._stop:
                self._drain_commands()
                if self._stop:
                    break
                try:
                    observation = self._robot.retrieve_observation()
                except Exception:
                    logger.exception('retrieve_observation failed in worker subprocess')
                    time.sleep(_IDLE_SLEEP_S)
                    continue
                if observation is not None:
                    self._publish(observation)
                else:
                    time.sleep(_IDLE_SLEEP_S)
        except (KeyboardInterrupt, SystemExit):
            # Covers both Ctrl-C and the SystemExit raised by the SIGTERM handler.
            logger.info('Robot worker received a shutdown signal, cleaning up')

    def _drain_commands(self) -> None:
        """Execute every queued command so control latency is not frame-bound."""
        while True:
            try:
                command = self._cmd_queue.get_nowait()
            except queue.Empty:
                return
            self._handle_command(command)

    def _handle_command(self, command: Tuple) -> None:
        kind = command[0]
        if kind == _CMD_STOP:
            self._stop = True
            return
        _, cmd_id, method, args, kwargs = command
        try:
            target = getattr(self._robot, method)
            result = target(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            # Never convert an interrupt into a command error; let _loop shut down.
            raise
        except BaseException as exc:  # noqa: BLE001 - forwarded to the parent
            self._resp_queue.put((cmd_id, False, exc))
        else:
            self._resp_queue.put((cmd_id, True, result))

    # ------------------------------------------------------------------
    # observation publishing
    # ------------------------------------------------------------------
    def _init_shm(self, observation: Dict[str, Any]) -> None:
        camera_items = [
            (key, value) for key, value in observation.items()
            if str(key).startswith('cam.') and isinstance(value, np.ndarray)
        ]
        if not camera_items:
            logger.warning('Observation has no camera frames; shared memory disabled')
            return
        self._shm = SharedMemoryManager(ring_size=self._shm_ring_size)
        self._shm.init_pool(
            {key: value.shape for key, value in camera_items},
            camera_dtypes={key: value.dtype for key, value in camera_items},
        )

    def _publish(self, observation: Dict[str, Any]) -> None:
        if self._shm is None:
            self._init_shm(observation)

        if self._shm is not None:
            packet = self._shm.encode_observation(observation)
            if isinstance(packet, FramePacket):
                payload_obs = packet.to_observation_descriptors()
            else:
                payload_obs = observation
        else:
            # No camera frames: fall back to plain (pickled) values.
            payload_obs = observation

        state = getattr(self._robot, 'current_state', None)
        payload = {
            'observation': payload_obs,
            'state': np.asarray(state).copy() if state is not None else None,
            't_send': time.perf_counter(),
        }
        self._push_observation(payload)

    def _push_observation(self, payload: Dict[str, Any]) -> None:
        """Publish the newest frame, dropping the oldest when the queue is full."""
        try:
            self._obs_queue.put_nowait(payload)
            return
        except queue.Full:
            pass
        try:
            self._obs_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            self._obs_queue.put_nowait(payload)
        except queue.Full:
            pass


def _ignore_interrupt_signals() -> None:
    """Ignore Ctrl-C inside the worker; shutdown is driven by the parent proxy.

    SIGINT reaches every process of the foreground group, so a plain Ctrl-C (and
    any repeat of it) would interrupt the worker mid-frame or even during
    cleanup. The parent sends an explicit stop command instead. As a safety net
    the worker is a daemon process and is terminated when the parent exits.
    """
    try:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    except Exception:  # pragma: no cover - non-POSIX / restricted environments
        logger.debug('Could not ignore SIGINT in the robot worker', exc_info=True)


def _install_worker_signal_handlers() -> None:
    """Turn SIGTERM (``Process.terminate``) into a graceful shutdown.

    ``terminate()`` sends SIGTERM, whose default action kills the worker before
    its ``finally`` block runs, so the shared memory blocks it created stay
    unlinked and resource_tracker reports them as leaked. Raising SystemExit from
    the handler makes it propagate through ``_loop()`` so the cleanup still runs.
    """
    def _graceful_exit(signum, frame):  # noqa: ARG001 - signal handler signature
        raise SystemExit(0)

    try:
        signal.signal(signal.SIGTERM, _graceful_exit)
    except Exception:  # pragma: no cover - restricted environments
        logger.debug('Could not install SIGTERM handler in the robot worker',
                     exc_info=True)


def _robot_worker_entry(robot_type, config, obs_queue, cmd_queue, resp_queue,
                        ready_queue, shm_ring_size, robot_module=None) -> None:
    """Subprocess entry point (must stay importable/picklable for spawn)."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )
    _ignore_interrupt_signals()
    _install_worker_signal_handlers()
    _RobotWorker(
        robot_type=robot_type,
        config=config,
        obs_queue=obs_queue,
        cmd_queue=cmd_queue,
        resp_queue=resp_queue,
        ready_queue=ready_queue,
        shm_ring_size=shm_ring_size,
        robot_module=robot_module,
    ).run()


class RobotProxy:
    """Main-process stand-in for a ``RobotBody`` running in a subprocess.

    Exposes the same surface the VLA client and the web API rely on, so no caller
    needs to change:
        * ``retrieve_observation()``      -> newest frame from the worker queue
        * ``control_robot`` / ``execute_action`` / ``_control_robot`` / ``reset_robot``
          and any other public robot method -> synchronous RPC to the worker
        * ``config`` / ``action_layout`` / ``*_dim`` / ``*_indices`` -> captured once
          at startup (no per-frame IPC)
        * ``current_state`` -> refreshed from the observation stream
    """

    def __init__(self, robot_type, config,
                 shm_ring_size: int = 4,
                 obs_queue_size: int = 2,
                 cmd_queue_size: int = 64,
                 rpc_timeout: float = 30.0,
                 startup_timeout: float = 180.0,
                 robot_module: Optional[str] = None):
        self._robot_type = _normalize_robot_type(robot_type)
        self._robot_module = robot_module
        self.logger = logging.getLogger(__name__)

        self._ctx = mp.get_context('spawn')
        self._obs_queue = self._ctx.Queue(maxsize=obs_queue_size)
        self._cmd_queue = self._ctx.Queue(maxsize=cmd_queue_size)
        self._resp_queue = self._ctx.Queue()
        self._ready_queue = self._ctx.Queue(maxsize=1)

        self._rpc_lock = threading.Lock()
        self._rpc_timeout = rpc_timeout
        self._cmd_id = 0
        self._closed = False
        self._shm_cache: Dict[str, Any] = {}
        # Names of the worker-owned shared memory blocks seen in observations;
        # used to unlink any survivor if the worker was killed before cleaning up.
        self._remote_shm_names = set()

        # The worker owns the shared memory blocks; attaching here must not make
        # this process try to unlink them on exit.
        SharedMemoryManager.disable_shared_memory_tracking_in_process()

        self._process = self._ctx.Process(
            target=_robot_worker_entry,
            args=(self._robot_type, config, self._obs_queue, self._cmd_queue,
                  self._resp_queue, self._ready_queue, shm_ring_size,
                  self._robot_module),
            name=f'robot-worker-{self._robot_type}',
            daemon=True,
        )
        self._process.start()
        self.logger.info('Robot worker subprocess starting (type=%s, pid=%s)',
                         self._robot_type, self._process.pid)

        try:
            metadata = self._await_startup(startup_timeout)
        except BaseException:
            self._terminate()
            raise

        self._apply_metadata(metadata)

        # Safety net: if the caller never closes the proxy (for example an
        # aborted shutdown), the IPC resources are still released at exit.
        self._atexit_handle = atexit.register(self.close)

    # ------------------------------------------------------------------
    # startup
    # ------------------------------------------------------------------
    def _await_startup(self, timeout: float) -> Dict[str, Any]:
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError(
                    f'Robot worker did not become ready within {timeout:.0f}s '
                    f'(type={self._robot_type})'
                )
            try:
                status, payload = self._ready_queue.get(timeout=min(0.5, remaining))
            except queue.Empty:
                if not self._process.is_alive():
                    raise RuntimeError(
                        f'Robot worker process died during startup '
                        f'(type={self._robot_type}, exitcode={self._process.exitcode})'
                    )
                continue
            if status == 'ready':
                return payload
            raise RuntimeError(f'Robot worker startup failed: {payload!r}') from payload

    def _apply_metadata(self, metadata: Dict[str, Any]) -> None:
        self.robot_type = metadata['robot_type']
        self.config = metadata['config']
        self.action_layout = metadata['action_layout']
        self.action_dim = metadata['action_dim']
        self.state_dim = metadata['state_dim']
        self.joint_indices = metadata['joint_indices']
        self.step_indices = metadata['step_indices']
        self._remote_methods = frozenset(metadata['methods'])

        state_dim = self.state_dim or 0
        self.current_state = np.zeros(state_dim, dtype=np.float32)

        # Keep ``type(obj).__module__`` / ``__name__`` identical to the real robot
        # so existing type/duck-typing checks in callers keep working.
        proxy_cls = type(
            metadata['class_name'],
            (RobotProxy,),
            {'__module__': metadata['module']},
        )
        self.__class__ = proxy_cls

        self.logger.info('Robot worker ready (type=%s, class=%s.%s, pid=%s)',
                         self.robot_type, metadata['module'],
                         metadata['class_name'], self._process.pid)

    # ------------------------------------------------------------------
    # observation
    # ------------------------------------------------------------------
    def retrieve_observation(self):
        """Return the newest observation, or None when no new frame is available."""
        if self._closed:
            return None
        try:
            payload = self._obs_queue.get_nowait()
        except queue.Empty:
            return None

        state = payload.get('state')
        if state is not None:
            self.current_state = state

        observation = payload.get('observation')
        self._track_remote_shm(observation)
        decoded = SharedMemoryManager.decode_observation(
            observation, self._shm_cache, copy=False
        )
        if decoded is None:
            self.logger.warning('Dropping one observation: shared memory decode failed')
            return None
        return decoded

    # ------------------------------------------------------------------
    # commands / RPC
    # ------------------------------------------------------------------
    def _rpc(self, method: str, *args, **kwargs):
        """Run a method inside the worker subprocess and wait for its result."""
        if self._closed:
            raise RuntimeError(f'Robot proxy is closed; cannot call {method!r}')
        with self._rpc_lock:
            self._cmd_id += 1
            cmd_id = self._cmd_id
            self._cmd_queue.put(('call', cmd_id, method, args, kwargs))

            deadline = time.time() + self._rpc_timeout
            while True:
                try:
                    resp_id, ok, value = self._resp_queue.get(timeout=0.05)
                except queue.Empty:
                    if time.time() > deadline:
                        raise TimeoutError(
                            f'Robot worker did not answer {method!r} within '
                            f'{self._rpc_timeout:.0f}s'
                        )
                    if not self._process.is_alive():
                        raise RuntimeError(
                            f'Robot worker process died while running {method!r} '
                            f'(exitcode={self._process.exitcode})'
                        )
                    continue
                if resp_id != cmd_id:
                    continue
                if ok:
                    return value
                raise value

    def control_robot(self, action):
        """Send an action to the robot (mirrors RobotBody.control_robot)."""
        return self._rpc('control_robot', action)

    def execute_action(self, data):
        """Send a raw action command to the robot."""
        return self._rpc('execute_action', data)

    def _control_robot(self, data):
        """Manual / web control path (see RobotBase._control_robot)."""
        return self._rpc('_control_robot', data)

    def reset_robot(self, target_pose=None, mode='default'):
        """Reset the robot to its default pose."""
        return self._rpc('reset_robot', target_pose=target_pose, mode=mode)

    def get_joint_indices(self):
        return self.joint_indices

    def get_step_indices(self):
        return self.step_indices

    def __getattr__(self, name):
        # Only called when normal lookup fails; forward known robot methods.
        methods = self.__dict__.get('_remote_methods')
        if methods is not None and name in methods:
            return lambda *args, **kwargs: self._rpc(name, *args, **kwargs)
        raise AttributeError(
            f'{type(self).__name__!r} object has no attribute {name!r}'
        )

    # ------------------------------------------------------------------
    # shutdown
    # ------------------------------------------------------------------
    def close(self):
        """Stop the worker subprocess and release the shared memory attachments."""
        if self._closed:
            return
        self._closed = True

        handle = getattr(self, '_atexit_handle', None)
        if handle is not None:
            try:
                atexit.unregister(handle)
            except Exception:  # pragma: no cover - best effort
                pass
            self._atexit_handle = None

        try:
            # While a KeyboardInterrupt is being unwound the enqueue can be
            # aborted; retry so the worker still gets the chance to shut down
            # cleanly instead of being killed.
            for _ in range(3):
                try:
                    self._cmd_queue.put((_CMD_STOP, None, None, None, None))
                    break
                except BaseException:  # noqa: BLE001 - never let it block shutdown
                    time.sleep(0.01)
            else:
                self.logger.debug('Failed to send the stop command to the robot worker')

            process = getattr(self, '_process', None)
            if process is not None and process.is_alive():
                process.join(timeout=5.0)
                if process.is_alive():
                    self.logger.warning('Robot worker did not exit gracefully; terminating')
                    process.terminate()
                    process.join(timeout=3.0)
                    if process.is_alive():
                        process.kill()
                        process.join(timeout=1.0)
        finally:
            # Always detach from the worker-owned blocks, even if we are interrupted.
            SharedMemoryManager.close_reader(self._shm_cache)
            self._unlink_remote_shm()
            self._close_queues()
            self.logger.info('Robot worker stopped (type=%s)', self._robot_type)

    def _track_remote_shm(self, observation) -> None:
        """Remember the worker-owned block names carried by an observation."""
        if not isinstance(observation, dict):
            return
        for key, value in observation.items():
            if str(key).startswith('cam.') and isinstance(value, dict):
                name = value.get('name')
                if name:
                    self._remote_shm_names.add(name)

    def _unlink_remote_shm(self) -> None:
        """Last resort: unlink worker-owned blocks that survived shutdown.

        If the worker was killed before its own cleanup ran, the blocks it
        created are still registered with resource_tracker and get reported as
        leaked shared_memory objects at exit.
        """
        if not self._remote_shm_names:
            return
        for name in list(self._remote_shm_names):
            block = None
            try:
                block = shared_memory.SharedMemory(name=name)
                block.close()
                block.unlink()
            except FileNotFoundError:
                pass
            except Exception:
                self.logger.debug('Could not unlink shared memory block %s', name,
                                  exc_info=True)
            finally:
                if block is not None:
                    try:
                        block.close()
                    except Exception:
                        pass
                self._remote_shm_names.discard(name)

    def _close_queues(self) -> None:
        """Close the IPC queues so their semaphores are unregistered.

        Every ``multiprocessing.Queue`` owns three semaphores (``_rlock``,
        ``_wlock`` and ``_sem``). They are only unregistered with the resource
        tracker when the underlying ``SemLock`` objects are collected or when the
        atexit finalizers run to completion - neither happens reliably on a
        Ctrl-C shutdown, and resource_tracker then reports them as leaked
        ("There appear to be N leaked semaphore objects"). Closing the queues and
        dropping the references lets the semaphores be released deterministically.
        """
        for name in _QUEUE_ATTRS:
            pipe = getattr(self, name, None)
            if pipe is None:
                continue
            try:
                pipe.cancel_join_thread()
            except Exception:
                self.logger.debug('Failed to cancel join thread on %s', name, exc_info=True)
            try:
                pipe.close()
            except Exception:
                self.logger.debug('Failed to close %s', name, exc_info=True)
            setattr(self, name, None)

    def _terminate(self) -> None:
        """Best-effort teardown used when startup fails."""
        self._closed = True
        process = getattr(self, '_process', None)
        if process is not None and process.is_alive():
            process.terminate()
            process.join(timeout=3.0)
            if process.is_alive():
                process.kill()
                process.join(timeout=1.0)
        SharedMemoryManager.close_reader(self._shm_cache)
        self._close_queues()

    def __del__(self):  # pragma: no cover - best effort
        try:
            self.close()
        except Exception:
            pass
