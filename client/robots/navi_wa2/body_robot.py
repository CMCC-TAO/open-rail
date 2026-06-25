import time
import cv2
import logging
import threading
import numpy as np
from ..base_robot import RobotBase
import pandas as pd
import rospy
from collections import deque
from sensor_msgs.msg import JointState
from sensor_msgs.msg import Image,CompressedImage
from cv_bridge import CvBridge, CvBridgeError
from upperlimb.srv import Servo, ServoRequest,MoveJ,MoveJRequest,MoveJResponse
from upperlimb.msg import Joints
from zj_robot.msg import Resource, Errors
from hand.srv import HandJoint, HandJointRequest

_ROS_INIT_LOCK = threading.Lock()


def _ensure_rospy_node():
    with _ROS_INIT_LOCK:
        if rospy.core.is_initialized():
            return
        rospy.init_node('vla_rail_navi_wa2', anonymous=True, disable_signals=True)


class RobotBody(RobotBase):
    def __init__(self, config):
        """Initialize the wa2 robot body
        
        Args:
            config (dict): Configuration dictionary containing wa2 robot settings
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.cfg, self.ori_cfg = config["robots"]['navi_wa2'], config
        default_action_layout = {
            'arm': {'start': 0, 'end': 16, 'policy': 'gradual'},
            'hand': {'start': 16, 'end': 28, 'policy': 'stepwise'},
            'neck': {'start': 28, 'end': 30, 'policy': 'gradual'},
            'waist': {'start': 30, 'end': 34, 'policy': 'gradual'},
        }
        self.action_layout = dict(self.cfg.get('action_layout', default_action_layout))
        self.current_state = np.zeros(8*2+6*2)
        # 总开关
        self._stop = False

        service_name_servo = '/zj_humanoid/upperlimb/set_servo_params'
        service_name_hand = '/zj_humanoid/hand/joint_switch/dual'
        _ensure_rospy_node()
        rospy.wait_for_service(service_name_servo, timeout=10.0)
        rospy.wait_for_service(service_name_hand, timeout=10.0)

        # 创建订阅者，订阅 /joint_states 话题
        self.subscriber = rospy.Subscriber(
            '/zj_humanoid/upperlimb/joint_states',      # 话题名称
            JointState,           # 消息类型
            self.joint_states_callback,  # 回调函数
            queue_size=5 #10         # 队列大小
        )
        self.subscriber_hand = rospy.Subscriber(
            '/zj_humanoid/hand/joint_states',      # 话题名称
            JointState,           # 消息类型
            self.joint_states_callback_hand,  # 回调函数
            queue_size=5 #10         # 队列大小
        )        
        # 手臂控制器
        rospy.ServiceProxy(service_name_servo, Servo).call(ServoRequest(time=self.cfg['tt'], gain=self.cfg['gain'])) 
        self.servoj = rospy.Publisher('/zj_humanoid/upperlimb/servoj/dual_arm', Joints, queue_size=1)
        # 手指控制器
        self.hand_controller = rospy.ServiceProxy(service_name_hand, HandJoint)
        self.hand_request_ready = False
        self.hand_request = HandJointRequest()
        self.hand_thread = threading.Thread(
                target=self.hand_request_func,
                name="navi_wa2_hand_request_func",
                daemon=True  # 设为守护线程，主线程结束时自动终止
            )
        self.hand_thread.start()
        # 相机接收器
        self.bridge = CvBridge()
        camera_topics = dict(getattr(self.cfg.camera, 'topic_dict', {}))
        self.camera_topic_substribers = {came_name:None for came_name in camera_topics}
        self.camera_image_queue = {came_name:None for came_name in camera_topics}
        for cam_name, cam_topic in camera_topics.items():
            if not cam_topic:
                self.logger.warning(f"Skip empty camera topic for {cam_name}")
                continue
            self.camera_topic_substribers[cam_name] = rospy.Subscriber(
                cam_topic,  # 话题名称
                CompressedImage,                                    # 消息类型
                self.camera_image_callback,                      # 回调函数
                callback_args=cam_name,  # 通过callback_args传递标识
                queue_size=1                              # 队列大小（实时性优先）
            )
        # 手部及腰部movej控制器
        self.waist_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/waist', MoveJ)
        self.left_arm_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/left_arm', MoveJ)
        self.right_arm_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/right_arm', MoveJ)
        self.neck_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/neck', MoveJ)
        self.dual_arm_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/dual_arm', MoveJ)
        self.waist_head_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/whole_body', MoveJ)
        time.sleep(0.5)

        # --- 离散手势滤波配置 ---
        # 选项: 'mode' (滑动窗口众数滤波), 'debounce' (状态确认延迟), 'none' (无滤波)
        self.hand_filter_type = 'none' 

        # 1. 众数滤波 (Mode Filter) 参数
        self.mode_window_size = 10
        self.left_history = deque(maxlen=self.mode_window_size)
        self.right_history = deque(maxlen=self.mode_window_size)

        # 2. 去抖动 (Debouncing) 参数
        self.debounce_k_frames = 4  # 新状态必须连续出现K帧才生效
        self.left_candidate_idx = 0
        self.left_candidate_count = 0
        self.right_candidate_idx = 0
        self.right_candidate_count = 0

        # 当前实际生效的离散手势索引
        self.current_left_idx = 0
        self.current_right_idx = 0

        pose_open = np.array([-0.6, 0.9, 0.0, 0.0, 0.0, 0.0])
        pose_close = np.array([-0.2, 0.9, 0.0, 1.0, 1.0, 1.0])
        pose_half = np.array([-0.2, 0.9, 0.4, 0.4, 0.4, 0.4])
        self.hand_poses = [pose_open, pose_close, pose_half]



    def camera_image_callback(self, msg, cam_name):
        try:
            cv_image = self.bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")
            self.camera_image_queue[cam_name] = cv_image
            return
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge转换错误: {e}")
        print('X'*100)
        return

    def joint_states_callback(self, msg):
        """
        回调函数：处理接收到的 JointState 消息
        """
        self.current_state[:16] = msg.position[:16]
        return
    
    def joint_states_callback_hand(self, msg):
        """
        回调函数：处理接收到的 JointState 消息
        """
        self.current_state[16:] = msg.position[:]
        return

    def _apply_kalman(self, measurement, state_x, state_p):
        """执行简易一维多路卡尔曼滤波"""
        if state_x is None:
            return measurement, np.ones_like(measurement) # 初始化第一帧

        # 1. 预测阶段 (Prediction)
        pred_x = state_x
        pred_p = state_p + self.kf_q
        
        # 2. 更新阶段 (Update)
        k_gain = pred_p / (pred_p + self.kf_r)            # 计算卡尔曼增益
        new_x = pred_x + k_gain * (measurement - pred_x)  # 更新状态估计
        new_p = (1 - k_gain) * pred_p                     # 更新协方差

        return new_x, new_p
    
    def control_robot(self, action):
        """Control the robot arm and gripper based on the given action.
        
        Args:
            action (array-like): Action array containing arm commands (0:14) and gripper commands (14:16)
        """
        # 提取原始手部指令
        left_hand_action = np.array(action[16:22])
        right_hand_action = np.array(action[22:28])

        # ==========================================
        # 2. 离散手势映射层 (Discrete Gesture Mapping)
        # ==========================================
        

        # 获取当前网络原始预测的最匹配手势索引
        raw_left_idx = np.argmin([np.linalg.norm(left_hand_action - p) for p in self.hand_poses])
        raw_right_idx = np.argmin([np.linalg.norm(right_hand_action - p) for p in self.hand_poses])

        # ==========================================
        # 3. 离散切换滤波层 (Discrete Filtering)
        # ==========================================
        if self.hand_filter_type == 'mode':
            # --- 策略 A: 滑动窗口众数滤波 ---
            self.left_history.append(raw_left_idx)
            self.right_history.append(raw_right_idx)

            # 统计窗口内出现次数最多的状态
            self.current_left_idx = max(set(self.left_history), key=self.left_history.count)
            self.current_right_idx = max(set(self.right_history), key=self.right_history.count)

        elif self.hand_filter_type == 'debounce':
            # --- 策略 B: 状态确认延迟 (去抖动) - 修正版 ---
            
            # ====== 左手逻辑 ======
            if raw_left_idx != self.current_left_idx:
                # 只有当网络预测出了一个“新”状态时，才开始/继续累加
                if raw_left_idx == self.left_candidate_idx:
                    self.left_candidate_count += 1
                else:
                    self.left_candidate_idx = raw_left_idx
                    self.left_candidate_count = 1
                    
                # 连续出现次数达到阈值，执行切换
                if self.left_candidate_count >= self.debounce_k_frames:
                    self.current_left_idx = self.left_candidate_idx
                    self.left_candidate_count = 0  # 切换成功，计数器归零
            else:
                # 预测状态与当前生效状态一致（说明没有跳变，或者跳变只是闪了一下就恢复了）
                self.left_candidate_count = 0  # 计数器清零
                self.left_candidate_idx = raw_left_idx

            # ====== 右手逻辑 ======
            if raw_right_idx != self.current_right_idx:
                if raw_right_idx == self.right_candidate_idx:
                    self.right_candidate_count += 1
                else:
                    self.right_candidate_idx = raw_right_idx
                    self.right_candidate_count = 1
                    
                if self.right_candidate_count >= self.debounce_k_frames:
                    self.current_right_idx = self.right_candidate_idx
                    self.right_candidate_count = 0  # 切换成功，计数器归零
            else:
                self.right_candidate_count = 0
                self.right_candidate_idx = raw_right_idx

        else:
            # --- 策略 C: 无滤波，直接跟随 ---
            self.current_left_idx = raw_left_idx
            self.current_right_idx = raw_right_idx

        # ==========================================
        # 4. 指令组合与下发
        # ==========================================
        target_left = self.hand_poses[self.current_left_idx]
        target_right = self.hand_poses[self.current_right_idx]
        
        target_hand_action = np.concatenate([target_left, target_right])

        # 执行动作
        self.execute_action({'arm': action[:16].tolist()})
        self.execute_action({'hand': target_hand_action})
        
        return
    
    def hand_request_func(self):
        while not self._stop:
            if self.hand_request_ready:
                self.hand_controller(self.hand_request)
                self.hand_request_ready = False
            time.sleep(self.cfg['tt'])
    
    def execute_action(self, data,t=10):
        """Execute the given action on the wa2 robot.
        
        Args:
            action (dict): Dictionary containing action commands for robot joints and gripper
        """
        if 'head' in data and 'neck' not in data:
            data['neck'] = data['head']

        if 'arm' in data:
            self.servoj.publish(Joints(data['arm']))
        if 'hand' in data:
            self.hand_request.q = np.asarray(data['hand'], dtype=float).ravel().tolist()
            self.hand_request_ready = True
        if 'waist' in data:
            request=MoveJRequest()
            joints = np.asarray(data['waist'], dtype=float).ravel()
            print(joints.shape)
            request.joints=joints.tolist()
            request.v=0.8
            request.acc=0.4
            request.is_async=False
            resp: MoveJResponse = self.waist_movej_controller.call(request)
            print(f"Service Name:/zj_humanoid/upperlimb/movej/waist | Resp Success:{resp.success}, Resp Message:{resp.message}")
        if 'left_arm' in data:
            request=MoveJRequest()
            request.joints=np.asarray(data['left_arm'], dtype=float).ravel().tolist()
            request.v=0.1
            request.acc=0.05
            request.t=t
            request.is_async=False
            resp: MoveJResponse = self.left_arm_movej_controller.call(request)
            print(f"Service Name:/zj_humanoid/upperlimb/movej/left_arm | Resp Success:{resp.success}, Resp Message:{resp.message}")
        if 'right_arm' in data:
            request=MoveJRequest()
            request.joints=np.asarray(data['right_arm'], dtype=float).ravel().tolist()
            request.v=0.1
            request.acc=0.05
            request.t=t
            request.is_async=False
            resp: MoveJResponse = self.right_arm_movej_controller.call(request)
            print(f"Service Name:/zj_humanoid/upperlimb/movej/right_arm | Resp Success:{resp.success}, Resp Message:{resp.message}")
        if 'neck' in data:
            request=MoveJRequest()
            request.joints=np.asarray(data['neck'], dtype=float).ravel().tolist()
            request.v=0.4
            request.acc=0.15
            request.is_async=False
            resp: MoveJResponse = self.neck_movej_controller.call(request)
            print(f"Service Name:/zj_humanoid/upperlimb/movej/neck | Resp Success:{resp.success}, Resp Message:{resp.message}")
        if 'waist_head' in data:
            request=MoveJRequest()
            request.joints=np.asarray(data['waist_head'], dtype=float).ravel().tolist()
            request.arm_type = 12
            request.v=1.5 # 2
            request.acc=1.0 #1.5
            request.is_async=False
            resp: MoveJResponse = self.waist_head_movej_controller.call(request)
            print(f"Service Name:/zj_humanoid/upperlimb/movej/waist_head | Resp Success:{resp.success}, Resp Message:{resp.message}")
        return

    def reset_robot(self, target_pose=None, mode='zero'):
        """Reset the robot to its default position.
        """
        target_pose = np.asarray(self.cfg['reset_position'] if target_pose is None else target_pose, dtype=float)
        
        # 获取输入向量的实际长度
        pose_len = len(target_pose)
        segments = {}
        print("reset robot")
        for name, v in self.action_layout.items():
            start = v['start']
            # 如果 start 已经超出了当前 target_pose 的长度，则跳过该部分
            if start >= pose_len:
                continue
            
            # 确保 end 不会超过实际长度 (min 函数防止越界)
            end = min(v['end'], pose_len)
            segments[name] = target_pose[start:end]
        print(segments)
        if mode == "dispatch":
            if "waist" in segments:
                current_arm_position=self.retrieve_observation()['obs.state'][0:16]
                default_arm_pose=np.array([0.182591655739083, 0.32575521044236666, 0.639202615644364, 0.03292066673111549, -1.9789475037079458, 0.5495126798768879, -0.1635420177877668, -0.5]+[ -0.21499700078493333, 0.1528587929215064, -0.718166681663206, 0.12983709623767936, -1.6508818544817816, -0.38494056388590252, -0.8677823346142831, 0.5])
                trajs = self.ruckig_planning(current_arm_position, default_arm_pose,dof=16)
                for i, traj in enumerate(trajs):
                    # print(f"Executing trajectory point {i}: {traj}")
                    self.execute_action({'arm': traj})
                    time.sleep(0.01)
                
                self.execute_action({'waist_head': np.concatenate([segments['neck'],segments['waist']])},t=5)
                time.sleep(0.5)
                
            if "arm" in segments:
                current_arm_position=self.retrieve_observation()['obs.state'][0:16]
                target_arm_position = np.array(segments['arm'])
                # print(f"cur_pos:{current_arm_position}")
                trajs = self.ruckig_planning(current_arm_position, target_arm_position,dof=16)
                for i, traj in enumerate(trajs):
                    # print(f"Executing trajectory point {i}: {traj}")
                    self.execute_action({'arm': traj})
                    time.sleep(0.01)
                self.execute_action({'hand':np.array(segments['hand'])})

                # # 注释
                raw_left_idx = np.argmin([np.linalg.norm(segments['hand'][0:6] - p) for p in self.hand_poses])
                raw_right_idx = np.argmin([np.linalg.norm(segments['hand'][6:12] - p) for p in self.hand_poses])
                self.left_history = deque([raw_left_idx] * self.mode_window_size,maxlen=self.mode_window_size)
                self.right_history=deque([raw_right_idx] * self.mode_window_size,maxlen=self.mode_window_size)
                time.sleep(0.5)
            
        else:
            if "arm" in segments:
                current_arm_position=self.retrieve_observation()['obs.state'][0:16]
                target_arm_position = np.array(segments['arm'])
                # print(f"cur_pos:{current_arm_position}")
                trajs = self.ruckig_planning(current_arm_position, target_arm_position,dof=16)
                for i, traj in enumerate(trajs):
                    # print(f"Executing trajectory point {i}: {traj}")
                    self.execute_action({'arm': traj})
                    time.sleep(0.02)
                self.execute_action({'hand':np.array(segments['hand'])})
                # # 注释
                raw_left_idx = np.argmin([np.linalg.norm(segments['hand'][0:6] - p) for p in self.hand_poses])
                raw_right_idx = np.argmin([np.linalg.norm(segments['hand'][6:12] - p) for p in self.hand_poses])
                self.left_history = deque([raw_left_idx] * self.mode_window_size,maxlen=self.mode_window_size)
                self.right_history=deque([raw_right_idx] * self.mode_window_size,maxlen=self.mode_window_size)

            if "waist" in segments:
                time.sleep(0.5)
                self.execute_action({'waist_head': np.concatenate([segments['neck'],segments['waist']])},t=5)     
        return

    def retrieve_observation(self):
        """Retrieve observation data from the wa2
        
        Returns:
            dict: Dictionary containing camera images, joint states, and timestamp from dataset
        """
        try:
            result = {}
            ref_timestamp = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            for cam_name in self.camera_image_queue:
                image = self.camera_image_queue[cam_name]
                if image is None:
                    return None
                result[f'cam.{cam_name}'] = image
            result['ref_timestamp'] = ref_timestamp
            result['obs.state'] = self.current_state
            return result
        except Exception as e:
            print(e)
            return None

    def close(self):
        """Close the mock robot and clean up resources.
        
        This method performs cleanup for the mock robot simulation.
        """
        self.logger.info('Closing wa2 robot...')
        self._stop = True
        resp = rospy.ServiceProxy(f"/zj_humanoid/upperlimb/clear_servo_params", Servo).call(ServoRequest())
        return
    
    def load_action_data(self, parquet_path, key="action"):
        """ read specific data from parquet file

        Args:
            parquet_path: the parquet file path 
            key: key of data, for example, action, observation.state
        """
        # read parquet file
        df = pd.read_parquet(parquet_path)
        data = df[key].tolist()
        # process data of dexterous hand to gripper format
        processed_data = []
        for idx, ele in enumerate(data):
            processed_data.append(ele)
        return processed_data

    def replay_trajectories(self, parquet_path, use_default: bool=True, accelerate:bool=True, accelerate_times: int=2, exclude_path=['place'], progress_fn=None):
        """replay trajectory based on teleoperation data"""
        try:
            trajs = self.load_action_data(parquet_path=parquet_path)
            for idx, traj in enumerate(trajs):
                if progress_fn is not None:
                    progress_fn(idx, len(trajs), traj)
                traj=np.array(traj)
                self.execute_action({'arm': traj[0:16].tolist()})
                self.execute_action({'hand': np.concatenate((traj[58:64], traj[64:70]))})
                time.sleep(0.03)
        except Exception as e:
            print(f"Replay {parquet_path} failed, error: {e}")

if __name__ == '__main__':
    from conf.robots_conf import get_robots_config
    config = get_robots_config()
    robot = RobotBody(config)
    robot.execute_action({'waist':np.array([0])})
