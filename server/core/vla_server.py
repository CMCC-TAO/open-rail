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
        
        # Statistics for Live display
        self.request_count = 0
        self.total_inference_time = 0.0
        self.avg_inference_time = 0.0
        self.inference_times = deque(maxlen=100)  # Keep last 100 inference times
        self.obs_info, self.act_info = {}, {}
        self.debug_info = "The debug information or trace information will be displayed here."
        
        # Create thread pool for handling inference tasks
        self.executor = ThreadPoolExecutor(max_workers=config.max_infer_workers)
        # Create thread pool for parallel image decoding
        self.image_decode_executor = ThreadPoolExecutor(max_workers=config.max_decode_workers)
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
    
    def _pad_and_resize(self, img, target_height=640, target_width=640, pad_color=(0, 0, 0)):
        """Pad and resize image to target dimensions while maintaining aspect ratio.
        
        Args:
            img: Input image array
            target_height (int): Target height in pixels
            target_width (int): Target width in pixels
            pad_color (tuple): RGB color for padding (default: black)
            
        Returns:
            numpy.ndarray: Padded and resized image
        """
        height, width = img.shape[:2]
        # print(f"Debug: raw shape={height}x{width}, target shape={target_width}x{target_height}")
        target_ratio = target_width / target_height
        current_ratio = width / height

        # Calculate edges to pad
        if current_ratio > target_ratio:
            # Pad height (width is the longer side)
            new_height = int(width / target_ratio)  # Calculate new height based on target ratio
            delta = new_height - height
            top = delta // 2
            bottom = delta - top
            padded = cv2.copyMakeBorder(img, top, bottom, 0, 0, cv2.BORDER_CONSTANT, value=pad_color)  # Keep width unchanged, pad top and bottom
        elif current_ratio < target_ratio:
            # Pad width (height is the longer side)
            new_width = int(height * target_ratio)  # Calculate new width based on target ratio
            delta = new_width - width
            left = delta // 2
            right = delta - left
            padded = cv2.copyMakeBorder(img, 0, 0, left, right, cv2.BORDER_CONSTANT, value=pad_color)  # Keep height unchanged, pad left and right
        else:
            padded = img

        # Resize to target dimensions (using INTER_AREA interpolation suitable for downscaling)
        if max(height, width) != max(target_width, target_height):
            resized = cv2.resize(padded, (target_width, target_height), interpolation=cv2.INTER_AREA)
            # print(f"Debug: resized shape={resized.shape}")
            return resized
        else:
            # print(f"Debug: resized shape={padded.shape}")
            return padded

    def _image_decode_thread_func(self, key, encoded_img):
        """Decode image data for a specific observation key
        
        Args:
            key: The observation key (e.g., 'cam.head')
            data: np.array, the encoded image
        """
        decoded_img = cv2.imdecode(encoded_img, cv2.IMREAD_ANYDEPTH if 'depth.' in key else cv2.IMREAD_COLOR)
        padded_img = self._pad_and_resize(decoded_img)
        return key, padded_img[:, :, ::-1] # RGB to BGR
    
    def _process_image(self, frame):
        # futures = [self.image_decode_executor.submit(self._image_decode_thread_func, key, value) for key, value in frame if 'cam.' in key]
        futures = [self.image_decode_executor.submit(self._image_decode_thread_func, key, value) for key, value in frame.items() if 'cam.' in key]
        results = [future.result() for future in futures]  # Wait for all tasks to complete
        # encoded_imgs = {}
        # for key, encoded_img in results:
        #     encoded_imgs[key] = encoded_img

        return results
    
    def inference(self, data, meta=None):
        """Process inference request with image decoding and model inference
        
        Args:
            data: Input data containing observations and other information
            meta: Optional metadata dict from client request.
        """
        try:
            # Decode image data with parallel processing
            start_time = time.time()
            if isinstance(data, list):
                # Process multiple data items
                for data_item in data:
                    # cam_keys = [key for key in data_item['obs'] if 'cam.' in key]
                    # images_data = [(key, data_item['obs'][key]) for key in cam_keys]
                    # with ThreadPoolExecutor() as executor:
                    #     decoded_images = list(executor.map(lambda d: cv2.imdecode(d[1], cv2.IMREAD_ANYDEPTH if 'depth.' in d[0] else cv2.IMREAD_COLOR), images_data))
                    processed_imgs = self._process_image(data_item['obs'])
                    for key, img in processed_imgs:
                        data_item['obs'][key] = img
            else:
                # Use thread pool for parallel image decoding
                # print(f"Debug: type(data['obs']) = {type(data['obs'])}")
                # cam_keys = [key for key in data['obs'] if 'cam.' in key]
                # images_data = [(key, data['obs'][key]) for key in cam_keys]
                # with ThreadPoolExecutor() as executor:
                #     decoded_images = list(executor.map(lambda d: cv2.imdecode(d[1], cv2.IMREAD_ANYDEPTH if 'depth.' in d[0] else cv2.IMREAD_COLOR), images_data))
                processed_imgs = self._process_image(data['obs'])
                for key, img in processed_imgs:
                    # print(f"Debug: image shape before process: {data['obs'][key].shape}")
                    data['obs'][key] = img
                    # print(f"Debug: image shape after process: {data['obs'][key].shape}")
            
            end_time = time.time()
            # Calculate and print execution time
            elapsed_time = end_time - start_time
            self.obs_info['img_decode_time'] = round(elapsed_time, 4)

            # Update request count
            with self.thread_lock:
                self.request_count += 1
            
            # Submit inference task to thread pool with timing
            inference_start_time = time.time()
            model_data = data if isinstance(data, list) else [data]
            future = self.executor.submit(self.model.infer, model_data)
            future.add_done_callback(lambda f: self.inference_callback(f, inference_start_time, meta=meta))
            for key, value in model_data[0]['obs'].items():
                if 'cam.' in key:
                    self.obs_info[key] = value.shape
                elif 'state' in key:
                    self.obs_info[key] = value.shape
                elif 'language' in key:
                    self.obs_info[key] = value
            self.obs_info['obs_comm_delay'] = time.perf_counter() - model_data[0]['loc_timestamp']
        except Exception as e:
            print(f"Error processing inference queue: {e}")
            import traceback
            traceback.print_exc()
    
    def inference_callback(self, future, start_time, meta=None):
        """Callback function for handling inference results
        
        Args:
            future: Future object containing inference results
            start_time: Inference start time for timing calculation
            meta: Optional metadata dict from request.
        """
        try:
            result = future.result()  # Get thread result
            
            # Calculate inference time and update statistics
            inference_time = time.time() - start_time
            with self.thread_lock:
                self.inference_times.append(inference_time)
                self.total_inference_time += inference_time
                # Calculate rolling average from recent inference times
                if self.inference_times:
                    self.avg_inference_time = sum(self.inference_times) / len(self.inference_times)
            self.zmq_server.sendMessage(result, meta=meta or {})
            self.act_info['pred_action'] = result['pred_action']
        except Exception as e:
            print(f"Error in inference callback: {e}")
            import traceback
            traceback.print_exc()
    
    def recvThreadFun(self):
        """Main receiving thread function for processing incoming messages"""
        print('Start to receive data and infer...')
        while self.running:
            message = self.zmq_server.recvMessage()
            if message is None or 'data' not in message:
                continue
            self.inference(message['data'], message.get('meta', {}))
        print('Stop to receive data...')
    
    def close(self):
        """Close the VLA server and cleanup resources"""
        # Stop threads
        with self.thread_lock:
            self.running = False
        self.executor.shutdown(wait=False)
        self.zmq_server.close()
