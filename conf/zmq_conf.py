from ml_collections import ConfigDict

def get_zmq_config():
    """Generate config for zmq

    Returns:
        ConfigDict: Configuration for zmq.
    """
    config = ConfigDict()
    config.client_addr = 'tcp://localhost:5566'  # server address and port
    # config.server_addr = 'tcp://*:5566' # server address and port
    config.server_addr = 'tcp://localhost:5566' # server address and port
    return config