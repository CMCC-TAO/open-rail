import time
import cv2
import numpy as np
import ruckig

class RobotBase():
    def __init__(self):
        self.robot = None

    def controlRobot(self, action):
        """
        控制机器人执行动作
        Args:
            action: action array，顺序同obs['state']
        """
        raise NotImplementedError('controlRobot is not implemented')

    def retrieveObservation(self):
        """
        获取机器人当前obs
        Returns:
            obs: 机器人当前obs，obs['state']为当前pose
        """
        raise NotImplementedError('retrieveObservation is not implemented')

    def reset_robot(self, target_pose='default'):
        """
        重置机器人到指定姿态
        Args:
            target_pose: 目标姿态，'default'表示默认姿态，'zero'表示零位姿态，格式: [7左臂+7右臂+2夹爪+2头部+2腰部+2轮子]
        """
        if target_pose == 'default':
            target_pose = np.array([-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0])
        elif target_pose == 'zero':
            target_pose = np.array([0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0])
        elif isinstance(target_pose, list):
            target_pose = np.array(target_pose)
        
        current_obs = self.retrieveObservation()
        current_positions = current_obs['obs.state'][:14]
        target_positions = target_pose[:14]
        # 计算关节位置差异
        dis = np.abs(current_positions - target_positions)
        mask = dis > np.deg2rad(0.01)  # 决定是否使用插值策略
        # 如果差异很小，直接移动到目标位置
        if not np.any(mask):
            target_pose[:14] = target_positions
            self.controlRobot(target_pose)
            time.sleep(0.01)
            return
        # 否则规划
        trajs = self._ruckig_planning(current_positions, target_positions)
        for i, traj in enumerate(trajs):
            print(f"执行轨迹点 {i}: {traj}")
            target_pose[:14] = traj
            self.controlRobot(target_pose)
            time.sleep(0.01)
    
    def _ruckig_planning(self, current_pose, target_pose, dof=14, interval=0.01):
        """
        使用Ruckig进行轨迹规划
        Args:
            current_pose: 当前关节pose
            target_pose: 目标关节pose
            dof: 自由度
            interval: 间隔
        Returns:
            轨迹点列表
        """
        rk = ruckig.Ruckig(dof, interval)
        rk_input = ruckig.InputParameter(dof)
        rk_output = ruckig.OutputParameter(dof)
        
        # 设置当前状态
        rk_input.current_position = current_pose
        rk_input.current_velocity = [0.0] * dof
        rk_input.current_acceleration = [0.0] * dof
        
        # 设置目标状态
        rk_input.target_position = target_pose
        rk_input.target_velocity = [0.0] * dof
        rk_input.target_acceleration = [0.0] * dof
        
        # 设置运动约束
        rk_input.max_velocity = [2.0] * dof
        rk_input.max_acceleration = [1.0] * dof
        rk_input.max_jerk = [5.0] * dof
        
        # 生成轨迹
        trajs = []
        while rk.update(rk_input, rk_output) == ruckig.Result.Working:
            trajs.append(rk_output.new_position)
            rk_output.pass_to_input(rk_input)
        
        return trajs
    
    def close(self):
        pass
