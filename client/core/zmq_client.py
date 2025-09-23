import zmq
import json
import pickle
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
        print(f'ZMQ client started, connected to: {config.client_addr}')

    def recvMessage(self):
        """Receive message from the VLA inference server.
        
        This method performs blocking receive operation, typically used in threads.
        
        Returns:
            dict: Message containing 'data' and 'meta' fields, or None if error occurs.
        """
        try:
            # Blocking receive, used in threads
            if self.dealer.poll() != 0:
                message = {}
                parts = self.dealer.recv_multipart() # Receive multipart message
                if len(parts) >= 2:
                    message['data'] = pickle.loads(parts[0]) # Part 0 is binary data
                    message['meta'] = json.loads(parts[1].decode('utf8')) # Part 1 is metadata JSON
                    return message
                else:
                    print("Received data has issues")
                    return None
        except Exception as e:
            print(f"Error receiving message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def sendMessage(self, data, meta={}):
        """Send message to the VLA inference server.
        
        Args:
            data: Data to be sent (will be pickled)
            meta (dict): Metadata to be sent as JSON
            
        Note:
            Images need encoding before sending: _, img_encoded = cv2.imencode('.jpg', data)
            Received images need decoding: img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        """
        try:
            data = pickle.dumps(data) # Convert data dict to byte stream
            meta = json.dumps(meta).encode('utf8')
            self.dealer.send_multipart([data, meta], flags=zmq.NOBLOCK) # Non-blocking send
        except Exception as e:
            print(f"Error sending message: {e}")
            import traceback
            traceback.print_exc()
    
    def close(self):
        """Close the ZMQ client and clean up resources."""
        self.dealer.close()
        self.context.term()
        print(f'ZMQ client closed, connection address: {self.config.client_addr}')