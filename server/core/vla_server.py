import os
import time
import numpy as np
import threading
import cv2
import queue
from ml_collections import ConfigDict
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from .zmq_server import ZMQServer
class VLAServer:
    """VLA (Vision-Language-Action) Server for handling inference requests
    
    This server manages the inference pipeline for VLA models, including:
    - Receiving data from ZMQ clients
    - Decoding image data in parallel
    - Running model inference
    - Sending results back to clients
    """
    
    def __init__(self, config: ConfigDict, zmq_server: ZMQServer,  model= None):
        """Initialize VLA Server
        
        Args:
            config: Configuration dictionary containing server settings
            zmq_server: ZMQ server instance for communication
            model: VLA model instance for inference
        """
        self.config = config
        self.zmq_server = zmq_server
        self.model = model

        self.running = False
        self.last_inference_time = 0
        
        # Create thread pool for handling inference tasks
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        # Create thread pool for parallel image decoding
        self.image_decode_executor = ThreadPoolExecutor(max_workers=3)
        # Create lock to protect shared variables
        self.thread_lock = threading.Lock()
        
        self.receive_thread = threading.Thread(target=self.recvThreadFun, daemon=True)

    def run(self):
        """Start the VLA server and begin processing requests"""
        # Start receiving thread
        self.running = True
        self.receive_thread.start()
        # Wait for thread to finish
        self.receive_thread.join()
    
    def image_decode(self, key, data):
        """Decode image data for a specific observation key
        
        Args:
            key: The observation key (e.g., 'cam.head')
            data: Data dictionary containing encoded image
        """
        data['obs'][key] = cv2.imdecode(data['obs'][key], cv2.IMREAD_COLOR)
    
    def inference(self, data):
        """Process inference request with image decoding and model inference
        
        Args:
            data: Input data containing observations and other information
        """
        try:
            # Decode image data with parallel processing
            start_time = time.time()
            if isinstance(data, list):
                # Process multiple data items
                for data_item in data:
                    cam_keys = [key for key in data_item['obs'] if 'cam.' in key]
                    images_data = [(key, data_item['obs'][key]) for key in cam_keys]
                    with ThreadPoolExecutor() as executor:
                        decoded_images = list(executor.map(lambda d: cv2.imdecode(d[1], cv2.IMREAD_ANYDEPTH if 'depth.' in d[0] else cv2.IMREAD_COLOR), images_data))
                    for key, img in zip(cam_keys, decoded_images):
                        data_item['obs'][key] = img
            else:
                # Use thread pool for parallel image decoding
                cam_keys = [key for key in data['obs'] if 'cam.' in key]
                images_data = [(key, data['obs'][key]) for key in cam_keys]
                with ThreadPoolExecutor() as executor:
                    decoded_images = list(executor.map(lambda d: cv2.imdecode(d[1], cv2.IMREAD_ANYDEPTH if 'depth.' in d[0] else cv2.IMREAD_COLOR), images_data))
                for key, img in zip(cam_keys, decoded_images):
                    data['obs'][key] = img
                print(f'data[obs] keys: {data.keys()}')
            
            end_time = time.time()
            # Calculate and print execution time
            elapsed_time = (end_time - start_time) * 1000
            print(f"Image decoding time: {elapsed_time} ms")

            # Submit inference task to thread pool
            future = self.executor.submit(self.model.infer, data if isinstance(data, list) else [data])
            future.add_done_callback(self.inference_callback)
        except Exception as e:
            print(f"Error processing inference queue: {e}")
            import traceback
            traceback.print_exc()
    
    def inference_callback(self, future):
        """Callback function for handling inference results
        
        Args:
            future: Future object containing inference results
        """
        try:
            result = future.result()  # Get thread result
            print(result)
            self.zmq_server.sendMessage(result)
        except Exception as e:
            print(f"Error in inference callback: {e}")
            import traceback
            traceback.print_exc()
    
    def recvThreadFun(self):
        """Main receiving thread function for processing incoming messages"""
        print('Start to receive data and infer...')
        while self.running:
            message = self.zmq_server.recvMessage()
            self.inference(message['data'])
        print('Stop to receive data...')
    
    def close(self):
        """Close the VLA server and cleanup resources"""
        # Stop threads
        with self.thread_lock:
            self.running = False
        self.executor.shutdown(wait=False)
        self.zmq_server.close()
