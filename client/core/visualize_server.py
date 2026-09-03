#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import time
import threading
import os
import numpy as np
from typing import Dict, Set, Optional
from ml_collections import ConfigDict

# Limits threads used in OpenCV to avoid conflicts.
# cv2.setNumThreads(1)
class VisualizeServer:
    def __init__(self, visualize_config: ConfigDict):
        # Use a stable logger name so logging_conf.py mapping always matches,
        # including script/uvicorn execution paths.
        self.logger = logging.getLogger(__name__)
        self.config = visualize_config
        self.kill_port(self.config.port)
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False

        # Data storage
        self.latest_imgs_snapshot: Optional[tuple] = None
        self.latest_imgs_seq = 0
        self.sent_imgs_seq = -1
        self.data_lock = threading.Lock()

        # Data send queue
        self.data_send_list = []
        self._trajectory_type = ['position'] # position, velocity, and acceleration， TODO: move this to config

        # Server instance
        self.server = None
        # self._img_executor = None
        # self._create_img_executor()
        self.vis_global_step = 0
        self.vis_prev_action, self.vis_prev_state, self.vis_prev_origin = None, None, None
        self.vis_prev_action_vel, self.vis_prev_state_vel, self.vis_prev_origin_vel = None, None, None
        self.start_server()
        self.logger.info("Initializing server on %s:%d", self.config.host, self.config.port)

    def kill_port(self, port):
        os.system(f'kill -9 $(lsof -t -i:{port})')

    def update_image_data(self, imgs: Dict):
        """Update image data.

        Args:
            imgs (Dict): Image data dict, key is camera identifier, value is image array.
        """
        self.latest_imgs_seq += 1
        self.latest_imgs_snapshot = (self.latest_imgs_seq, imgs)

    # def update_chart_data(self, data: List[Dict]):
    #     """Update chart data.

    #     Args:
    #         data (List[Dict]): Data list, each element is
    #             {'tab': 'position|velocity|acceleration',
    #              'type': 'origin|action|state',
    #              'x': step, 'joints_y': values}.
    #     """
    #     with self.data_lock:
    #         for dt in data:
    #             timestamp = time.time()
    #             dt_with_ts = {**dt, 'timestamp': timestamp}
    #             self.data_send_list.append(dt_with_ts)

    #         # Bounded automatically by deque(maxlen=1000).

    def update_chart_data(self, action_fitted=None, vel_fitted=None, acc_fitted=None, action_raw=None, current_state=None, observe_period=None, control_period=None):
        """Visualize action and state data for debugging and monitoring.

        Args:
            action_fitted: Predicted action values for robot joints vel_fitted: Predicted velocity values (of action_fitted) for robot joints
            acc_fitted: Predicted acceleration values (of action_fitted) for robot joints
            action_raw: Raw action values before fitting
            current_state: Current robot joint state
        """
        timestamp = time.time()
        self.vis_global_step += 1
        data_list = []
        # with self.data_lock:
            # dt_ctrl = self.config.controller.period / 1000.0
            # Position data
        if action_fitted is not None:
            data_list.append({
                'tab': 'position',
                'type': 'action_fitted',
                'x': self.vis_global_step,
                'timestamp': timestamp,
                'joints_y': action_fitted.tolist()
            })
        if current_state is not None:
            data_list.append({
                'tab': 'position',
                'type': 'state',
                'x': self.vis_global_step,
                'timestamp': timestamp,
                'joints_y': current_state.tolist()
            })
        if action_raw is not None:
            data_list.append({
                'tab': 'position',
                'type': 'action_raw',
                'x': self.vis_global_step,
                'timestamp': timestamp,
                'joints_y': action_raw.tolist()
            })

        # TODO: use real velocity/acceleration
        # Velocity/acceleration for state (derived from state)
        with self.data_lock:
            self.data_send_list = data_list
            if 'velocity' not in self._trajectory_type and 'acceleration' not in self._trajectory_type:
                return
            state_vel = None
            state_acc = None
            if current_state is not None:
                if self.vis_prev_state is None or np.shape(self.vis_prev_state) != np.shape(current_state):
                    state_vel = np.zeros_like(current_state)
                    state_acc = np.zeros_like(current_state)
                else:
                    state_vel = (current_state - self.vis_prev_state) / control_period
                    if self.vis_prev_state_vel is None or np.shape(self.vis_prev_state_vel) != np.shape(state_vel):
                        state_acc = np.zeros_like(current_state)
                    else:
                        state_acc = (state_vel - self.vis_prev_state_vel) / control_period

                self.data_send_list.append({
                    'tab': 'velocity',
                    'type': 'state',
                    'x': self.vis_global_step,
                    'timestamp': timestamp,
                    'joints_y': state_vel.tolist()
                })
                self.data_send_list.append({
                    'tab': 'acceleration',
                    'type': 'state',
                    'x': self.vis_global_step,
                    'timestamp': timestamp,
                    'joints_y': state_acc.tolist()
                })

            # Velocity/acceleration for action (direct input)
            if vel_fitted is not None:
                self.data_send_list.append({
                    'tab': 'velocity',
                    'type': 'action_fitted',
                    'x': self.vis_global_step,
                    'timestamp': timestamp,
                    'joints_y': vel_fitted.tolist()
                })
            if acc_fitted is not None:
                self.data_send_list.append({
                    'tab': 'acceleration',
                    'type': 'action_fitted',
                    'x': self.vis_global_step,
                    'timestamp': timestamp,
                    'joints_y': acc_fitted.tolist()
                })

            # Origin (raw action) series
            if action_raw is not None:
                if self.vis_prev_origin is None or np.shape(self.vis_prev_origin) != np.shape(action_raw):
                    origin_vel = np.zeros_like(action_raw)
                    origin_acc = np.zeros_like(action_raw)
                else:
                    origin_vel = (action_raw - self.vis_prev_origin) / observe_period
                    if self.vis_prev_origin_vel is None or np.shape(self.vis_prev_origin_vel) != np.shape(origin_vel):
                        origin_acc = np.zeros_like(action_raw)
                    else:
                        origin_acc = (origin_vel - self.vis_prev_origin_vel) / observe_period

                self.data_send_list.append({
                    'tab': 'velocity',
                    'type': 'action_raw',
                    'x': self.vis_global_step,
                    'timestamp': timestamp,
                    'joints_y': origin_vel.tolist()
                })
                self.data_send_list.append({
                    'tab': 'acceleration',
                    'type': 'action_raw',
                    'x': self.vis_global_step,
                    'timestamp': timestamp,
                    'joints_y': origin_acc.tolist()
                })
                self.vis_prev_origin = action_raw
                self.vis_prev_origin_vel = origin_vel


            # Update previous values only for available inputs
            if action_fitted is not None:
                self.vis_prev_action = action_fitted
            if vel_fitted is not None:
                self.vis_prev_action_vel = vel_fitted
            if current_state is not None:
                self.vis_prev_state = current_state
            if state_vel is not None:
                self.vis_prev_state_vel = state_vel

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

    # @staticmethod
    # def _cfg_get(cfg, key, default=False):
    #     if cfg is None:
    #         return default
    #     if isinstance(cfg, dict):
    #         return bool(cfg.get(key, default))
    #     return bool(getattr(cfg, key, default))

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
        return {
            0: getattr(self.config.camera, 'open_head', True),
            1: getattr(self.config.camera, 'open_wrist_left', True),
            2: getattr(self.config.camera, 'open_wrist_right', True)
        }

    async def send_camera_data(self):
        """Send camera frames to all clients using binary transport."""
        if not self.clients:
            return

        current_timestamp = time.time()

        disconnected_clients = set()

        # Snapshot latest images; skip if no new frame since last send.
        if not self.latest_imgs_snapshot:
            return
        # imgs = self.latest_imgs.copy()
        # imgs = self.latest_imgs
        img_seq, imgs = self.latest_imgs_snapshot
        if img_seq == self.sent_imgs_seq:
            return

        camera_open = self._get_camera_open_map()

        for camera_key, img in imgs.items():
            try:
                camera_id = self._camera_id_from_key(camera_key)
                if camera_id is None:
                    self.logger.warning(f"Unknown camera key: {camera_key}")
                    continue
                if not camera_open.get(camera_id, True):
                    continue

                frame_bytes = img.tobytes()

                header = {
                    'type': 'camera_data_binary',
                    'camera_id': camera_id,
                    'timestamp': current_timestamp,
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

        self.sent_imgs_seq = img_seq

        for client in disconnected_clients:
            await self.unregister_client(client)

    async def send_chart_data(self):
        """Send chart (joint trajectory) data to all clients in one batched message."""
        if not self.clients or not self.data_send_list:
            return

        disconnected_clients = set()

        with self.data_lock:
            data_to_send = self.data_send_list
            self.data_send_list = []

        if not data_to_send:
            return

        message_json = json.dumps({
            'type': 'joint_data_batch',
            'data': data_to_send,
            'count': len(data_to_send),
            'timestamp': time.time()
        })

        for client in self.clients.copy():
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.warning("Failed to send chart data batch to client: %s", e)
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
                        'has_image_data': self.latest_imgs_snapshot is not None,
                        'chart_queue_size': len(self.data_send_list)
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
        """
        Main data-sending loop: camera frames and chart data at up to 50 Hz.

        This asynchronous method continuously sends camera frames and chart data 
        while the instance is running. The loop frequency is determined by the 
        configured `updata_fps` setting. If an exception occurs during the 
        sending process, it logs the error and waits for 1 second before 
        retrying to prevent tight error loops.

        Raises:
            Exception: Catches and logs any exception that occurs within the 
                    data sending loop, allowing the loop to continue running.
        """
        while self.running:
            try:
                await self.send_camera_data()
                await self.send_chart_data()
                await asyncio.sleep(1/self.config.updata_fps)
            except Exception as e:
                self.logger.error("Data sender loop error: %s", e)
                await asyncio.sleep(1)
    async def _server_running_fun(self):
        """Start the WebSocket server and the data-sending loop."""
        self.running = True
        self._shutdown_event = asyncio.Event()

        async with websockets.serve(
            self.client_handler,
            self.config.host,
            self.config.port,
            compression=None,
            max_size=self.config.max_size,
            ping_interval=self.config.ping_interval,
            ping_timeout=self.config.ping_timeout
        ) as server:
            self.server = server
            self.logger.info("Server started: ws://%s:%d", self.config.host, self.config.port)
            
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

    # def _create_img_executor(self):
    #     if getattr(self, '_img_executor', None) is None or getattr(self._img_executor, '_shutdown', False):
    #         self._img_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vis_img_enc")

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
        # self._create_img_executor()
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
