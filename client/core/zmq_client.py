import zmq
import json
import pickle
import logging
import threading
import time
from ml_collections import ConfigDict


class ZMQClient():
    """ZMQ client for communication with VLA inference server.

    This class handles the ZMQ communication protocol for sending observation data
    to the VLA inference server and receiving action predictions.

    Socket ownership
    ----------------
    ZMQ sockets are not thread safe, so every socket here is created, used and
    closed by exactly one thread:

    * the data DEALER is claimed by the first thread that sends or receives on
      it (the inference thread in production), see ``_data_socket``;
    * the heartbeat DEALER lives entirely inside the heartbeat thread.

    No thread ever closes a socket it does not own. The heartbeat thread only
    reports link state through ``is_connected``; it never rebuilds the data
    socket, because zmq reconnects the underlying TCP connection on its own.
    """

    def __init__(self, config: ConfigDict):
        """Initialize the ZMQ client.

        Args:
            config (ConfigDict): Configuration containing client address and other parameters.
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.context = zmq.Context()

        self.client_addr = f'tcp://{config.ip}:{config.port}'  # Client connection address and port

        # Data socket state. The socket is created lazily by its owner thread.
        self._dealer = None
        self._data_owner = None
        self._data_claim_lock = threading.Lock()
        self._data_released = threading.Event()

        self.is_closed = False
        self.is_connected = False  # Written by the heartbeat thread only
        self._close_lock = threading.Lock()
        self._stop_event = threading.Event()

        # Heartbeat thread
        self.heartbeat_thread = None
        self.last_heartbeat_time = time.time()
        self.heartbeat_info = {}

        self.logger.info(f'ZMQ client started, connected to: {self.client_addr}')

        # Start heartbeat thread
        self.start_heartbeat()

    def _create_dealer(self, hwm=1):
        """Create and connect a DEALER socket.

        ZMTP-level heartbeats let libzmq notice a half-open TCP connection and
        reconnect by itself, so the application never has to rebuild a socket.
        """
        dealer = self.context.socket(zmq.DEALER)
        dealer.setsockopt(zmq.SNDHWM, hwm)
        dealer.setsockopt(zmq.LINGER, 0)
        dealer.setsockopt(zmq.HEARTBEAT_IVL, 2000)      # send a ZMTP ping every 2s
        dealer.setsockopt(zmq.HEARTBEAT_TIMEOUT, 6000)  # drop and reconnect without a pong
        dealer.setsockopt(zmq.HEARTBEAT_TTL, 10000)     # let the peer expire us as well
        dealer.connect(self.client_addr)
        return dealer

    def _data_socket(self):
        """Return the data DEALER, claiming ownership for the calling thread.

        The first thread to touch the socket owns it for the rest of its life.
        Any other thread raises instead of silently corrupting the socket state.
        """
        tid = threading.get_ident()
        with self._data_claim_lock:
            if self._data_owner is None:
                self._data_owner = tid
                self._dealer = self._create_dealer(hwm=1)
                self.logger.info(f'Data socket created, owned by thread {tid}')
        if self._data_owner != tid:
            raise RuntimeError(
                f'Data socket is owned by thread {self._data_owner} but was used '
                f'from thread {tid}; one socket must stay with one thread')
        if self._dealer is None:
            raise RuntimeError('Data socket has already been released')
        return self._dealer

    def release_data_socket(self):
        """Close the data socket. Only its owner thread may call this."""
        tid = threading.get_ident()
        if self._data_owner is not None and self._data_owner != tid:
            raise RuntimeError(
                f'Data socket is owned by thread {self._data_owner}; '
                f'thread {tid} must not release it')
        if self._dealer is not None:
            try:
                self._dealer.close(linger=0)
            except Exception:
                pass
            self._dealer = None
        self._data_released.set()

    def start_heartbeat(self):
        """Start the heartbeat thread to detect connection status."""
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        self.heartbeat_thread.start()

    def _send_heartbeat(self, sock):
        """Send heartbeat ping on the heartbeat thread's own socket."""
        try:
            data = pickle.dumps({'type': 'heartbeat', 'timestamp': time.time()})
            meta = json.dumps({'action': 'ping'}).encode('utf8')
            sock.send_multipart([data, meta], flags=zmq.NOBLOCK)
            return True
        except zmq.ZMQError:
            return False
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
            return False

    def _receive_heartbeat(self, sock, timeout_ms=1500):
        """Receive heartbeat response on the heartbeat thread's own socket.

        Polls in short slices so that ``close()`` does not have to wait out a
        whole heartbeat timeout before the thread notices it should stop.
        """
        try:
            deadline = time.perf_counter() + timeout_ms / 1000.0
            while True:
                left_ms = int((deadline - time.perf_counter()) * 1000)
                if left_ms <= 0 or self.is_closed:
                    return False
                if sock.poll(timeout=min(100, left_ms)) != 0:
                    break

            parts = sock.recv_multipart()
            if len(parts) < 2:
                return False

            data = pickle.loads(parts[0])
            meta = json.loads(parts[1].decode('utf8'))

            if isinstance(data, dict) and data.get('type') == 'heartbeat' and meta.get('action') == 'pong':
                self.heartbeat_info = data
                self.last_heartbeat_time = time.time()
                return True
            return False
        except zmq.ZMQError as e:
            if self.is_closed or e.errno in (zmq.ENOTSOCK, zmq.ETERM):
                return False
            self.logger.error(f"Error receiving heartbeat: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error receiving heartbeat: {e}")
            return False

    def _heartbeat_worker(self):
        """Heartbeat worker: owns its socket and only reports link state.

        Pings first and sleeps afterwards, so ``is_connected`` is meaningful
        within one round trip of start-up instead of one full interval later.
        """
        sock = self._create_dealer(hwm=100)
        try:
            while not self.is_closed:
                ok = self._send_heartbeat(sock) and self._receive_heartbeat(sock, timeout_ms=1500)
                if not ok and self.is_connected:
                    self.logger.warning('Heartbeat failed, connection may be lost')
                self.is_connected = ok
                # NOTE: the data socket is deliberately untouched here. It belongs
                # to the inference thread, and zmq reconnects TCP on its own.
                if self._stop_event.wait(self.config.heartbeat_interval / 1000):
                    break
        finally:
            try:
                sock.close(linger=0)
            except Exception:
                pass

    def recvMessage(self, timeout_ms=500):
        """Receive message from the VLA inference server.

        Args:
            timeout_ms (int): Total poll budget in milliseconds. The budget is
                shared across every frame read in this call, so the method never
                blocks longer than the caller asked for.

        Returns:
            dict: Message containing 'data' and 'meta' fields, or None if no data/error/closed.
        """
        if self.is_closed:
            return None

        # Claimed outside the try: an ownership violation is a programming error
        # and must escape instead of being swallowed as a transport failure.
        sock = self._data_socket()

        try:
            deadline = time.perf_counter() + timeout_ms / 1000.0
            while True:
                left_ms = int((deadline - time.perf_counter()) * 1000)
                if left_ms <= 0 or sock.poll(timeout=left_ms) == 0:
                    return None

                parts = sock.recv_multipart()
                if len(parts) < 2:
                    self.logger.warning(f"Malformed message dropped: {len(parts)} frames")
                    continue

                data = pickle.loads(parts[0])
                meta = json.loads(parts[1].decode('utf8'))

                # Heartbeats belong on the heartbeat socket; log and keep waiting.
                if isinstance(data, dict) and data.get('type') == 'heartbeat':
                    self.logger.warning('Heartbeat received on the data socket, dropping')
                    continue

                return {
                    'data': data,
                    'meta': meta,
                }
        except zmq.ZMQError as e:
            # Socket may be closed concurrently during shutdown.
            if self.is_closed or e.errno in (zmq.ENOTSOCK, zmq.ETERM):
                return None
            self.logger.error(f"Error receiving message: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            return None

    def sendMessage(self, data, meta=None):
        """Send message to the VLA inference server.

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if self.is_closed:
            return False

        if meta is None:
            meta = {}

        # Claimed outside the try: an ownership violation is a programming error
        # and must escape instead of being swallowed as a transport failure.
        sock = self._data_socket()

        try:
            # memoryview is zero-copy for WebSocket consumers but is not
            # pickleable on all supported Python versions. Convert only at
            # the ZMQ serialization boundary.
            data = pickle.dumps(self._pickle_safe(data))
            meta = json.dumps(meta).encode('utf8')
            sock.send_multipart([data, meta], flags=zmq.NOBLOCK)
            return True
        except zmq.Again:
            # HWM backpressure, not a broken link: the socket stays usable, so
            # the connection state must not be touched here.
            self.logger.debug('Send skipped: high-water mark reached')
            return False
        except zmq.ZMQError as e:
            if not (self.is_closed or e.errno in (zmq.ENOTSOCK, zmq.ETERM)):
                self.logger.error(f"Error sending message: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False

    @classmethod
    def _pickle_safe(cls, value):
        if isinstance(value, memoryview):
            return value.tobytes()
        if isinstance(value, dict):
            return {key: cls._pickle_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._pickle_safe(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._pickle_safe(item) for item in value)
        return value

    @property
    def status(self):
        """Get current connection status.

        Returns:
            dict: Connection status information including connectivity and last heartbeat time.
        """
        status = {
            "zmq_connected": self.is_connected
        }
        status.update(self.heartbeat_info)
        return status

    def close(self):
        """Close the ZMQ client and clean up resources.

        Only sockets owned by the calling thread are closed here. The data
        socket is normally released by the inference thread in its own
        ``finally`` block; if it has not been released yet, the context is
        left un-terminated on purpose rather than closing a socket across
        threads, which is undefined behaviour in libzmq.
        """
        with self._close_lock:
            if self.is_closed:
                return
            self.is_closed = True
            self.is_connected = False
            self._stop_event.set()

            # The caller may own the data socket (single-threaded tools do).
            if self._data_owner == threading.get_ident():
                self.release_data_socket()

            heartbeat_joined = True
            if self.heartbeat_thread is not None:
                self.heartbeat_thread.join(timeout=2.5)
                heartbeat_joined = not self.heartbeat_thread.is_alive()

            data_released = self._data_owner is None or self._data_released.is_set()

            if heartbeat_joined and data_released:
                try:
                    self.context.term()
                except Exception as e:
                    self.logger.error(f'Context termination failed: {e}')
            else:
                self.logger.warning(
                    f'Skipping context termination: data_released={data_released}, '
                    f'heartbeat_joined={heartbeat_joined}. Sockets are left to the OS '
                    f'instead of being closed from a thread that does not own them.')
        self.logger.info(f'ZMQ client closed, connection address: {self.client_addr}')
