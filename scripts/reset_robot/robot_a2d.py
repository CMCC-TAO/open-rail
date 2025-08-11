from rclpy.node import Node
from sensor_msgs.msg import JointState
from genie_msgs.srv import BodyPose
from std_msgs.msg import Header
import rclpy
import numpy as np
from geometry_msgs.msg import TwistStamped
import time
import numpy as np
import ruckig
from a2d_sdk.robot import RobotDds
from scipy.interpolate import CubicSpline

class RobotController_direct():
    """Direct robot controller for A2D robot.
    
    This class provides direct control interface for A2D robot with trajectory planning capabilities.
    
    Attributes:
        robot: RobotDds instance for robot communication
        dof (int): Degrees of freedom (14 for A2D robot)
        interval (float): Control interval in seconds
    """
    
    def __init__(self, simulation=False, robot=None):
        """Initialize the robot controller.
        
        Args:
            simulation (bool): Whether running in simulation mode
            robot: Existing robot instance, creates new one if None
        """
        self.robot = RobotDds() if robot is None else robot
        self.dof = 14
        self.interval = 0.01
        # Wait for robot to initialize
        time.sleep(1)

    def rucking_planing(self, current_pose, target_pose):
        """Generate trajectory using Ruckig trajectory planner.
        
        Args:
            current_pose: Current joint positions
            target_pose: Target joint positions
            
        Returns:
            list: Generated trajectory points
        """
        # Setup ruckig trajectory planner
        rk = ruckig.Ruckig(self.dof, self.interval)
        rk_input = ruckig.InputParameter(self.dof)
        rk_output = ruckig.OutputParameter(self.dof)

        # Set current state
        rk_input.current_position = current_pose
        rk_input.current_velocity = [0.0] * self.dof
        rk_input.current_acceleration = [0.0] * self.dof

        # Set target state
        rk_input.target_position = target_pose
        rk_input.target_velocity = [0.0] * self.dof
        rk_input.target_acceleration = [0.0] * self.dof

        # Set motion constraints
        rk_input.max_velocity = [2.0] * self.dof
        rk_input.max_acceleration = [1.0] * self.dof
        rk_input.max_jerk = [5.0] * self.dof

        # Generate trajectory
        # print("Generating trajectory...")
        trajs = []

        while rk.update(rk_input, rk_output) == ruckig.Result.Working:
            trajs.append(rk_output.new_position)
            rk_output.pass_to_input(rk_input)
        return trajs

    def third_order_interpolation(self, current_pose, target_pose):
        """Generate third-order polynomial interpolation trajectory.
        
        Args:
            current_pose: Current joint positions
            target_pose: Target joint positions
            
        Returns:
            list: Interpolated trajectory points
        """
        current = np.array(current_pose, dtype=np.float16)
        target = np.array(target_pose, dtype=np.float16)
        
    
        deltas = np.abs(target - current)
        mask = deltas > np.deg2rad(1)
        # print('mask', mask)
        max_velocity = 0.785  # rad/s
        # Calculate interpolation time
        if np.any(mask):
            T_i = (3 * deltas[mask]) / (2 * max_velocity)
            T_total = np.max(T_i)
        else:
            arm_msg = self.generate_joint_msg(target.tolist())
            self.publisher_arm.publish(arm_msg)
            # self.send_cmd(target.tolist(), neck_trans)
            return
        # print(T_total)
        # Pre-allocate arrays
        num_steps = int(T_total / 0.01) + 1
        time_points = np.linspace(0, T_total, num_steps + 1)
        coeff_a2 = 3 * (target - current) / (T_total ** 2 + 1e-9)
        coeff_a3 = -2 * (target - current) / (T_total ** 3 + 1e-9)
        
        # Broadcast calculation
        t_matrix = time_points[:, np.newaxis]  # 转换为列向量
        theta = current + coeff_a2 * t_matrix**2 + coeff_a3 * t_matrix**3
        # print(num_steps)
        # print(f'get interpolation time:{(time.time()-starttime)*1000} ms ')
        # Apply mask to handle joints that don't need interpolation
        theta[:, ~mask] = target[~mask]
        return theta.tolist()

    def test_arm_trajectory_planning(self, target_positions=None):
        """Test arm trajectory planning and execution

        Args:
            target_positions: Optional target joint positions. If None, uses initial positions.
        """
        # print("Starting arm trajectory test...")
        start_time = time.time()
        # Get current joint states
        current_positions, _ = self.robot.arm_joint_states()
        if not current_positions:
            raise Exception("Failed to get arm joint states")

        dis=np.abs(np.array(current_positions) - np.array(target_positions))
        mask = dis>np.deg2rad(0.01)  # Determine whether to use interpolation strategy
        if not np.any(mask):
            self.robot.move_arm(target_positions)
            time.sleep(0.03)
            return
        
        trajs = self.rucking_planing(current_positions,target_positions)
      
        # print(time.time() - start_time)
        # print(len(trajs))
        # # Execute trajectory
        # print("Executing trajectory...")
        for i, traj in enumerate(trajs):
            print(f"point {i} traj : {traj}")
            self.robot.move_arm(traj)
            time.sleep(self.interval)

        # Wait for motion to complete
        # time.sleep(0.1)

        # print("Trajectory test completed successfully!")


    def translate_rag_todeg(self,joints_list):
        """Convert joint values from radians to degrees and meters to centimeters
        
        Args:
            joints_list: List of joint values where first 3 are in radians and last is in meters
            
        Returns:
            List with first 3 elements converted to degrees and last element to centimeters
        """
        joint_list_3 = [round(joints_list[i] / 3.1415 * 180, 4) for i in range(3)]
        
        # Convert last element from meters to centimeters with 4 decimal places
        joints_list[-1] = round(joints_list[-1] * 100, 4)
        
        # Combine first 3 elements (angles) and last element (centimeters)
        joints_list = joint_list_3 + [joints_list[-1]]
            
        return joints_list
  

    def send_cmd(self, joints_value,neck_trans=False):
        if len(joints_value)!=22:
            print(len(joints_value))
            print("len joints_value should be 22!")
            print("7LeftArm、7RightArm、2gripper、2head、2waist、2wheel!")
            return
        arm_joints=joints_value[:14].tolist()
        gripper = joints_value[14:16].tolist()
        head_joints = joints_value[16:18].tolist()
        waist_joints=joints_value[18:20].tolist()
        weel_joints=joints_value[20:22].tolist()
        # 发送控制命令到机械臂
        start_time = time.time()
        self.test_arm_trajectory_planning(arm_joints)
        # print(time.time() - start_time)
        # ## 发送控制命令到夹爪
        self.robot.move_gripper(gripper)
        # print('send gripper')
        # time.sleep(1)
        # gripper_msg = self.generate_joint_msg(gripper)
        # self.publisher_gripper.publish(gripper_msg)
    
        # 发送控制命令到头部和腰部
        if neck_trans:
            translate_neckwaist=self.translate_rag_todeg(head_joints+waist_joints)
        else:
            translate_neckwaist = head_joints+waist_joints
        self.robot.move_head_and_waist(translate_neckwaist[:2],translate_neckwaist[2:]) #是否发送头腰部运动，复位时需要。
        # print('send neck waist')
        # self.robot.move_wheel(weel_joints)

        # ## 发送控制命令到轮子
        # wheel_msg=self.generate_wheel_msg(weel_joints)
        # self.publisher_wheel.publish(wheel_msg)
        # print("send robot control command finish")

def cubicspline_chunk(P):
    distances = np.linalg.norm(np.diff(P, axis=0), axis=1)
    print(len(P))
    total_distance = np.sum(distances)
    max_velocity = 1.57 * 0.8
    total_time = total_distance / max_velocity

    # 计算每段时间
    time_segments = distances / max_velocity

    # 过滤掉非正的时间段
    time_segments = time_segments[time_segments > 0]

    # 重新计算总时间
    total_time = np.sum(time_segments)

    # 计算时间向量
    time_vector = np.concatenate(([0], np.cumsum(time_segments)))

    # 使用三次样条插值
    cs = CubicSpline(time_vector, P[:len(time_vector)], bc_type='natural')

    # 生成插值结果
    t_fine = np.linspace(0, total_time, num=60)
    P_interp = cs(t_fine)
    return P_interp

def main(args=None, robot=None):
    """Main function to reset robot to default position.
    
    Args:
        args: Command line arguments (unused)
        robot: Existing robot instance
    """
    np.set_printoptions(suppress=True, precision=4)
    robot_controller = RobotController_direct(robot=robot)
    arm_joints = np.array([-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869,
                            1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873])
    gripper = np.array([0, 0])
    head_joints = np.array([0.0, 0.4363])
    waist_joints = np.array([0.2967, 20.0])
    weel_joints = np.array([0.0, 0.0])
    joint_list = np.concatenate((arm_joints, gripper, head_joints, waist_joints, weel_joints))
    robot_controller.send_cmd(joint_list)
    # Robot shutdown and cleanup would go here if needed

if __name__ == '__main__':
    main()
