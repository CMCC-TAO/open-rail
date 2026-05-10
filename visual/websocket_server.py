#!/usr/bin/env python3
import asyncio
import websockets
import json
import numpy as np
import time
import threading
from typing import Dict, List, Set, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import cv2

# 限制 OpenCV 线程，降低与解码端并发冲突概率
cv2.setNumThreads(1)


class VLAWebSocketServer:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host='0.0.0.0', port=8765):
        if self.__class__._initialized:
            return
        self.__class__._initialized = True
         # 设置 OpenCV 线程数为 1，避免多线程问题
        # cv2.setNumThreads(1)
        self.kill_port(port)
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False
        
        # 数据存储
        self.latest_imgs: Optional[Dict] = None
        self.latest_chart_data: List[Dict] = []
        self.camera_open = {0: True, 1: True, 2: True}  # 0=head, 1=left wrist, 2=right wrist
        self.data_lock = threading.Lock()
        
        # 数据发送队列
        self.data_send_queue = []
        
        # 服务器实例
        self.server = None

        self._run_http_server_thread()

    @classmethod
    def get_instance(cls, host='0.0.0.0', port=8765):
        return cls(host=host, port=port)

    def kill_port(self, port):
        os.system(f'kill -9 $(lsof -t -i:{port})')  # 杀掉占用端口的进程

    def _start_http_server(self, port=8080, directory=None):
        if directory:
            os.chdir(directory)  # 切换到指定目录
        
        # 创建HTTP服务器
        server = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)
        print(f"web服务器启动在 http://localhost:{port}, 根目录: {directory or os.getcwd()}")
        server.serve_forever()

    def _run_http_server_thread(self, port=8080, directory=os.path.dirname(os.path.abspath(__file__))):
        """在单独线程中运行HTTP服务器"""
        http_thread = threading.Thread(
            target=self._start_http_server,
            args=(port, directory),
            daemon=True
        )
        http_thread.start()
        
    def update_image_data(self, imgs: Dict, camera_cfg=None):
        """更新图像数据

        Args:
            imgs (Dict): 图像数据，key为摄像头标识，value为图像数据
            camera_cfg: 相机显示配置，支持 open_head/open_wrist_left/open_wrist_right
        """
        if camera_cfg is not None:
            self.update_camera_open_config(camera_cfg)

        with self.data_lock:
            self.latest_imgs = imgs.copy()
        # print(f"图像数据已更新，包含摄像头: {list(imgs.keys())}")

    def update_chart_data(self, data: List[Dict]):
        """更新图表数据
        
        Args:
            data (List[Dict]): 数据列表，每个元素为 {'tab': 'position|velocity|acceleration', 'type': 'origin|action|state', 'x': step, 'joints_y': values}
        """
        with self.data_lock:
            for dt in data:
                # 添加时间戳
                timestamp = time.time()
                dt_with_ts = {**dt, 'timestamp': timestamp}
                self.data_send_queue.append(dt_with_ts)

            # 保持队列大小，避免内存溢出
            if len(self.data_send_queue) > 1000:
                self.data_send_queue = self.data_send_queue[-500:]
        
        # print(f"chart_data: {self.data_send_queue}")
    
    async def register_client(self, websocket):
        """注册新客户端"""
        self.clients.add(websocket)
        print(f"客户端已连接，当前连接数: {len(self.clients)}")
        
        # 发送初始配置信息
        config_message = {
            'type': 'config',
            'data': {
                'cameras': [],  # 将在有数据时动态更新
                'joints': []    # 将在有数据时动态更新
            }
        }
        await websocket.send(json.dumps(config_message))
    
    async def unregister_client(self, websocket):
        """注销客户端"""
        self.clients.discard(websocket)
        print(f"客户端已断开，当前连接数: {len(self.clients)}")

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
        if 'hand_left' in k or 'left_wrist' in k or 'wrist_left' in k or '.left' in k:
            return 1
        if 'hand_right' in k or 'right_wrist' in k or 'wrist_right' in k or '.right' in k:
            return 2
        if 'head' in k or '.top' in k:
            return 0
        return None

    def update_camera_open_config(self, camera_cfg):
        with self.data_lock:
            self.camera_open[0] = self._cfg_get(camera_cfg, 'open_head', True)
            self.camera_open[1] = self._cfg_get(camera_cfg, 'open_wrist_left', True)
            self.camera_open[2] = self._cfg_get(camera_cfg, 'open_wrist_right', True)

    async def send_camera_data(self):
        """发送摄像头数据 - 使用二进制传输优化性能"""
        if not self.clients:
            # print(f"No client is connected.")
            return
        if not self.latest_imgs:
            # print(f"No latest images.")
            return
        
        disconnected_clients = set()
        
        # 获取最新的图像数据
        with self.data_lock:
            imgs = self.latest_imgs.copy() if self.latest_imgs else {}
            camera_open = self.camera_open.copy()

        # 为每个摄像头发送单独的二进制消息
        for index, (camera_key, img) in enumerate(imgs.items()):
            try:
                mapped_id = self._camera_id_from_key(camera_key)
                camera_id = mapped_id if mapped_id is not None else index
                if camera_id in (0, 1, 2) and not camera_open.get(camera_id, True):
                    continue

                # 将numpy数组转换为bytes
                if isinstance(img, np.ndarray):
                    # img = cv2.resize(img, (w // 2, h // 2))  # 降低分辨率以减少数据量
                    if 'depth.' in camera_key:
                        img_depth_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                        img_for_encode = cv2.applyColorMap(img_depth_norm, cv2.COLORMAP_JET)
                    else:
                        # 避免 cv2.cvtColor 额外并发调用；同时统一到 uint8，防止 CV_64F 导致编码异常
                        img_uint8 = img if img.dtype == np.uint8 else np.clip(img, 0, 255).astype(np.uint8)
                        img_for_encode = img_uint8[:, :, ::-1] if img_uint8.ndim == 3 and img_uint8.shape[2] == 3 else img_uint8
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 80]
                    ok, enc = cv2.imencode('.jpg', img_for_encode, encode_params)
                    if not ok:
                        continue
                    frame_bytes = enc.tobytes()
                else:
                    frame_bytes = img

                # 创建消息头（JSON格式）
                header = {
                    'type': 'camera_data_binary',
                    'camera_id': camera_id,
                    'timestamp': time.time(),
                    'data_size': len(frame_bytes)
                }
                header_json = json.dumps(header)
                header_bytes = header_json.encode('utf-8')
                
                # 创建完整消息：头部长度(4字节) + 头部 + 图像数据
                header_length = len(header_bytes)
                message = header_length.to_bytes(4, byteorder='big') + header_bytes + frame_bytes
                
                # 发送给所有客户端
                for client in self.clients.copy():
                    try:
                        await client.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        disconnected_clients.add(client)
                    except Exception as e:
                        print(f"发送图像数据失败: {e}")
                        disconnected_clients.add(client)
                        
            except Exception as e:
                print(f"处理图像数据失败 {camera_key}: {e}")
        # print(f"已发送摄像头数据，包含摄像头: {list(imgs.keys())}")
        # 清理断开的客户端
        for client in disconnected_clients:
            await self.unregister_client(client)
    
    async def send_chart_data(self):
        """发送图表数据"""
        if not self.clients or not self.data_send_queue:
            return
        
        disconnected_clients = set()
        
        # 获取待发送的数据
        with self.data_lock:
            data_to_send = self.data_send_queue.copy()
            self.data_send_queue.clear()
        
        # 发送数据
        for data_packet in data_to_send:
            message = {
                'type': 'joint_data',
                'data': data_packet
            }
            message_json = json.dumps(message)
            
            for client in self.clients.copy():
                try:
                    await client.send(message_json)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    print(f"发送图表数据失败: {e}")
                    disconnected_clients.add(client)
        
        # 清理断开的客户端
        for client in disconnected_clients:
            await self.unregister_client(client)
    
    async def handle_client_message(self, websocket, message):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # 响应心跳
                response = {
                    'type': 'pong',
                    'timestamp': time.time()
                }
                await websocket.send(json.dumps(response))
            elif message_type == 'get_status':
                # 返回服务器状态
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
                # 处理控制命令
                await self.handle_control_command(data.get('command'), data.get('params', {}))
                # 发送确认响应
                response = {
                    'type': 'command_response',
                    'command': data.get('command'),
                    'status': 'received'
                }
                await websocket.send(json.dumps(response))
                
        except json.JSONDecodeError:
            print("收到无效的JSON消息")
        except Exception as e:
            print(f"处理客户端消息失败: {e}")
    
    async def handle_control_command(self, command, params):
        """处理控制命令"""
        print(f"收到控制命令: {command} with params: {params}")
    
    async def client_handler(self, websocket):
        """处理客户端连接"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"客户端处理错误: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def data_sender(self):
        """数据发送循环"""
        while self.running:
            try:
                # 发送摄像头数据
                await self.send_camera_data()
                
                # 发送图表数据
                await self.send_chart_data()
                await asyncio.sleep(0.01)
                
            except Exception as e:
                print(f"数据发送循环错误: {e}")
                await asyncio.sleep(1)
    
    async def start_server(self):
        """启动WebSocket服务器"""
        self.running = True
        
        # 启动WebSocket服务器
        self.server = await websockets.serve(
            self.client_handler,
            self.host,
            self.port,
            max_size=10 * 1024 * 1024,  # 10MB max message size
            ping_interval=20,
            ping_timeout=10
        )
        
        print(f"VLA WebSocket服务器已启动: ws://{self.host}:{self.port}")
        
        # 启动数据发送任务
        data_sender_task = asyncio.create_task(self.data_sender())
        
        try:
            # 等待服务器关闭
            await self.server.wait_closed()
        finally:
            data_sender_task.cancel()
            try:
                await data_sender_task
            except asyncio.CancelledError:
                pass
    
    def stop_server(self):
        """停止WebSocket服务器"""
        self.running = False
        if self.server:
            self.server.close()
            print("VLA WebSocket服务器已停止")

    def _run_loop_server(self):
        """Run WebSocket server in asyncio event loop"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the server
            loop.run_until_complete(self.start_server())
        except Exception as e:
            print(f"WebSocket server error: {e}")

    def run(self):
        if hasattr(self, 'websocket_thread') and self.websocket_thread and self.websocket_thread.is_alive():
            return
        self.websocket_thread = threading.Thread(
            target=self._run_loop_server,
            daemon=True
        )
        self.websocket_thread.start()

def main():
    """主函数 - 用于测试"""
    server = VLAWebSocketServer.get_instance()
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("收到中断信号，正在关闭服务器...")
        server.stop_server()

if __name__ == "__main__":
    main()