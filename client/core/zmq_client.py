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
        self.dealer = self.context.socket(zmq.DEALER)
        # self.dealer.setsockopt(zmq.SNDTIMEO, 5000)  # 5 second timeout
        self.dealer.setsockopt(zmq.SNDHWM, 1)  # Set send buffer to 1 message
        self.dealer.connect(self.client_addr)
        
        self.is_closed = False
        self.is_connected = False
        self._close_lock = threading.Lock()
        self._reconnect_lock = threading.Lock()
        
        # Heartbeat thread
        self.heartbeat_thread = None
        self.last_heartbeat_time = time.time()
        
        self.logger.info(f'ZMQ client started, connected to: {self.client_addr}')
        
        # Start heartbeat thread
        self.start_heartbeat()

    def start_heartbeat(self):
        """Start the heartbeat thread to detect connection status."""
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_worker, daemon=True)
        self.heartbeat_thread.start()

    def _heartbeat_worker(self):
        """Heartbeat worker function to periodically send heartbeat messages."""
        while not self.is_closed:
            time.sleep(self.config.heartbeat_interval/1000)
            
            if self.is_closed:
                break
                
            # Send a heartbeat message to check connection
            if not self.sendMessage({'type': 'heartbeat', 'timestamp': time.time()}, {'action': 'ping'}):
                self.logger.warning(f"Failed to send heartbeat, connection may be lost, is_closed={self.is_closed}")
                # print("Failed to send heartbeat, connection may be lost")
                self.is_connected = False
                # Attempt to reconnect if connection is lost
                self._attempt_reconnect()
            else:
                self.last_heartbeat_time = time.time()
                self.is_connected = True
                # print(f"Heartbeat keep alive, is_connected: {self.is_connected}, heartbeat_time: {self.last_heartbeat_time}")

    def _attempt_reconnect(self):
        """Attempt to reconnect to the server."""
            
        with self._reconnect_lock:
            # Close old socket
            try:
                self.dealer.close(linger=0)
            except:
                pass
                
            self.dealer = self.context.socket(zmq.DEALER)
            self.dealer.setsockopt(zmq.SNDHWM, 1)  # Set send buffer to 1 message
            self.dealer.connect(self.client_addr)
            
            # Test connection by sending two message, the first message will return true anyway.
            self.sendMessage({'type': 'test_connection', 'timestamp': time.time()}, {'action': 'test'})
            if self.sendMessage({'type': 'test_connection', 'timestamp': time.time()}, {'action': 'test'}):
                self.logger.info("Reconnection successful")
                self.is_connected = True
                self.last_heartbeat_time = time.time()
            else:
                self.logger.warning("Reconnection unsuccessful")
            
    def update_connection(self, new_ip=None, new_port=None):
        """Update connection parameters and reconnect to the server.
        
        Args:
            new_ip (str, optional): New IP address to connect to
            new_port (int, optional): New port to connect to
        """
        with self._reconnect_lock: 
            
            # Close old socket
            try:
                self.dealer.close(linger=0)
            except:
                pass
                
            # Create a new socket and connect
            try:
                # Update the connection address
                if new_ip is None:
                    new_ip = self.config.ip
                if new_port is None:
                    new_port = self.config.port
                self.client_addr = f'tcp://{new_ip}:{new_port}'
                self.logger.info(f"Updating connection to: {self.client_addr}")
                print(f"Updating connection to: {self.client_addr}")
                self.dealer = self.context.socket(zmq.DEALER)
                self.dealer.setsockopt(zmq.SNDHWM, 1)  # Set send buffer to 1 message
                self.dealer.connect(self.client_addr)
                
                # Test connection
                if self.sendMessage({'type': 'test_connection', 'timestamp': time.time()}, {'action': 'test'}):
                    self.logger.info("Connection update successful")
                    self.is_connected = True
                    self.last_heartbeat_time = time.time()
                    return True
                else:
                    self.logger.error("Connection test failed after update")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Connection update failed: {e}")
                return False

    def recvMessage(self, timeout_ms=500):
        """Receive message from the VLA inference server.

        Args:
            timeout_ms (int): Poll timeout in milliseconds.

        Returns:
            dict: Message containing 'data' and 'meta' fields, or None if no data/error/closed.
        """
        if self.is_closed:
            return None
        if not self.is_connected:
            return None

        try:
            if self.dealer.poll(timeout=timeout_ms) != 0:
                parts = self.dealer.recv_multipart()
                if len(parts) >= 2:
                    # Check if this is a heartbeat response
                    data = pickle.loads(parts[0])
                    meta = json.loads(parts[1].decode('utf8'))
                    
                    # Handle heartbeat responses
                    if isinstance(data, dict) and data.get('type') == 'heartbeat':
                        self.last_heartbeat_time = time.time()
                        self.is_connected = True
                        # Don't return heartbeat responses to the caller, continue to next message
                        if meta.get('action') == 'pong':
                            return self.recvMessage(timeout_ms)  # Recursively get next message
                    
                    return {
                        'data': data,
                        'meta': meta,
                    }
                self.logger.warning("Received data has issues")
            return None
        except zmq.ZMQError as e:
            # Socket may be closed concurrently during shutdown.
            if self.is_closed or e.errno in (zmq.ENOTSOCK, zmq.ETERM):
                return None
            self.logger.error(f"Error receiving message: {e}")
            import traceback
            traceback.print_exc()
            self.is_connected = False
            return None
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            import traceback
            traceback.print_exc()
            self.is_connected = False
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

        try:
            data = pickle.dumps(data)
            meta = json.dumps(meta).encode('utf8')
            self.dealer.send_multipart([data, meta], flags=zmq.NOBLOCK)
            # print(f"DEBUG: sending data")
            return True
        except zmq.ZMQError as e:
            # self.logger.error(f"Error sending message: {e}")
            # import traceback
            # traceback.print_exc()
            self.is_connected = False
            # EAGAIN means HWM/backpressure in non-blocking mode; treat as soft failure.
            if self.is_closed or e.errno in (zmq.ENOTSOCK, zmq.ETERM, zmq.EAGAIN):
                return False
            return False
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            # import traceback
            # traceback.print_exc()
            self.is_connected = False
            return False

    def get_connection_status(self):
        """Get current connection status.
        
        Returns:
            dict: Connection status information including connectivity and last heartbeat time.
        """
        return {
            'is_connected': self.is_connected,
            'last_heartbeat_time': self.last_heartbeat_time,
            'current_address': self.client_addr,
            'time_since_last_heartbeat': time.time() - self.last_heartbeat_time
        }

    def close(self):
        """Close the ZMQ client and clean up resources."""
        with self._close_lock:
            if self.is_closed:
                return
            self.is_closed = True
            
            # Stop heartbeat thread
            if self.heartbeat_thread:
                self.heartbeat_thread.join(timeout=1)
            self.is_connected = False
            
            try:
                self.dealer.close(linger=0)
            except Exception:
                pass
            try:
                self.context.term()
            except Exception:
                pass
        self.logger.info(f'ZMQ client closed, connection address: {self.client_addr}')