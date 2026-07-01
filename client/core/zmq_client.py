import zmq
import json
import pickle
import logging
import threading
from ml_collections import ConfigDict

class ZMQClient():
    """ZMQ client for communication with VLA inference server.
    
    This class handles the ZMQ communication protocol for sending observation data
    to the VLA inference server and receiving action predictions.
    """
    
    def __init__(self, config: ConfigDict):
        """Initialize the ZMQ client.
        
        Args:
            config (ConfigDict): Configuration containing client address and other parameters.
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.client_addr = f'tcp://{config.ip}:{config.port}'  # Client connection address and port
        self.context = zmq.Context()
        self.dealer = self.context.socket(zmq.DEALER)
        # self.dealer.setsockopt(zmq.SNDTIMEO, 5000)  # 5 second timeout
        self.dealer.setsockopt(zmq.SNDHWM, 1)  # Set send buffer to 1 message
        self.dealer.connect(self.client_addr)
        self._closed = False
        self._close_lock = threading.Lock()
        self.logger.info(f'ZMQ client started, connected to: {self.client_addr}')

    def recvMessage(self, timeout_ms=500):
        """Receive message from the VLA inference server.

        Args:
            timeout_ms (int): Poll timeout in milliseconds.

        Returns:
            dict: Message containing 'data' and 'meta' fields, or None if no data/error/closed.
        """
        if self._closed:
            return None

        try:
            if self.dealer.poll(timeout=timeout_ms) != 0:
                parts = self.dealer.recv_multipart()
                if len(parts) >= 2:
                    return {
                        'data': pickle.loads(parts[0]),
                        'meta': json.loads(parts[1].decode('utf8')),
                    }
                self.logger.warning("Received data has issues")
            return None
        except zmq.ZMQError as e:
            # Socket may be closed concurrently during shutdown.
            if self._closed or e.errno in (zmq.ENOTSOCK, zmq.ETERM):
                return None
            self.logger.error(f"Error receiving message: {e}")
            import traceback
            traceback.print_exc()
            return None
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            import traceback
            traceback.print_exc()
            return None

    def sendMessage(self, data, meta=None):
        """Send message to the VLA inference server.

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if self._closed:
            return False

        if meta is None:
            meta = {}

        try:
            data = pickle.dumps(data)
            meta = json.dumps(meta).encode('utf8')
            self.dealer.send_multipart([data, meta], flags=zmq.NOBLOCK)
            return True
        except zmq.ZMQError as e:
            # EAGAIN means HWM/backpressure in non-blocking mode; treat as soft failure.
            if self._closed or e.errno in (zmq.ENOTSOCK, zmq.ETERM, zmq.EAGAIN):
                return False
            self.logger.error(f"Error sending message: {e}")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            import traceback
            traceback.print_exc()
            return False

    def close(self):
        """Close the ZMQ client and clean up resources."""
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
            try:
                self.dealer.close(linger=0)
            except Exception:
                pass
            try:
                self.context.term()
            except Exception:
                pass
        self.logger.info(f'ZMQ client closed, connection address: {self.client_addr}')
