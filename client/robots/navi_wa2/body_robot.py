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
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.cfg = config
        self.current_state = np.zeros(8*2+6*2)
        # Main stop flag
        self._stop = False

        service_name_servo = '/zj_humanoid/upperlimb/set_servo_params'
        service_name_hand = '/zj_humanoid/hand/joint_switch/dual'
        _ensure_rospy_node()
        rospy.wait_for_service(service_name_servo, timeout=10.0)
        rospy.wait_for_service(service_name_hand, timeout=10.0)

        # Create subscribers for joint state topics
        self.subscriber = rospy.Subscriber(
            '/zj_humanoid/upperlimb/joint_states',      # Topic name
            JointState,           # Message type
            self.joint_states_callback,  # Callback function
            queue_size=5 #10         # Queue size
        )
        self.subscriber_hand = rospy.Subscriber(
            '/zj_humanoid/hand/joint_states',      # Topic name
            JointState,           # Message type
            self.joint_states_callback_hand,  # Callback function
            queue_size=5 #10         # Queue size
        )        
        # Arm controller
        rospy.ServiceProxy(service_name_servo, Servo).call(ServoRequest(time=self.cfg['tt'], gain=self.cfg['gain'])) 
        self.servoj = rospy.Publisher('/zj_humanoid/upperlimb/servoj/dual_arm', Joints, queue_size=1)
        # Hand controller
        self.hand_controller = rospy.ServiceProxy(service_name_hand, HandJoint)
        self.hand_request_ready = False
        self.hand_request = HandJointRequest()
        self.hand_thread = threading.Thread(
                target=self.hand_request_func,
                name="navi_wa2_hand_request_func",
                daemon=True  # Run as a daemon so it exits with the main thread
            )
        self.hand_thread.start()
        # Camera receiver
        self.bridge = CvBridge()
        camera_topics = dict(getattr(self.cfg.camera, 'topic_dict', {}))
        self.camera_topic_substribers = {came_name:None for came_name in camera_topics}
        self.camera_image_queue = {came_name:None for came_name in camera_topics}
        self.camera_stamp_queue = {came_name:None for came_name in camera_topics}
        self.camera_lock = threading.Lock()
        configured_ref = str(getattr(getattr(self.cfg, 'camera', None), 'ref', 'head') or 'head')
        self.camera_ref = configured_ref if configured_ref in camera_topics else next(iter(camera_topics), None)
        self.current_timestamp = None
        for cam_name, cam_topic in camera_topics.items():
            if not cam_topic:
                self.logger.warning(f"Skip empty camera topic for {cam_name}")
                continue
            self.camera_topic_substribers[cam_name] = rospy.Subscriber(
                cam_topic,  # Topic name
                CompressedImage,                                    # Message type
                self.camera_image_callback,                      # Callback function
                callback_args=cam_name,  # Pass camera identifier through callback_args
                queue_size=1                              # Queue size, prioritizing real-time behavior
            )
        # Hand and waist MoveJ controllers
        self.waist_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/waist', MoveJ)
        self.left_arm_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/left_arm', MoveJ)
        self.right_arm_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/right_arm', MoveJ)
        self.neck_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/neck', MoveJ)
        self.dual_arm_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/dual_arm', MoveJ)
        self.waist_head_movej_controller=rospy.ServiceProxy('/zj_humanoid/upperlimb/movej/whole_body', MoveJ)
        time.sleep(0.5)

        # Currently active discrete hand gesture indices
        self.current_left_idx = 0
        self.current_right_idx = 0

        pose_open = np.array([-0.6, 0.9, 0.0, 0.0, 0.0, 0.0])
        pose_close = np.array([-0.2, 0.9, 0.0, 1.0, 1.0, 1.0])
        pose_half = np.array([-0.2, 0.9, 0.4, 0.4, 0.4, 0.4])
        self.hand_poses = [pose_open, pose_close, pose_half]
        self.control_action_jump_threshold = float(self.cfg.get('control_action_jump_threshold', 0.05))



    def camera_image_callback(self, msg, cam_name):
        try:
            cv_image = self.bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")
            stamp = msg.header.stamp.to_nsec() if getattr(msg, 'header', None) is not None else 0
            if not stamp:
                stamp = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            with self.camera_lock:
                self.camera_image_queue[cam_name] = cv_image
                self.camera_stamp_queue[cam_name] = stamp
            return
        except CvBridgeError as e:
            rospy.logerr(f"CvBridge transfer error: {e}")
        return

    def joint_states_callback(self, msg):
        """
        Callback function for received JointState messages.
        """
        self.current_state[:16] = msg.position[:16]
        return
    
    def joint_states_callback_hand(self, msg):
        """
        Callback function for received JointState messages.
        """
        self.current_state[16:] = msg.position[:]
        return

    def _check_control_action_jump(self, action):
        current_action = np.asarray(action, dtype=float).reshape(-1)
        current_state = np.asarray(self.current_state, dtype=float).reshape(-1)
        if not self.joint_indices:
            return current_action

        max_index = max(self.joint_indices)
        if max_index >= current_state.shape[0] or max_index >= current_action.shape[0]:
            msg = (
                f"Control action/state shape mismatch for joint index {max_index}: "
                f"state={current_state.shape}, action={current_action.shape}."
            )
            self.logger.error(msg)
            raise RuntimeError(msg)

        diff = np.abs(current_action[self.joint_indices] - current_state[self.joint_indices])
        max_pos = int(np.argmax(diff))
        max_diff = float(diff[max_pos])
        if max_diff > self.control_action_jump_threshold:
            action_index = self.joint_indices[max_pos]
            msg = (
                f"Control action jump detected at action index {action_index}: "
                f"diff={max_diff:.6f}, threshold={self.control_action_jump_threshold:.6f}, "
                f"state={current_state[action_index]:.6f}, action={current_action[action_index]:.6f}."
            )
            self.logger.error(msg)
            raise RuntimeError(msg)

        return current_action
    
    def control_robot(self, action):
        """Control the robot arm and gripper based on the given action.
        
        Args:
            action (array-like): Action array containing arm commands (0:14) and gripper commands (14:16)
        """
        action = self._check_control_action_jump(action)
        left_hand_action = np.array(action[16:22])
        right_hand_action = np.array(action[22:28])

        raw_left_idx = np.argmin([np.linalg.norm(left_hand_action - p) for p in self.hand_poses])
        raw_right_idx = np.argmin([np.linalg.norm(right_hand_action - p) for p in self.hand_poses])
        self.current_left_idx = raw_left_idx
        self.current_right_idx = raw_right_idx

        target_left = self.hand_poses[self.current_left_idx]
        target_right = self.hand_poses[self.current_right_idx]
        
        target_hand_action = np.concatenate([target_left, target_right])

        # Execute action
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
        
        pose_len = len(target_pose)
        segments = {}
        print("reset robot")
        for name, v in self.action_layout.items():
            start = v['start']

            if start >= pose_len:
                continue

            end = min(v['end'], pose_len)
            segments[name] = target_pose[start:end]
        print(segments)
        if mode == "dispatch":
            if "waist" in segments:
                default_arm_pose=np.array([0.182591655739083, 0.32575521044236666, 0.639202615644364, 0.03292066673111549, -1.9789475037079458, 0.5495126798768879, -0.1635420177877668, -0.5]+[ -0.21499700078493333, 0.1528587929215064, -0.718166681663206, 0.12983709623767936, -1.6508818544817816, -0.38494056388590252, -0.8677823346142831, 0.5])
                current_arm_position=np.asarray(self.current_state, dtype=float)[:len(default_arm_pose)].copy()
                trajs = self.ruckig_planning(current_arm_position, default_arm_pose,dof=len(default_arm_pose))
                for i, traj in enumerate(trajs):
                    self.execute_action({'arm': traj})
                    time.sleep(0.01)
                
                self.execute_action({'waist_head': np.concatenate([segments['neck'],segments['waist']])},t=5)
                time.sleep(0.5)
                
            if "arm" in segments:
                target_arm_position = np.array(segments['arm'])
                current_arm_position=np.asarray(self.current_state, dtype=float)[:len(target_arm_position)].copy()
                trajs = self.ruckig_planning(current_arm_position, target_arm_position,dof=len(target_arm_position))
                for i, traj in enumerate(trajs):
                    self.execute_action({'arm': traj})
                    time.sleep(0.01)
                self.execute_action({'hand':np.array(segments['hand'])})

                time.sleep(0.5)
            
        else:
            if "arm" in segments:
                target_arm_position = np.asarray(segments['arm'], dtype=float)
                current_arm_position=np.asarray(self.current_state, dtype=float)[:len(target_arm_position)].copy()
                trajs = self.ruckig_planning(current_arm_position, target_arm_position,dof=16)
                for i, traj in enumerate(trajs):
                    self.execute_action({'arm': traj})
                    time.sleep(0.02)
                    
            if "hand" in segments:
                self.execute_action({'hand':np.array(segments['hand'])})

            if "neck" in segments and "waist" in segments:
                self.execute_action({'waist_head': np.concatenate([segments['neck'],segments['waist']])},t=5)     
        return

    def retrieve_observation(self):
        """Retrieve observation data from the wa2
        
        Returns:
            dict: Dictionary containing camera images, joint states, and timestamp from dataset
        """
        try:
            with self.camera_lock:
                if self.camera_ref is None:
                    return None
                ref_timestamp = self.camera_stamp_queue.get(self.camera_ref)
                if ref_timestamp is None:
                    return None
                if ref_timestamp == self.current_timestamp:
                    return None

                images = {}
                for cam_name, image in self.camera_image_queue.items():
                    if image is None:
                        return None
                    images[cam_name] = image.copy()
                self.current_timestamp = ref_timestamp

            result = {f'cam.{self.camera_ref}': images[self.camera_ref]}
            for cam_name, image in images.items():
                if cam_name == self.camera_ref:
                    continue
                result[f'cam.{cam_name}'] = image
            result['ref_timestamp'] = ref_timestamp
            result['obs.state'] = np.asarray(self.current_state, dtype=float).copy()
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
