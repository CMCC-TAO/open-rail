import zmq
import json
import pickle
from ml_collections import ConfigDict

class ZMQServer():
    """ZMQ Server for handling client-server communication
    
    This server uses ZMQ ROUTER socket pattern to handle multiple clients
    and manage bidirectional communication for VLA inference requests.
    """
    
    def __init__(self, config: ConfigDict):
        """Initialize ZMQ Server
        
        Args:
            config: Configuration dictionary containing server settings
        """
        # Initialize ZMQ server with configuration dictionary
        self.config = config
        self.context = zmq.Context()
        # Create ROUTER socket for handling multiple clients
        self.router = self.context.socket(zmq.ROUTER)
        self.router.setsockopt(zmq.SNDHWM, 1)  # Set send buffer to 1 message
        self.router.bind(config.server_addr)
        self.client_id = None  # Client identifier for current connection
        print(f'ZMQ server started, listening on: {config.server_addr}')

    def recvMessage(self):
        """Receive message from client
        
        Returns:
            dict: Message containing 'data' and 'meta' fields, or None if error
        """
        try:
            # Receive message (blocking), ROUTER socket includes sender identity and multipart message
            parts = self.router.recv_multipart()
            self.client_id = parts[0]  # Client identifier
            message = {}
            if len(parts) >= 2:
                message['data'] = pickle.loads(parts[1])  # Binary data
                message['meta'] = json.loads(parts[2].decode('utf8'))  # Metadata JSON
                return message
            else:
                print("Invalid message format received")
                return None
        except Exception as e:
            print(f"Error receiving message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def sendMessage(self, data, meta={}):
        """Send message to client
        
        Args:
            data: Data to send (will be pickled)
            meta: Metadata dictionary (will be JSON encoded)
        """
        try:
            if self.client_id is None:
                print("Client ID not found, cannot send message")
                return
            # Convert data dictionary to byte stream
            data = pickle.dumps(data)
            meta = json.dumps(meta).encode('utf8')
            self.router.send_multipart([self.client_id, data, meta], flags=zmq.NOBLOCK)  # Non-blocking send
        except Exception as e:
            print(f"Error sending message: {e}")
            import traceback
            traceback.print_exc()
    
    def close(self):
        """Close ZMQ server and cleanup resources"""
        self.router.close()
        self.context.term()
        print(f'ZMQ server closed, address was: {self.config.server_addr}')