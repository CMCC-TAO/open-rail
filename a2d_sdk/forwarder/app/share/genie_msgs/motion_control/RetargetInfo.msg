# 控制组Group序号
uint8 GROUP_HEAD_YAW = 0
uint8 GROUP_HEAD_PITCH = 1
uint8 GROUP_LEFT_ARM = 2
uint8 GROUP_RIGHT_ARM = 3
uint8 GROUP_LEFT_TOOL = 4 # 手或夹爪，mc根据配置
uint8 GROUP_RIGHT_TOOL = 5 # 手或夹爪，mc根据配置
uint8 GROUP_WAIST_LIFT = 6
uint8 GROUP_WAIST_PITCH = 7
uint8 GROUP_CHASSIS = 8
uint8 group_id  #控制组序号

# 发出控制源
uint8 INPUT_VR = 51
uint8 INPUT_MOCAP = 52
uint8 INPUT_HMI = 53
uint8 INPUT_GDK = 54
uint8 input_type

uint8 ABS_POSE = 0
uint8 DELTA_POSE = 1
uint8 END_SPEED = 2
uint8 ABS_JOINT = 3
uint8 DELTA_JOINT = 4
uint8 JOINT_SPEED = 5
uint8 PASSIVE = 6

# 输出类型
# 0: 末端绝对位姿
# 1: 末端相对位姿（相对与Last Command）
# 2：末端速度 (不支持离线规划)
# 3: 绝对关节角
# 4: 相对关节角（相对与Last Command）
# 5：关节角速度 (不支持离线规划)
# 6: 被动 (加入SE3的ik解的自由度中)，等效之前的FREE模式
uint8 control_type

string frame_id   #末端控制的base frame
string[] target_frame_names
# 模式 0: 末端绝对位姿
geometry_msgs/Pose[] target_frame_poses

# 模式 1: 末端相对位姿（按照大模型的定义，比较奇怪）
geometry_msgs/Pose[] target_frame_poses_delta

# 模式0与1：输入参考位置，用于校正IK多解情况
string[] reference_frame_names
geometry_msgs/Pose[] reference_frame_poses

# 模式 2：末端速度（按照全局线速度与局部角速度）
geometry_msgs/Twist[] target_frame_velocities

# 模式3: 绝对关节角
float64[] target_joint_positions

# 模式4: 相对关节角
float64[] target_joint_positions_delta

# 模式5：关节角速度
float64[] target_joint_velocities