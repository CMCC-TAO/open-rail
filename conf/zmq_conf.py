from ml_collections import ConfigDict

def get_vla_zmq_config():
    """Generate configuration for ZMQ communication system.
    
    This function creates configuration settings for ZeroMQ communication
    between client and VLA server, including network addresses and ports.

    Returns:
        ConfigDict: Configuration dictionary for ZMQ containing:
            - client_addr: Client connection address
            - server_addr: Server binding address
    """
    config = ConfigDict()
    # config.client_addr = 'tcp://localhost:5566'  # Client connection address and port
    # config.server_addr = 'tcp://*:5566'  # Server binding address and port
    config.ip = '127.0.0.1'  # Client connection address
    config.port = '5566'     # Client connect port
    config.infer_timeout = 500     # Timeout for zmq.recv(), milliseconds
    config.heartbeat_timeout = 30000  # Timeout for remove unconnected client, milliseconds
    config.heartbeat_interval = 1000  # Heartbeat interval, milliseconds
    config.reconnect_interval = 1000  # Reconnect interval, milliseconds
    # config.server_ip = '*'          # Server binding address
    # config.server_port = '5566'     # Server binding port
    return config


def get_vis_zmq_config():
    """Generate configuration for ZMQ communication system.
    
    This function creates configuration settings for ZeroMQ communication
    between client and visualization server, including network addresses and ports.

    Returns:
        ConfigDict: Configuration dictionary for ZMQ containing:
            - client_addr: Client connection address
            - server_addr: Server binding address
    """
    config = ConfigDict()
    # config.client_addr = 'tcp://localhost:7788'  # Client connection address and port
    # config.server_addr = 'tcp://*:7788'  # Server binding address and port
    config.client_ip = 'localhost'  # Client connection address
    config.client_port = '7788'     # Client connect port
    config.server_ip = '*'          # Server binding address
    config.server_port = '7788'     # Server binding port
    return config
    