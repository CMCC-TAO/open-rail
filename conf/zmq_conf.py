from ml_collections import ConfigDict

def get_zmq_config():
    """Generate configuration for ZMQ communication system.
    
    This function creates configuration settings for ZeroMQ communication
    between client and server, including network addresses and ports.

    Returns:
        ConfigDict: Configuration dictionary for ZMQ containing:
            - client_addr: Client connection address
            - server_addr: Server binding address
    """
    config = ConfigDict()
    config.client_addr = 'tcp://localhost:5566'  # Client connection address and port
    config.server_addr = 'tcp://*:5566'  # Server binding address and port
    return config