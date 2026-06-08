#!/usr/bin/env python3
"""
VLA Action Server - ROS2 Action Server 模式

独立的 ROS2 Action Server 节点，接收外部任务 goal 后创建 VLAClient、
启动推理、监控 prob_progress 并发送 feedback，支持任务取消和错误处理。

使用方式:
    python run_vla_action_server.py
    
与 run_client.py 的区别:
    - run_client.py: 手动触发，用户通过交互命令控制任务流程
    - run_vla_action_server.py: ROS2 action 触发，外部系统（调度器/语音助手）发送 goal
"""

import rclpy
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.node import Node
from message_center.action import ExecutionUnit

import time
import json
import numpy as np
import sys
import os

# 添加项目根目录到 path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)


class VLAActionServer(Node):
    """VLA (Vision-Language-Action) ROS2 Action Server"""
    
    # 配置参数
    THRE_PROGRESS = 0.9          # 完成阈值
    STABLE_COUNT_THRESHOLD = 20  # 连续稳定计数
    STABILITY_RATIO_THRESH = 0.05  # 变异系数阈值
    FEEDBACK_INTERVAL = 1.0 / 3.0  # feedback 频率 (3Hz)
    MAX_TASK_DURATION = 60.0     # 最大任务时长（秒）
    
    def __init__(self):
        super().__init__('vla_action_server')
        
        self.get_logger().info('VLA Action Server starting...')
        
        # 创建 Action Server
        self._action_server = ActionServer(
            self,
            ExecutionUnit,
            'vla_task',
            self.execute_callback,
            cancel_callback=self.cancel_callback
        )
        
        self.get_logger().info('VLA Action Server ready. Waiting for goals...')
    
    def cancel_callback(self, goal_handle):
        """处理取消请求"""
        self.get_logger().warn('Received cancel request for VLA task')
        return CancelResponse.ACCEPT
    
    async def execute_callback(self, goal_handle):
        """执行任务回调函数
        
        流程:
        1. 解析 goal (task_src, params)
        2. 创建 VLAClient + RobotBody 实例
        3. 复位机器人到安全姿态
        4. 设置语言指令并启动推理
        5. 每 0.33s 读取 prob_progress 并发送 feedback
        6. 判断完成条件 (prob_progress > 0.9, 连续稳定 20次)
        7. 返回 result (SUCCESS/FAILED)
        8. finally 块清理所有资源
        """
        
        # ========== 第1步：解析 goal ==========
        goal = goal_handle.get_goal()
        task_src = goal.task_src  # 1=scheduler, 2=scratch
        params_json = goal.params  # JSON 字符串
        
        self.get_logger().info(f'Received task: task_src={task_src}, params={params_json}')
        
        # 解析 params，提取语言指令等关键参数
        try:
            params = json.loads(params_json) if params_json else {}
        except json.JSONDecodeError as e:
            self.get_logger().error(f'Failed to parse params JSON: {e}')
            result = ExecutionUnit.Result()
            result.result = 2  # FAILED
            result.error_code = 1
            result.error_message = f'Invalid params JSON: {str(e)}'
            goal_handle.abort()
            return result
        
        language_instruction = params.get('language', '')
        target_object = params.get('target_object', '')
        
        if not language_instruction:
            self.get_logger().error('Language instruction is empty in params')
            result = ExecutionUnit.Result()
            result.result = 2  # FAILED
            result.error_code = 2
            result.error_message = 'Missing language instruction in params'
            goal_handle.abort()
            return result
        
        self.get_logger().info(f'Language instruction: {language_instruction}')
        
        # ========== 第2步：创建 VLAClient + RobotBody 实例 ==========
        from client.core.vla_client import VLAClientAsync
        from client.core.realtime_data_manager import RealtimeDataManager
        from client.core.trajectory_generator import TrajectoryGenerator
        from client.core.zmq_client import ZMQClient
        from conf.client_conf import get_client_config
        from client.robots.unitree_g1.body_robot import RobotBody
        
        try:
            # 加载配置
            config = get_client_config()
            
            # 初始化各组件
            vla_zmq_client = ZMQClient(config.vla_zmq)
            rdm = RealtimeDataManager(config.rdm)
            traj_generator = TrajectoryGenerator(config=config.traj)
            robot_body = RobotBody(config)
            
            vla_client = VLAClientAsync(
                config=config,
                rdm=rdm,
                traj_generator=traj_generator,
                vla_zmq_client=vla_zmq_client,
                robot=robot_body
            )
            
        except Exception as e:
            self.get_logger().error(f'Failed to create VLAClient: {e}')
            result = ExecutionUnit.Result()
            result.result = 2  # FAILED
            result.error_code = 3
            result.error_message = f'Failed to create VLAClient: {str(e)}'
            goal_handle.abort()
            return result
        
        # ========== 第3步：复位机器人到安全姿态 ==========
        try:
            self.get_logger().info('Resetting robot to safe pose...')
            robot_body.reset_robot(mode='default')
            time.sleep(1.0)
        except Exception as e:
            self.get_logger().error(f'Robot reset failed: {e}')
            vla_client.close()
            robot_body.close()
            vla_zmq_client.close()
            
            result = ExecutionUnit.Result()
            result.result = 2  # FAILED
            result.error_code = 4
            result.error_message = f'Robot reset failed: {str(e)}'
            goal_handle.abort()
            return result
        
        # ========== 第4步：设置语言指令并启动推理 ==========
        try:
            vla_client.language = language_instruction
            vla_client.is_running_action = False  # 先暂停
            
            self.get_logger().info('Starting VLA inference...')
            vla_client.inference_first()
            vla_client.is_running_action = True
            
            # 启动 VLAClient 线程
            vla_client.run()
            
        except Exception as e:
            self.get_logger().error(f'Failed to start VLA inference: {e}')
            vla_client.is_running_action = False
            vla_client.close()
            robot_body.close()
            vla_zmq_client.close()
            
            result = ExecutionUnit.Result()
            result.result = 2  # FAILED
            result.error_code = 5
            result.error_message = f'Failed to start inference: {str(e)}'
            goal_handle.abort()
            return result
        
        # ========== 第5步：监控进度并发送 feedback ==========
        progress_start_time = time.time()
        stable_count = 0
        stability_window = []
        
        try:
            while True:
                # 检查是否应该停止
                if not vla_client.is_running_action:
                    break
                
                # 检查超时
                elapsed_total = time.time() - progress_start_time
                if elapsed_total > self.MAX_TASK_DURATION:
                    self.get_logger().error(f'Task timed out after {elapsed_total:.1f}s')
                    break
                
                # 获取当前状态
                current_prob_progress = vla_client.info_act.get('current_prob_progress', 0.0)
                
                # 计算 elapsed time 和进度百分比
                elapsed = time.time() - progress_start_time
                progress_percent = min(int(current_prob_progress * 100), 99)  # 最大99%
                
                # ========== 构建 feedback message ==========
                # 格式：[progress=XX%][elapsed=Xs] description
                feedback = ExecutionUnit.Feedback()
                feedback.need_process = True
                feedback.feedback_code = 0  # 心跳检测
                feedback.message = f"[progress={progress_percent}%][elapsed={int(elapsed)}s] VLA task in progress - prob_progress={current_prob_progress:.3f}"
                goal_handle.publish_feedback(feedback)
                
                # ========== 检查任务完成条件 ==========
                if current_prob_progress > self.THRE_PROGRESS:
                    stability_window.append(current_prob_progress)
                    
                    # 保持滑动窗口大小
                    if len(stability_window) > 50:
                        stability_window.pop(0)
                    
                    if len(stability_window) >= 3:
                        window_std = np.std(stability_window)
                        window_mean = np.mean(stability_window)
                        stability_ratio = window_std / (window_mean + 1e-6)
                        
                        # 连续稳定计数
                        if stability_ratio < self.STABILITY_RATIO_THRESH:
                            stable_count += 1
                        else:
                            stable_count = 0
                        
                        # 满足稳定性条件 → 任务完成
                        if stable_count >= self.STABLE_COUNT_THRESHOLD:
                            self.get_logger().info(f'Task completed successfully! Total time: {elapsed:.1f}s')
                            
                            # 发送成功结果
                            result = ExecutionUnit.Result()
                            result.result = 1  # SUCCESS
                            result.error_code = 0
                            result.error_message = ''
                            goal_handle.succeed(result)
                            return result
                else:
                    stable_count = 0
                    stability_window.clear()
                
                # 休眠约 0.33s (3Hz 频率)
                time.sleep(self.FEEDBACK_INTERVAL)
        
        except Exception as e:
            self.get_logger().error(f'Error during task execution: {e}')
        
        finally:
            # ========== 始终清理资源 ==========
            try:
                vla_client.is_running_action = False
                time.sleep(0.1)
                robot_body.reset_robot(mode='default')
                time.sleep(0.5)
                vla_client.close()
                robot_body.close()
                vla_zmq_client.close()
            except Exception as cleanup_e:
                self.get_logger().error(f'Cleanup error: {cleanup_e}')
        
        # 检查是否是取消请求
        if goal_handle.is_cancel_requested:
            self.get_logger().info('Task was cancelled by client')
            result = ExecutionUnit.Result()
            result.result = 2  # FAILED
            result.error_code = 3  # 自定义错误码（任务被取消）
            result.error_message = 'Task cancelled by user'
            goal_handle.abort()
            return result
        
        # 其他失败情况
        self.get_logger().error(f'Task failed after {elapsed_total:.1f}s')
        result = ExecutionUnit.Result()
        result.result = 2  # FAILED
        result.error_code = 99  # 通用错误码
        result.error_message = f'Task failed: {str(e)}'
        goal_handle.abort()
        return result


def main(args=None):
    rclpy.init(args=args)
    
    try:
        action_server = VLAActionServer()
        rclpy.spin(action_server)
    except KeyboardInterrupt:
        print("\nShutting down VLA Action Server...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'action_server' in locals():
            action_server.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
