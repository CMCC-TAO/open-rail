import zmq
import json
import pickle
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
        self.config = config
        self.context = zmq.Context()
        self.dealer = self.context.socket(zmq.DEALER)
        # self.dealer.setsockopt(zmq.SNDTIMEO, 5000)  # 5 second timeout
        self.dealer.setsockopt(zmq.SNDHWM, 1)  # Set send buffer to 1 message
        self.dealer.connect(config.client_addr)
        self._closed = False
        self._close_lock = threading.Lock()
        print(f'ZMQ client started, connected to: {config.client_addr}')

    def recvMessage(self):
        """Receive message from the VLA inference server.

        Returns:
            dict: Message containing 'data' and 'meta' fields, or None if no data/error/closed.
        """
        if self._closed:
            return None

        try:
            if self.dealer.poll(timeout=100) != 0:
                parts = self.dealer.recv_multipart()
                if len(parts) >= 2:
                    return {
                        'data': pickle.loads(parts[0]),
                        'meta': json.loads(parts[1].decode('utf8')),
                    }
                print("Received data has issues")
            return None
        except zmq.ZMQError as e:
            # Socket may be closed concurrently during shutdown.
            if self._closed or e.errno in (zmq.ENOTSOCK, zmq.ETERM):
                return None
            print(f"Error receiving message: {e}")
            import traceback
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"Error receiving message: {e}")
            import traceback
            traceback.print_exc()
            return None

    def sendMessage(self, data, meta=None):
        """Send message to the VLA inference server."""
        if self._closed:
            return

        if meta is None:
            meta = {}

        try:
            data = pickle.dumps(data)
            meta = json.dumps(meta).encode('utf8')
            self.dealer.send_multipart([data, meta], flags=zmq.NOBLOCK)
        except zmq.ZMQError as e:
            if self._closed or e.errno in (zmq.ENOTSOCK, zmq.ETERM):
                return
            print(f"Error sending message: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"Error sending message: {e}")
            import traceback
            traceback.print_exc()

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
        print(f'ZMQ client closed, connection address: {self.config.client_addr}')
