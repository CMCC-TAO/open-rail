import logging
import time
import os
import numpy as np

from .SDK_PYTHON.fx_kine import Marvin_Kine, FX_InvKineSolvePara, convert_to_8x8_matrix
from .SDK_PYTHON.fx_robot import Marvin_Robot, DCSS


class SaveJoints:
    def __init__(self):
        self.left_cmd_path = "left_cmd.csv"
        self.right_cmd_path = "right_cmd.csv"
        self.left_real_path = "left_real.csv"
        self.right_real_path = "right_real.csv"
        self.left_cmd_f = open(self.left_cmd_path, 'w')
        self.right_cmd_f = open(self.right_cmd_path, 'w')
        self.left_real_f = open(self.left_real_path, 'w')
        self.right_real_f = open(self.right_real_path, 'w')
        self.left_cmd_f.write('time,joint1,joint2,joint3,joint4,joint5,joint6,joint7\n')
        self.right_cmd_f.write('time,joint1,joint2,joint3,joint4,joint5,joint6,joint7\n')
        self.left_real_f.write('time,joint1,joint2,joint3,joint4,joint5,joint6,joint7\n')
        self.right_real_f.write('time,joint1,joint2,joint3,joint4,joint5,joint6,joint7\n')
        self.first_time = None
    
    def write(self, t, cmd_joints, real_joints):
        def _write(f, t, joints):
            jstr = ','.join([f"{j:.5f}" for j in joints])
            f.write(str(t) + ',' + jstr + '\n')
        
        if self.first_time is None:
            self.first_time = t
        t = t - self.first_time

        if 'left_arm' in cmd_joints:
            _write(self.left_cmd_f, t, cmd_joints['left_arm'])
        if 'right_arm' in cmd_joints:
            _write(self.right_cmd_f, t, cmd_joints['right_arm'])
        if 'left_arm' in real_joints:
            _write(self.left_real_f, t, real_joints['left_arm'])
        if 'right_arm' in real_joints:
            _write(self.right_real_f, t, real_joints['right_arm'])


class TJDualArm:
    def __init__(self, ip='192.168.1.190'):
        logging.basicConfig(format='%(message)s')
        logger = logging.getLogger('debug_printer')
        logger.setLevel(logging.WARN)# 一键关闭所有调试打印
        self.logger = logger

        '''初始化订阅数据的结构体'''
        self.dcss=DCSS()

        '''初始化机器人接口'''
        self.robot=Marvin_Robot()
        self.connect(ip)

        '''开启日志以便检查'''
        self.robot.log_switch('0') #全局日志开："1", 关："0"
        self.robot.local_log_switch('0') # 主要日志开："1", 关："0"

        self.set_params()

        self.left_kk = Marvin_Kine()
        self.right_kk = Marvin_Kine()

        ini_result1 = self.left_kk.load_config(arm_type=0,config_path=os.path.join(os.path.dirname(__file__), 'ccs_m3.MvKDCfg'))
        ini_result2 = self.right_kk.load_config(arm_type=1,config_path=os.path.join(os.path.dirname(__file__),'ccs_m3.MvKDCfg'))

        '''
        初始化动力学
        '''
        _ = self.left_kk.initial_kine(
                                      robot_type=ini_result1['TYPE'][0],
                                      dh=ini_result1['DH'][0],
                                      pnva=ini_result1['PNVA'][0],
                                      j67=ini_result1['BD'][0])

        _ = self.right_kk.initial_kine(
                                       robot_type=ini_result2['TYPE'][1],
                                       dh=ini_result2['DH'][1],
                                       pnva=ini_result2['PNVA'][1],
                                       j67=ini_result2['BD'][1])
        
        self.left_arm_name = "left_arm"
        self.right_arm_name = 'right_arm'
        self.dual_arm_name = 'dual_arm'
        self.time_stamp_name = 'timestamp'
        # self.save_joints = SaveJoints()
        # self.ref_joints = {
        #     self.left_arm_name: np.deg2rad([74.2748, -35.7865, -70.0481, -87.2715, -46.2021, -13.0388,  -0.757]),
        #     self.right_arm_name: np.deg2rad([-70.3029, -28.9251,  60.5151, -88.275,   51.9415, -14.8668,   5.2858])
        # }
        self.ref_joints = {
            self.left_arm_name: np.deg2rad([41.3546, -48.0843, -19.3143, -106.1716, 36.3044, 16.5699, -30.3709]),
            self.right_arm_name: np.deg2rad([-31.5022, -54.5663, 4.2399, -107.1719, -25.8939, 40.2195, 23.0243])
        }
        _, left_zsp_param = self.left_kk.fk_nsp(self.ref_joints[self.left_arm_name])
        _, right_zsp_param = self.right_kk.fk_nsp(self.ref_joints[self.right_arm_name])
        self.left_zsp_xyz = [left_zsp_param[0][0], left_zsp_param[1][0], left_zsp_param[2][0], 0., 0., 0.]
        self.right_zsp_xyz = [right_zsp_param[0][0], right_zsp_param[1][0], right_zsp_param[2][0], 0., 0., 0.]

        self.inital_time = time.perf_counter()
    
    def connect(self, ip):
        '''查验连接是否成功'''
        init = self.robot.connect(ip)
        if init==0:
            self.logger.error(f'failed to connect to the robot {ip}, port is occupied')
            exit(0)

        '''检查机械臂和伺服当前是否存错误，有错误清错'''
        self.robot.check_error_and_clear(self.dcss)

        '''通过确认freame数据的刷新，确认UDP数据通道连接成功（防火墙等可能不能正常收到数据）'''
        motion_tag = 0
        frame_update = None
        for i in range(5):
            sub_data = self.robot.subscribe(self.dcss)
            print(f"connect frames :{sub_data['outputs'][0]['frame_serial']}")
            if sub_data['outputs'][0]['frame_serial'] != 0 and frame_update != sub_data['outputs'][0]['frame_serial']:
                motion_tag += 1
                frame_update = sub_data['outputs'][0]['frame_serial']
            time.sleep(0.01)
        if motion_tag > 0:
            self.logger.info('success:robot connected')
        else:
            self.logger.error('failed:robot connection failed')
            exit(0)
    
    def set_params(self):
        '''设置位置模式和速度 加速度百分比'''
        self.robot.clear_set()
        self.robot.set_state(arm='A',state=1)#state=1位置模式
        self.robot.set_vel_acc(arm='A',velRatio=100, AccRatio=100)
        self.robot.set_state(arm='B',state=1)#state=1位置模式
        self.robot.set_vel_acc(arm='B',velRatio=100, AccRatio=100)
        self.robot.send_cmd()
        time.sleep(0.5)
        # self.set_tool()

    def set_tool(self):
        self.robot.clear_set()
        self.robot.set_tool(arm='A', kineParams=[0.]*6, dynamicParams=[0.37333257506824447, 71.32831542653791, 62.32438226130522, 178.23014678552454, 0.017041762269679857, 0.0, 0.0, 0.028467172838229613, 0.0, 0.020694018377812578])
        self.robot.send_cmd()
        time.sleep(0.5)

        self.robot.clear_set()
        self.robot.set_tool(arm='B', kineParams=[0.]*6, dynamicParams=[0.46751689847913597, 32.710811507788996, 1.1947231103226919, 181.3187253543796, 0.028043181840994406, 0.0, 0.0, 0.001, 0.0, 0.006498988761305333])
        self.robot.send_cmd()
        time.sleep(0.5)
    
    def set_vel_acc(self, arm, vel, acc):
        if arm == 'A' or arm == self.left_arm_name:
            self.robot.clear_set()
            self.robot.set_vel_acc(arm='A',velRatio=vel, AccRatio=acc)
            self.robot.send_cmd()
        elif arm == 'B' or arm == self.right_arm_name:
            self.robot.clear_set()
            self.robot.set_vel_acc(arm='B',velRatio=vel, AccRatio=acc)
            self.robot.send_cmd()
        elif arm == 'AB' or arm == self.dual_arm_name:
            self.robot.clear_set()
            self.robot.set_vel_acc(arm='A',velRatio=vel, AccRatio=acc)
            self.robot.set_vel_acc(arm='B',velRatio=vel, AccRatio=acc)
            self.robot.send_cmd()
        time.sleep(0.5)
    
    def get_current_joints(self):
        # 获取当前双臂关节角
        data = self.robot.subscribe(self.dcss)
        a_current_joints=np.deg2rad(data["outputs"][0]["fb_joint_pos"])
        b_current_joints=np.deg2rad(data["outputs"][1]["fb_joint_pos"])
        timestamp = time.perf_counter() - self.inital_time
        return {self.left_arm_name: a_current_joints, self.right_arm_name: b_current_joints, self.time_stamp_name:timestamp}
    
    def get_current_pose(self, arm):
        # 获取当前双臂末端姿态矩阵 4x4
        return self.forward_kinematics({arm: self.get_current_joints()[arm]})[arm]
    
    def forward_kinematics(self, joints: dict):
        # 正运动学，根据 joints 得到末端位姿矩阵4x4
        ret = {}
        if self.left_arm_name in joints:
            tmp = self.left_kk.fk(joints=np.rad2deg(joints[self.left_arm_name]))
            if tmp:
                tmp = np.array(tmp)
                tmp[:3, 3] = tmp[:3, 3] / 1000          # 转成 米
                ret[self.left_arm_name] = tmp
        if self.right_arm_name in joints:
            tmp = self.right_kk.fk(joints=np.rad2deg(joints[self.right_arm_name]))
            if tmp:
                tmp = np.array(tmp)
                tmp[:3, 3] = tmp[:3, 3] / 1000          # 转成 米
                ret[self.right_arm_name] = tmp
        return ret
    
    def invert_kinematices(self, poses: dict, ref_joints: dict=None):
        # 逆运动学
        ret = {}
        if self.left_arm_name in poses:
            if ref_joints is None or self.left_arm_name not in ref_joints or ref_joints[self.left_arm_name] is None:
                # ref_j = self.get_current_joints()[self.left_arm_name]
                ref_j = self.ref_joints[self.left_arm_name]
            else:
                ref_j = ref_joints[self.left_arm_name]
            sp = FX_InvKineSolvePara()
            pose = poses[self.left_arm_name].copy()
            pose[:3, 3] = pose[:3, 3] * 1000                # 转成 毫米
            mat16 = pose.reshape(16).tolist()
            sp.set_input_ik_target_tcp(mat16)
            sp.set_input_ik_ref_joint(np.rad2deg(ref_j))
            sp.set_input_ik_zsp_type = 1
            sp.set_input_ik_zsp_para = self.left_zsp_xyz
            sp.set_input_zsp_angle = 0.
            ik_result_structure = self.left_kk.ik(structure_data=sp)
            if ik_result_structure:
                joints = ik_result_structure.m_Output_RetJoint.to_list()
                # print(f'{self.left_arm_name} ik joints:{joints}')
                # print(f'{self.left_arm_name} ik 当前位姿是否超出位置可达空间（False：未超出；True：超出）: {ik_result_structure.m_Output_IsOutRange}')
                # print(f'{self.left_arm_name} ik 各关节是否发生奇异（False：未奇异；True：奇异）: {ik_result_structure.m_Output_IsDeg[:]}')
                # print(f'{self.left_arm_name} ik 是否有关节超出位置正负限制（False：未超出；True：超出）: {ik_result_structure.m_Output_IsJntExd}')
                # print(f'{self.left_arm_name} ik 各关节是否超出位置正负限制（False：未超出；True：超出）: {ik_result_structure.m_Output_JntExdTags[:]}')
                ret[self.left_arm_name] = np.deg2rad(joints)
            else:
                print(f'{self.left_arm_name} NO ik results')
                ret[self.left_arm_name] = None

        if self.right_arm_name in poses:
            if ref_joints is None or self.right_arm_name not in ref_joints or ref_joints[self.right_arm_name] is None:
                # ref_j = self.get_current_joints()[self.right_arm_name]
                ref_j = self.ref_joints[self.right_arm_name]
            else:
                ref_j = ref_joints[self.right_arm_name]
            sp = FX_InvKineSolvePara()
            pose = poses[self.right_arm_name].copy()
            pose[:3, 3] = pose[:3, 3] * 1000                # 转成 毫米
            mat16 = pose.reshape(16).tolist()
            sp.set_input_ik_target_tcp(mat16)
            sp.set_input_ik_ref_joint(np.rad2deg(ref_j))
            sp.set_input_ik_zsp_type = 1
            sp.set_input_ik_zsp_para = self.left_zsp_xyz
            sp.set_input_zsp_angle = 0.
            ik_result_structure = self.right_kk.ik(structure_data=sp)
            if ik_result_structure:
                joints = ik_result_structure.m_Output_RetJoint.to_list()
                # print(f'{self.right_arm_name} ik joints:{joints}')
                # print(f'{self.right_arm_name} ik 当前位姿是否超出位置可达空间（False：未超出；True：超出）: {ik_result_structure.m_Output_IsOutRange}')
                # print(f'{self.right_arm_name} ik 各关节是否发生奇异（False：未奇异；True：奇异）: {ik_result_structure.m_Output_IsDeg[:]}')
                # print(f'{self.right_arm_name} ik 是否有关节超出位置正负限制（False：未超出；True：超出）: {ik_result_structure.m_Output_IsJntExd}')
                # print(f'{self.right_arm_name} ik 各关节是否超出位置正负限制（False：未超出；True：超出）: {ik_result_structure.m_Output_JntExdTags[:]}')
                ret[self.right_arm_name] = np.deg2rad(joints)
            else:
                print(f'{self.right_arm_name} NO ik results')
                ret[self.right_arm_name] = None
        return ret
    
    def set_joints(self, joints: dict):
        if self.left_arm_name not in joints and self.right_arm_name not in joints:
            return

        self.robot.clear_set()
        if self.left_arm_name in joints:
            # print(self.left_arm_name, "Set joints: ", np.rad2deg(joints[self.left_arm_name]))
            self.robot.set_joint_cmd_pose(arm='A', joints=np.rad2deg(joints[self.left_arm_name]))
        if self.right_arm_name in joints:
            # print(self.right_arm_name, "Set joints: ", np.rad2deg(joints[self.right_arm_name]))
            self.robot.set_joint_cmd_pose(arm='B', joints=np.rad2deg(joints[self.right_arm_name]))
        # self.save_joints.write(time.time_ns(), joints, self.get_current_joints())
        self.robot.send_cmd()
    
    def down_enable(self, arm):
        # 下使能
        if arm == 'A' or arm == self.left_arm_name:
            self.robot.clear_set()
            self.robot.set_state(arm='A',state=0)
            self.robot.send_cmd()
        elif arm == 'B' or arm == self.right_arm_name:
            self.robot.clear_set()
            self.robot.set_state(arm='B',state=0)
            self.robot.send_cmd()
        elif arm == 'AB' or arm == self.dual_arm_name:
            self.robot.clear_set()
            self.robot.set_state(arm='A',state=0)
            self.robot.set_state(arm='B',state=0)
            self.robot.send_cmd()

    def start_drag(self, arm):
        if arm == 'A' or arm == self.left_arm_name:
            self.robot.clear_set()
            self.robot.set_state(arm='A', state=3)              # 扭矩模式
            self.robot.send_cmd()
            time.sleep(0.5)

            self.robot.clear_set()
            self.robot.set_impedance_type(arm='A',type=1)       # 关节阻抗
            self.robot.send_cmd()
            time.sleep(0.5)

            self.robot.clear_set()
            self.robot.set_drag_space(arm='A',dgType=1)         # 关节空间拖动
            self.robot.send_cmd()
            time.sleep(0.5)
        elif arm == 'B' or arm == self.right_arm_name:
            self.robot.clear_set()
            self.robot.set_state(arm='B', state=3)              # 扭矩模式
            self.robot.send_cmd()
            time.sleep(0.5)

            self.robot.clear_set()
            self.robot.set_impedance_type(arm='B',type=1)       # 关节阻抗
            self.robot.send_cmd()
            time.sleep(0.5)

            self.robot.clear_set()
            self.robot.set_drag_space(arm='B',dgType=1)         # 关节空间拖动
            self.robot.send_cmd()
            time.sleep(0.5)
        else:
            print("!!!!!!!!!! drag 模式只支持单臂: A or B")
    
    def exit_drag(self, arm):
        # 退出拖拽模式，进入位置控制模式
        if arm == 'A' or arm == self.left_arm_name:
            self.robot.clear_set()
            self.robot.set_drag_space(arm='A',dgType=0)
            self.robot.send_cmd()
            time.sleep(0.5)

            self.robot.clear_set()
            self.robot.set_state(arm='A',state=1)
            self.robot.send_cmd()
            time.sleep(0.5)
        elif arm == 'B' or arm == self.right_arm_name:
            self.robot.clear_set()
            self.robot.set_drag_space(arm='B',dgType=0)
            self.robot.send_cmd()
            time.sleep(0.5)

            self.robot.clear_set()
            self.robot.set_state(arm='B',state=1)
            self.robot.send_cmd()
            time.sleep(0.5)

    def release(self):
        self.robot.clear_set()
        self.robot.set_state(arm='A',state=0)
        self.robot.set_state(arm='B',state=0)
        self.robot.send_cmd()
        time.sleep(0.5)

        '''释放机器人内存'''
        self.robot.release_robot()


if __name__ == '__main__':
    arm = TJDualArm()
    arm.start_drag('B')
    input()