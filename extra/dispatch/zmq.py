#!/usr/bin/env python3

import zmq
import json
import threading
import time
import logging
from enum import Enum
from typing import Callable, Optional, Dict, Any
import uuid
import socket

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DispatchZMQClient")

class RobotState(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    RECONNECTING = 3

class DispatchZMQClient:
    def __init__(self, robot_type: str, 
                 server_task_address: str, 
                 server_response_address: str,
                 heartbeat_interval: float = 5.0,
                 reconnect_interval: float = 3.0,
                 receive_timeout: float = 30.0):  # 改为接收超时时间
        """
        机器人 ZeroMQ 客户端
        
        Args:
            robot_type: 机器人类型标识
            server_task_address: 服务器任务地址 (tcp://host:port)
            server_response_address: 服务器响应地址 (tcp://host:port)
            heartbeat_interval: 心跳发送间隔(秒)
            reconnect_interval: 重连间隔(秒)
            receive_timeout: 接收消息超时时间(秒)
        """
        self.robot_type = robot_type
        self.server_task_address = server_task_address
        self.server_response_address = server_response_address
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_interval = reconnect_interval
        self.receive_timeout = receive_timeout  # 接收消息超时时间
        
        # ZeroMQ 上下文和套接字
        self.context = None
        self.task_socket = None
        self.response_socket = None
        self.poller = None
        
        # 状态管理
        self.state = RobotState.DISCONNECTED
        self.identity = f"{robot_type}_{uuid.uuid4().hex[:8]}"
        self.is_running = False
        self.processing_task = False  # 任务处理标志
        
        # 连接健康度监测 - 基于接收消息的时间
        self.last_received_message = time.time()
        
        # 回调函数
        self.task_handler = None
        self.connection_handler = None
        
        # 线程和锁
        self.state_lock = threading.RLock()
        self.socket_lock = threading.Lock()  # 套接字访问锁
        self.processing_lock = threading.Lock() # 任务处理锁
        self.listen_thread = None
        self.heartbeat_thread = None
        self.reconnect_thread = None
        
        logger.info(f"Robot ZMQ client initialized for {robot_type}")
        logger.info(f"Client identity: {self.identity}")
        logger.info(f"Task address: {server_task_address}")
        logger.info(f"Response address: {server_response_address}")

    def _get_current_state(self) -> RobotState:
        """使用读锁获取当前状态"""
        with self.state_lock:
            return self.state

    def set_task_handler(self, handler: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]):
        """设置任务处理回调"""
        self.task_handler = handler
        logger.info("Task handler set")

    def set_connection_handler(self, handler: Callable[[bool], None]):
        """设置连接状态回调"""
        self.connection_handler = handler
        logger.info("Connection handler set")

    def _update_state(self, new_state: RobotState):
        """更新连接状态"""
        with self.state_lock:
            if self.state != new_state:
                old_state = self.state
                self.state = new_state
                logger.info(f"State changed: {old_state.name} -> {new_state.name}")
                
                # 调用连接状态回调
                if self.connection_handler:
                    try:
                        self.connection_handler(new_state == RobotState.CONNECTED)
                    except Exception as e:
                        logger.error(f"Connection handler error: {e}")

    def _can_connect_to_address(self, address: str) -> bool:
        """检查是否可以连接到指定地址"""
        try:
            # 解析地址
            if address.startswith('tcp://'):
                parts = address[6:].split(':')
                if len(parts) == 2:
                    host, port = parts
                    logger.info(f"Testing connection to {host}:{port}")
                    # 尝试建立TCP连接
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2.0)  # 2秒超时
                    result = sock.connect_ex((host, int(port)))
                    sock.close()
                    if result == 0:
                        logger.info(f"Address {address} is reachable")
                        return True
                    else:
                        logger.warning(f"Address {address} is not reachable (error: {result})")
                        return False
        except Exception as e:
            logger.error(f"Address validation failed for {address}: {e}")
        return False

    def _setup_sockets(self) -> bool:
        """设置 ZeroMQ 套接字 (与C++服务器匹配)"""
        try:
            logger.info("Setting up ZeroMQ sockets...")
            # 创建上下文
            self.context = zmq.Context()
            
            # 创建任务套接字 (DEALER) - 用于接收任务
            self.task_socket = self.context.socket(zmq.DEALER)
            self.task_socket.setsockopt_string(zmq.IDENTITY, self.identity)
            self.task_socket.setsockopt(zmq.LINGER, 0)
            self.task_socket.setsockopt(zmq.RECONNECT_IVL, 1000)
            self.task_socket.setsockopt(zmq.RECONNECT_IVL_MAX, 5000)
            
            # 创建响应套接字 (DEALER) - 用于发送响应
            self.response_socket = self.context.socket(zmq.DEALER)
            self.response_socket.setsockopt_string(zmq.IDENTITY, self.identity)
            self.response_socket.setsockopt(zmq.LINGER, 0)
            self.response_socket.setsockopt(zmq.RECONNECT_IVL, 1000)
            self.response_socket.setsockopt(zmq.RECONNECT_IVL_MAX, 5000)
            
            # 设置轮询器
            self.poller = zmq.Poller()
            self.poller.register(self.task_socket, zmq.POLLIN)
            
            logger.info("ZeroMQ sockets setup completed")
            return True
            
        except zmq.ZMQError as e:
            logger.error(f"Failed to setup sockets: {e}")
            self._cleanup_sockets()
            return False

    def _connect_sockets(self) -> bool:
        """连接服务器套接字，添加连接验证"""
        try:
            logger.info("Connecting sockets to server...")
            # 先验证地址可达性
            if not self._can_connect_to_address(self.server_task_address):
                logger.error(f"Cannot connect to task address: {self.server_task_address}")
                return False
                
            if not self._can_connect_to_address(self.server_response_address):
                logger.error(f"Cannot connect to response address: {self.server_response_address}")
                return False
            
            logger.info(f"Connecting to server: {self.server_task_address}, {self.server_response_address}")
            
            self.task_socket.connect(self.server_task_address)
            self.response_socket.connect(self.server_response_address)

            logger.info(f"Task socket connected: {self.server_task_address}")
            logger.info(f"Response socket connected: {self.server_response_address}")

            # 添加连接验证：发送初始握手消息
            handshake_msg = {
                "version": "1.0",
                "type": "handshake",
                "robot_type": self.robot_type,
                "source": "robot",
                "timestamp": time.time()
            }
            # 尝试发送握手消息
            if not self._send_message(self.response_socket, handshake_msg):
                logger.warning("Handshake failed - cannot send message")
                return False
            logger.info("Sockets connected successfully (handshake sent)")
            return True
            
        except (zmq.ZMQError, socket.error) as e:
            logger.error(f"Failed to connect sockets: {e}")
            return False

    def _cleanup_sockets(self):
        """清理套接字资源"""
        try:
            logger.info("Cleaning up sockets...")
            # 先取消轮询器注册
            if hasattr(self, 'poller') and self.poller and self.task_socket:
                try:
                    self.poller.unregister(self.task_socket)
                    logger.info("Unregistered task socket from poller")
                except:
                    logger.warning("Failed to unregister task socket from poller")
                    pass
            
            # 关闭套接字
            if self.task_socket:
                try:
                    self.task_socket.close()
                    logger.info("Task socket closed")
                except:
                    logger.warning("Failed to close task socket")
                    pass
                self.task_socket = None
                
            if self.response_socket:
                try:
                    self.response_socket.close()
                    logger.info("Response socket closed")
                except:
                    logger.warning("Failed to close response socket")
                    pass
                self.response_socket = None
                
            # 终止上下文
            if self.context:
                try:
                    self.context.term()
                    logger.info("ZMQ context terminated")
                except:
                    logger.warning("Failed to terminate ZMQ context")
                    pass
                self.context = None
                
            self.poller = None
            logger.info("Socket cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up sockets: {e}")

    def _send_message(self, socket: zmq.Socket, data: Dict[str, Any]) -> bool:
        """发送消息到服务器 (与C++格式匹配)"""
        with self.socket_lock:
            if socket is None:
                logger.warning("Cannot send message - socket is None")
                return False
                
            try:
                message_str = json.dumps(data)
                # 发送三帧消息: [identity, delimiter, content]
                # socket.send(self.identity.encode('utf-8'), zmq.SNDMORE)   # 身份帧会默认发送，这里一定要注释掉，否则会发送四帧
                socket.send(b"", zmq.SNDMORE)
                socket.send(message_str.encode('utf-8'))

                logger.debug(f"SENT -> {message_str}")
                return True

            except zmq.ZMQError as e:
                if e.errno == zmq.EHOSTUNREACH:
                    logger.warning(f"Send failed: target unreachable - {e}")
                else:
                    logger.error(f"Failed to send message: {e}")
                return False
            except json.JSONEncodeError as e:
                logger.error(f"JSON encode error: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error in send: {e}")
                return False

    def _receive_message(self, socket: zmq.Socket, timeout: int = 100) -> Optional[Dict[str, Any]]:
        """接收消息 (使用轮询避免阻塞)"""
        with self.socket_lock:
            if socket is None or self.poller is None:
                return None
            try:
                # 检查是否有可读消息
                socks = dict(self.poller.poll(timeout))
                if socket not in socks:
                    return None
                
                # 接收多帧消息
                frames = []
                more = True
                while more:
                    try:
                        frame = socket.recv(zmq.NOBLOCK if not frames else 0)
                        frames.append(frame)
                        
                        # 检查是否还有更多帧
                        more = socket.getsockopt(zmq.RCVMORE)
                    except zmq.Again:
                        break
                
                # 调试信息：打印接收到的帧
                logger.debug(f"Received {len(frames)} frames")
                for i, frame in enumerate(frames):
                    if len(frame) == 0:
                        logger.debug(f"Frame {i}: [empty delimiter] (0 bytes)")
                    else:
                        try:
                            frame_content = frame.decode('utf-8')
                            logger.debug(f"Frame {i}: '{frame_content}' ({len(frame)} bytes)")
                        except UnicodeDecodeError:
                            logger.debug(f"Frame {i}: [binary data] ({len(frame)} bytes)")
                
                # 解析消息帧 - DEALER 套接字的特殊处理
                # 服务器发送: [identity, delimiter, content]
                # DEALER 接收: [delimiter, content] (身份帧被ZeroMQ自动处理)
                
                if len(frames) == 2:
                    # 标准 DEALER 接收格式: [delimiter, content]
                    # 第一帧是空分隔符，第二帧是内容
                    if len(frames[0]) == 0:  # 检查是否是空分隔符
                        try:
                            message_str = frames[1].decode('utf-8')
                            logger.debug(f"RECEIVED <- {message_str}")
                            # 更新最后接收消息时间
                            self.last_received_message = time.time()
                            return json.loads(message_str)
                        except (UnicodeDecodeError, json.JSONDecodeError) as e:
                            logger.error(f"Failed to decode message: {e}")
                            return None
                    else:
                        logger.warning("Unexpected frame format: first frame is not empty delimiter")
                        return None
                        
                elif len(frames) == 1:
                    # 单帧消息（可能是其他模式或简化格式）
                    try:
                        message_str = frames[0].decode('utf-8')
                        logger.debug(f"RECEIVED <- {message_str}")
                        # 更新最后接收消息时间
                        self.last_received_message = time.time()
                        return json.loads(message_str)
                    except (UnicodeDecodeError, json.JSONDecodeError) as e:
                        logger.error(f"Failed to decode single frame message: {e}")
                        return None
                        
                elif len(frames) >= 3:
                    # 如果收到3帧，可能是其他情况，尝试解析最后一帧
                    try:
                        message_str = frames[-1].decode('utf-8')
                        logger.debug(f"RECEIVED <- {message_str}")
                        logger.warning(f"Unexpected {len(frames)} frames received, using last frame")
                        # 更新最后接收消息时间
                        self.last_received_message = time.time()
                        return json.loads(message_str)
                    except (UnicodeDecodeError, json.JSONDecodeError) as e:
                        logger.error(f"Failed to decode message from multiple frames: {e}")
                        return None
                        
                else:
                    logger.warning(f"Unexpected frame count: {len(frames)}")
                    return None
                    
            except (zmq.ZMQError, json.JSONDecodeError) as e:
                logger.error(f"Failed to receive message: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in receive message: {e}")
                return None

    def start(self):
        """启动客户端"""
        if self.is_running:
            logger.warning("Client is already running")
            return
            
        self.is_running = True
        
        # 启动监听线程
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        # 启动重连线程
        self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self.reconnect_thread.start()
        
        logger.info("Robot ZMQ client started with all threads")

    def stop(self):
        """停止客户端"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        logger.info("Stopping client...")
        # 先清理套接字，这会中断所有阻塞的socket操作
        with self.socket_lock:
            self._cleanup_sockets()
        
        # 等待线程结束
        threads = [
            self.listen_thread, 
            self.heartbeat_thread, 
            self.reconnect_thread
        ]
        
        for thread in threads:
            if thread and thread.is_alive():
                logger.info(f"Waiting for {thread.name} to finish...")
                thread.join(timeout=2.0)
        
        self._update_state(RobotState.DISCONNECTED)
        
        logger.info("Robot ZMQ client stopped")

    def _listen_loop(self):
        """监听循环 - 接收服务器消息"""
        logger.info("Listen loop started")
        while self.is_running:
            try:
                # 检查状态
                current_state = self._get_current_state()
                if current_state != RobotState.CONNECTED:
                    logger.debug(f"Not connected, current state: {current_state.name}")
                    time.sleep(0.5)
                    continue
                
                # 接收消息
                message = self._receive_message(self.task_socket, 100)
                if message:
                    # 处理消息
                    self._handle_message(message)
                else:
                    time.sleep(0.01)  # 10ms休眠

            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                time.sleep(0.1)

    def _handle_message(self, message: Dict[str, Any]):
        """处理接收到的消息 (与C++服务器消息格式匹配)"""
        try:
            msg_type = message.get("type", "")
            task_id = message.get("task_id", "")
            source = message.get("source", "")
            
            logger.debug(f"Receive message - type: {msg_type}, task_id: {task_id}, source: {source}")
            
            if msg_type == "heartbeat_ack":
                # 心跳响应
                logger.debug("Heartbeat acknowledged")
                
            elif msg_type == "task" and source == "service":
                logger.info(f"Receive message - type: {msg_type}, task_id: {task_id}, source: {source}")
                with self.processing_lock:
                    if self.processing_task:
                        logger.warning("Already processing a task, skipping this one")
                        return
                # 处理任务
                task_thread = threading.Thread(
                    target=self._handle_task,
                    args=(message,),
                    daemon=True,
                    name=f"TaskHandler-{task_id}"
                )
                task_thread.start()
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _handle_task(self, task_data: Dict[str, Any]):
        """处理任务 (与C++服务器任务格式匹配)"""
        try:
            with self.processing_lock:
                self.processing_task = True

            task_id = task_data.get("task_id")
            action = task_data.get("action", "")
            item = task_data.get("item", "")
            
            logger.debug(f"Received task: id={task_id}, action={action}, item={item}")

            # 创建默认响应
            response = {}
            # 添加必要的元数据 (与C++服务器格式匹配)
            response.update({
                "version": "1.0",
                "type": "response",
                "robot_type": self.robot_type,
                "task_id": task_id,
                "source": "robot",
                "message": "Receive task successfully"
            })
            
            # 发送响应
            self.send_response(response)

            # 调用任务处理回调
            response = None
            if self.task_handler:
                try:
                    self.task_handler(task_data)
                except Exception as e:
                    logger.error(f"Task handler error: {e}")
            else:
                logger.warning("No task handler registered")

            with self.processing_lock:
                self.processing_task = False
            status = "completed"
            # self.send_status_update(task_id, status)
            logger.info("Processing task flag cleared")

        except Exception as e:
            logger.error(f"Error processing task: {e}")
            
            # 发送错误状态
            error_response = {
                "version": "1.0",
                "type": "error",
                "timestamp": time.time(),
                "robot_type": self.robot_type,
                "task_id": task_data.get("task_id", "unknown"),
                "source": "robot",
                "error_level": "E102",
                "error_message": str(e),
                "recoverable": True,
                "retry_suggested": "Resend"
            }
            self.send_response(error_response)

    def _heartbeat_loop(self):
        """心跳循环，只发送不等待响应"""
        logger.info("Heartbeat loop started")
        while self.is_running:
            try:
                current_state = self._get_current_state()
                if current_state != RobotState.CONNECTED:
                    time.sleep(self.heartbeat_interval)
                    continue
                
                # 发送单向心跳（不期待响应）
                heartbeat = {
                    "version": "1.0",
                    "type": "heartbeat",
                    "robot_type": self.robot_type,
                    "source": "robot",
                    "timestamp": time.time()
                }
                
                # 发送心跳但不检查响应
                self._send_message(self.response_socket, heartbeat)
                logger.debug("Heartbeat sent (one-way)")
                
                time.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(1.0)

    def _reconnect_loop(self):
        """重连循环 - 基于接收消息超时触发重连"""
        logger.info("Reconnect loop started")
        reconnect_attempts = 0
        max_reconnect_attempts = 30

        while self.is_running:
            try:
                current_state = self._get_current_state()

                if current_state == RobotState.DISCONNECTED:
                    logger.info("Initial connection attempt...")
                    self._update_state(RobotState.RECONNECTING)
                    continue  # 立即进入下一次循环处理 RECONNECTING 状态

                # 检查是否需要重连：长时间未收到任何消息
                if current_state == RobotState.CONNECTED:
                    # 如果正在处理任务，跳过重连检查

                    if self.processing_task:
                        logger.debug("Skipping reconnect check - task in progress")
                        self.last_received_message = time.time()
                        time.sleep(1.0)
                        continue

                    current_time = time.time()
                    time_since_last_received = current_time - self.last_received_message
                    
                    if time_since_last_received > self.receive_timeout:
                        logger.warning(f"No messages received for {time_since_last_received:.1f}s, triggering reconnect")
                        self._update_state(RobotState.RECONNECTING)
                
                # 处理重连状态
                if current_state == RobotState.RECONNECTING:
                    reconnect_attempts += 1

                    # 清理和重新连接
                    with self.socket_lock:
                        self._cleanup_sockets()
                        
                    # 设置和连接套接字（不在锁内，避免死锁）
                    setup_success = self._setup_sockets()
                    connect_success = False
                    if setup_success:
                        connect_success = self._connect_sockets()

                    # 更新状态
                    if setup_success and connect_success:
                        self._update_state(RobotState.CONNECTED)
                        reconnect_attempts = 0
                        # 重置最后接收消息时间
                        self.last_received_message = time.time()
                        logger.info("Reconnected to server successfully")
                    else:
                        if reconnect_attempts >= max_reconnect_attempts:
                            logger.error("Max reconnection attempts reached, giving up")
                            self._update_state(RobotState.DISCONNECTED)
                        else:
                            wait_time = self.reconnect_interval * (reconnect_attempts + 1)
                            logger.warning(f"Reconnection failed (attempt {reconnect_attempts}), retrying in {wait_time}s")
                            time.sleep(wait_time)
                            continue
                
                # 正常状态检查
                time.sleep(1.0)
                    
            except Exception as e:
                logger.error(f"Error in reconnect loop: {e}")
                time.sleep(self.reconnect_interval)

    def send_response(self, response_data: Dict[str, Any]) -> bool:
        """发送响应到服务器"""
        with self.state_lock:
            if self.state != RobotState.CONNECTED:
                logger.warning("Cannot send response - not connected")
                return False
                
        return self._send_message(self.response_socket, response_data)

    def send_status_update(self, task_id: str, status: str) -> bool:
        """发送状态更新 (与C++服务器格式匹配)"""
        status_data = {
            "version": "1.0",
            "type": "status",
            "robot_type": self.robot_type,
            "task_id": task_id,
            "source": "robot",
            "status": status
        }
        
        return self.send_response(status_data)

    def send_error(self, task_id: str, error_level: str, error_message: str, retry_suggested: str, 
                   recoverable : bool = True) -> bool:
        """发送错误信息 (与C++服务器格式匹配)"""
        error_data = {
            "version": "1.0",
            "type": "error",
            "timestamp": time.time(),
            "robot_type": self.robot_type,
            "task_id": task_id,
            "source": "robot",
            "error_level": error_level,
            "error_message": error_message,
            "recoverable": recoverable,
            "retry_suggested": retry_suggested
        }
        
        return self.send_response(error_data)