import zmq
import json
import socket
import pickle
import logging
import threading
import time
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
        self.logger = logging.getLogger(__name__)
        # Initialize ZMQ server with configuration dictionary
        self.config = config
        self.server_addr = f'tcp://*:{config.port}'  # Server binding address and port
        self.context = zmq.Context()
        # Create ROUTER socket for handling multiple clients
        self.router = self.context.socket(zmq.ROUTER)
        self.router.setsockopt(zmq.SNDHWM, 100)  # Set send buffer to 1 message
        self.router.bind(self.server_addr)
        
        # Client tracking
        self.clients = {}  # Track all connected clients (client_id -> info)
        self.heartbeat_timeout = getattr(config, 'heartbeat_timeout', 30)  # Heartbeat timeout in seconds
        self._running = True
        self._monitor_thread = None
        self._client_lock = threading.Lock()  # Lock for thread safety, receive message thread and monitor thread
        self._send_msg_lock = threading.Lock()  # Lock for thread safety, send message thread and monitor thread
        
        # Start heartbeat monitoring thread
        self._start_heartbeat_monitor()
        self._heartbeat_info = {'status': 'pong', 'type': 'heartbeat'}
        # self._heartbeat_info['server_ip'] = self.get_local_ip()
        self._heartbeat_info['server_ip'] = '*'
        self._heartbeat_info['server_port'] = config.port
        self._heartbeat_meta = {'type': 'heartbeat_response', 'action': 'pong'}
        
        self.logger.info(f'ZMQ server started, listening on: {self.server_addr}')
    def get_local_ip(self):
        """Get the local machine's IP address within the network"""
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            temp_socket.connect(("8.8.8.8", 80))
            local_ip = temp_socket.getsockname()[0]
        except Exception:
            local_ip = "127.0.0.1"
        finally:
            temp_socket.close()
        return local_ip
    def set_heartbeat_info(self, model_type: str = None, model_path: str = None, lang_cmd: str = None):
        if model_type is not None:
            self._heartbeat_info['model_type'] = model_type
        if model_path is not None:
            self._heartbeat_info['model_path'] = model_path
        if lang_cmd is not None:
            self._heartbeat_info['lang_cmd'] = lang_cmd
        self._heartbeat_info['timestamp'] = time.time()
    def _start_heartbeat_monitor(self):
        """Start heartbeat monitoring thread"""
        self._monitor_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
        self._monitor_thread.start()

    def _heartbeat_monitor(self):
        """Monitor heartbeat from client and handle disconnection"""
        while self._running:
            time.sleep(1)  # Check every second
            with self._client_lock:
                current_time = time.time()
                # Remove inactive clients
                inactive_clients = []
                for client_id, client_info in self.clients.items():
                    if (current_time - client_info['last_seen']) > self.heartbeat_timeout:
                        inactive_clients.append(client_id)
                
                for client_id in inactive_clients:
                    del self.clients[client_id]
                    self.logger.info(f"Removed inactive client: {client_id}")
                
    def recvMessage(self):
        """Receive message from client
        
        Returns:
            dict: Message containing 'data' and 'meta' fields, or None if error
        """
        try:
            # Receive message (blocking), ROUTER socket includes sender identity and multipart message
            parts = self.router.recv_multipart()
            # self.client_id = parts[0]  # Client identifier
            # client_id = b'\x00k\x8bEg'
            # print(f"Debug: client_id: {self.client_id}")
            message = {}
            
            if len(parts) >= 2:
                client_id = parts[0]
                data_part = pickle.loads(parts[1])  # Binary data
                meta_part = json.loads(parts[2].decode('utf8'))  # Metadata JSON
                
                # Update client tracking info
                with self._client_lock:
                    current_time = time.time()
                    # Store client info
                    self.clients[client_id] = {
                        'last_seen': current_time,
                        'address': client_id.hex() if isinstance(client_id, bytes) else str(client_id)
                    }
                
                # Check if this is a heartbeat message
                if isinstance(data_part, dict) and data_part.get('type') == 'heartbeat':
                    # Send heartbeat response
                    self.sendHeartbeatResponse(client_id)
                    
                    # Return None for heartbeat message.
                    return None
                elif isinstance(data_part, dict) and data_part.get('type') == 'test_connection':
                    # Return None for test connection message
                    return None
                else:
                    # Regular message for inference
                    message['client_id'] = client_id
                    message['data'] = data_part
                    message['meta'] = meta_part
                    return message
            else:
                self.logger.warning("Invalid message format received")
                return None
        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def sendMessage(self, client_id, data, meta={}):
        """Send message to client
        
        Args:
            client_id: Client identifier to send message to
            data: Data to send (will be pickled)
            meta: Metadata dictionary (will be JSON encoded)
        """
        try:
            with self._send_msg_lock:
                # Convert data dictionary to byte stream
                data_bytes = pickle.dumps(data)
                meta_bytes = json.dumps(meta).encode('utf8')
                self.router.send_multipart([client_id, data_bytes, meta_bytes], flags=zmq.NOBLOCK)  # Non-blocking send
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            import traceback
            traceback.print_exc()
    
    def sendHeartbeatResponse(self, client_id):
        """Send heartbeat response to client"""
        try:
            self.sendMessage(client_id, self._heartbeat_info, self._heartbeat_meta)
        except Exception as e:
            self.logger.error(f"Error sending heartbeat response: {e}")
    
    # def isClientConnected(self):
    #     """Check if any client is currently connected"""
    #     with self._client_lock:
    #         if not self.clients:
    #             return False
    #         # Check if any client has sent heartbeat recently
    #         current_time = time.time()
    #         for client_info in self.clients.values():
    #             if (current_time - client_info['last_seen']) <= self.heartbeat_timeout:
    #                 return True
    #         return False
    
    # def getClientInfo(self):
    #     """Get information about the connected client(s)"""
    #     with self._client_lock:
    #         if not self.clients:
    #             return {}  # Return empty dict instead of None to be consistent
            
    #         # Return info for all connected clients
    #         client_info_dict = {}
    #         current_time = time.time()
            
    #         for client_id, info in self.clients.items():
    #             client_hex = client_id.hex() if isinstance(client_id, bytes) else str(client_id)
    #             client_info_dict[client_hex] = {
    #                 'last_seen': info['last_seen'],
    #                 'time_since_last_seen': current_time - info['last_seen'],
    #                 'is_active': (current_time - info['last_seen']) <= self.heartbeat_timeout,
    #                 'address': info['address']
    #             }
            
    #         return client_info_dict

    def close(self):
        """Close ZMQ server and cleanup resources"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish
        self.router.close()
        self.context.term()
        self.logger.info(f'ZMQ server closed, address was: {self.server_addr}')