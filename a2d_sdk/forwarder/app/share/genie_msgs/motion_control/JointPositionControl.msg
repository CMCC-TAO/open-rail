# frame id 无用, timestamp发送时间
std_msgs/Header header
float64 lifetime

uint32 GROUP_HEAD_YAW = 1
uint32 GROUP_HEAD_PITCH = 2
uint32 GROUP_LEFT_ARM = 4
uint32 GROUP_RIGHT_ARM = 8
uint32 GROUP_WAIST_LIFT = 16
uint32 GROUP_WAIST_PITCH = 32
uint32 GROUP_LEFT_TOOL = 128 # 手或夹爪，mc根据配置
uint32 GROUP_RIGHT_TOOL = 256 # 手或夹爪，mc根据配置

uint32 control_group

# 关节位置控制信息
float64 head_yaw_joint_position
float64 head_pitch_joint_position

float64[] left_arm_joint_positions
float64[] right_arm_joint_positions

float64 waist_lift_joint_position
float64 waist_pitch_joint_position

float64[] left_tool_joint_positions
float64[] right_tool_joint_positions
