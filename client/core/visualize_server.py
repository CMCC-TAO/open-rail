#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import time
import threading
import os
import cv2
import numpy as np
from collections import deque
from typing import Dict, List, Set, Optional
from concurrent.futures import ThreadPoolExecutor
from ml_collections import ConfigDict

# Limits threads used in OpenCV to avoid conflicts.
cv2.setNumThreads(1)
class VisualizeServer:
    def __init__(self, visualize_config: ConfigDict):
        # Use a stable logger name so logging_conf.py mapping always matches,
        # including script/uvicorn execution paths.
        self.logger = logging.getLogger(__name__)
        self.config = visualize_config
        self.logger.info("Initializing server on %s:%d", self.config.server.host, self.config.server.port)
        self.kill_port(self.config.server.port)
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False

        # Data storage
        self.latest_imgs: Optional[Dict] = None
        self.latest_imgs_seq = 0
        self.sent_imgs_seq = -1
        self.data_lock = threading.Lock()
        self.camera_send_interval = 1.0 / 30.0
        self.chart_send_interval = 1.0 / 30.0
        self._last_camera_send_ts = 0.0
        self._last_chart_send_ts = 0.0

        # Data send queue (deque gives O(1) append/popleft; bounded by maxlen)
        self.data_send_queue = deque(maxlen=1000)

        # Server instance
        self.server = None
        self._img_executor = None
        self._create_img_executor()

    def kill_port(self, port):
        os.system(f'kill -9 $(lsof -t -i:{port})')

    def update_image_data(self, imgs: Dict):
        """Update image data.

        Args:
            imgs (Dict): Image data dict, key is camera identifier, value is image array.
        """
        with self.data_lock:
            self.latest_imgs = imgs.copy()
            self.latest_imgs_seq += 1

    def update_chart_data(self, data: List[Dict]):
        """Update chart data.

        Args:
            data (List[Dict]): Data list, each element is
                {'tab': 'position|velocity|acceleration',
                 'type': 'origin|action|state',
                 'x': step, 'joints_y': values}.
        """
        with self.data_lock:
            for dt in data:
                timestamp = time.time()
                dt_with_ts = {**dt, 'timestamp': timestamp}
                self.data_send_queue.append(dt_with_ts)

            # Bounded automatically by deque(maxlen=1000).

    async def register_client(self, websocket):
        """Register a new WebSocket client."""
        self.clients.add(websocket)
        self.logger.info("Client connected. Active connections: %d", len(self.clients))

        config_message = {
            'type': 'config',
            'data': {
                'cameras': [],   # Updated dynamically when data arrives
                'joints': []     # Updated dynamically when data arrives
            }
        }
        await websocket.send(json.dumps(config_message))

    async def unregister_client(self, websocket):
        """Unregister a WebSocket client."""
        self.clients.discard(websocket)
        self.logger.info("Client disconnected. Active connections: %d", len(self.clients))

    @staticmethod
    def _cfg_get(cfg, key, default=False):
        if cfg is None:
            return default
        if isinstance(cfg, dict):
            return bool(cfg.get(key, default))
        return bool(getattr(cfg, key, default))

    @staticmethod
    def _camera_id_from_key(camera_key: str):
        k = str(camera_key).lower()
        if 'hand_left' in k or 'left_wrist' in k or 'wrist_left' in k:
            return 1
        if 'hand_right' in k or 'right_wrist' in k or 'wrist_right' in k:
            return 2
        if 'head' in k:
            return 0
        return None

    def _get_camera_open_map(self):
        camera_cfg = getattr(self.config, 'camera', None)
        return {
            0: self._cfg_get(camera_cfg, 'open_head', True),
            1: self._cfg_get(camera_cfg, 'open_wrist_left', True),
            2: self._cfg_get(camera_cfg, 'open_wrist_right', True),
        }

    async def send_camera_data(self):
        """Send camera frames to all clients using binary transport."""
        if not self.clients:
            return

        now = time.time()
        if now - self._last_camera_send_ts < self.camera_send_interval:
            return

        disconnected_clients = set()

        # Snapshot latest images; skip if no new frame since last send.
        with self.data_lock:
            if not self.latest_imgs or self.latest_imgs_seq == self.sent_imgs_seq:
                return
            imgs = self.latest_imgs.copy()
            img_seq = self.latest_imgs_seq

        camera_open = self._get_camera_open_map()

        sent_camera_ids = set()

        for camera_key, img in imgs.items():
            try:
                camera_id = self._camera_id_from_key(camera_key)
                if camera_id is None:
                    continue
                if camera_id in sent_camera_ids:
                    continue
                if not camera_open.get(camera_id, True):
                    continue

                frame_bytes = img.tobytes()

                sent_camera_ids.add(camera_id)

                header = {
                    'type': 'camera_data_binary',
                    'camera_id': camera_id,
                    'timestamp': time.time(),
                    'data_size': len(frame_bytes)
                }
                header_bytes = json.dumps(header).encode('utf-8')
                header_length = len(header_bytes)
                message = header_length.to_bytes(4, byteorder='big') + header_bytes + frame_bytes

                for client in self.clients.copy():
                    try:
                        await client.send(message)
                    except websockets.exceptions.ConnectionClosed as e:
                        self.logger.warning("Failed to send camera frame to client: %s", e)
                        disconnected_clients.add(client)
                    except Exception as e:
                        self.logger.warning("Failed to send camera frame to client: %s", e)
                        disconnected_clients.add(client)

            except Exception as e:
                self.logger.warning("Failed to process camera data for key '%s': %s", camera_key, e)

        self._last_camera_send_ts = now
        with self.data_lock:
            self.sent_imgs_seq = max(self.sent_imgs_seq, img_seq)

        for client in disconnected_clients:
            await self.unregister_client(client)

    async def send_chart_data(self):
        """Send chart (joint trajectory) data to all clients."""
        if not self.clients or not self.data_send_queue:
            return
        now = time.time()
        if now - self._last_chart_send_ts < self.chart_send_interval:
            return
        self._last_chart_send_ts = now

        disconnected_clients = set()

        with self.data_lock:
            data_to_send = self.data_send_queue.copy()
            self.data_send_queue.clear()

        for data_packet in data_to_send:
            message_json = json.dumps({'type': 'joint_data', 'data': data_packet})

            for client in self.clients.copy():
                try:
                    await client.send(message_json)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    self.logger.warning("Failed to send chart data to client: %s", e)
                    disconnected_clients.add(client)

        for client in disconnected_clients:
            await self.unregister_client(client)

    async def handle_client_message(self, websocket, message):
        """Parse and dispatch a message received from a client."""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'ping':
                await websocket.send(json.dumps({'type': 'pong', 'timestamp': time.time()}))
            elif message_type == 'get_status':
                status = {
                    'type': 'status',
                    'data': {
                        'connected_clients': len(self.clients),
                        'has_image_data': self.latest_imgs is not None,
                        'chart_queue_size': len(self.data_send_queue)
                    }
                }
                await websocket.send(json.dumps(status))
            elif message_type == 'control_command':
                await self.handle_control_command(data.get('command'), data.get('params', {}))
                response = {
                    'type': 'command_response',
                    'command': data.get('command'),
                    'status': 'received'
                }
                await websocket.send(json.dumps(response))

        except json.JSONDecodeError:
            self.logger.warning("Received invalid JSON message from client.")
        except Exception as e:
            self.logger.error("Error handling client message: %s", e)

    async def handle_control_command(self, command, params):
        """Handle a control command received from a client."""
        self.logger.info("Received control command: %s, params: %s", command, params)

    async def client_handler(self, websocket):
        """Manage the lifecycle of a single client connection."""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            self.logger.error("Client handler error: %s", e)
        finally:
            await self.unregister_client(websocket)

    async def data_sender(self):
        """Main data-sending loop: camera frames and chart data at up to 50 Hz."""
        while self.running:
            try:
                await self.send_camera_data()
                await self.send_chart_data()
                await asyncio.sleep(0.02)
            except Exception as e:
                self.logger.error("Data sender loop error: %s", e)
                await asyncio.sleep(1)
    async def _server_running_fun(self):
        """Start the WebSocket server and the data-sending loop."""
        self.running = True
        self._shutdown_event = asyncio.Event()

        async with websockets.serve(
            self.client_handler,
            self.config.server.host,
            self.config.server.port,
            max_size=self.config.server.max_size,
            ping_interval=self.config.server.ping_interval,
            ping_timeout=self.config.server.ping_timeout
        ) as server:
            self.server = server
            self.logger.info("Server started: ws://%s:%d", self.config.server.host, self.config.server.port)
            
            data_sender_task = asyncio.create_task(self.data_sender())
            try:
                # 使用 Event 替代 wait_closed，通过 set() 优雅退出
                await self._shutdown_event.wait()
            finally:
                data_sender_task.cancel()
                try:
                    await data_sender_task
                except asyncio.CancelledError:
                    pass

    def stop_server(self):
        """Stop the WebSocket server."""
        self.running = False
        if self.server:
            # 触发事件通知异步循环退出
            if hasattr(self, '_shutdown_event') and self._shutdown_event.is_set() is False:
                self._shutdown_event.set()
            self.logger.info("Server stop signal sent.")
    # def stop_server(self):
    #     """Stop the WebSocket server."""
    #     self.running = False
    #     if self.server:
    #         self.server.close()
    #         self.logger.info("Visualize Serverstopped.")

    def _create_img_executor(self):
        if getattr(self, '_img_executor', None) is None or getattr(self._img_executor, '_shutdown', False):
            self._img_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vis_img_enc")

    def _main_thread_fun(self):
        """Run the Visualize Server in a dedicated asyncio event loop (background thread)."""
        try:
            asyncio.run(self._server_running_fun())
        except Exception as e:
            self.logger.error("Server error: %s", e)

    def start_server(self):
        """Start the server in a background daemon thread (idempotent)."""
        if hasattr(self, 'main_thread') and self.main_thread and self.main_thread.is_alive():
            return
        self._create_img_executor()
        self.main_thread = threading.Thread(
            target=self._main_thread_fun,
            daemon=True
        )
        self.main_thread.start()


def main():
    """Entry point for standalone testing."""
    from conf.logging_conf import setup_logging

    setup_logging("client.log", "client.core.visualize_server")

    server = VisualizeServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        server.logger.info("Interrupt received, shutting down server.")
        server.stop_server()


if __name__ == "__main__":
    main()
