# frame id 无用, timestamp发送时间
std_msgs/Header header
float64 lifetime

uint32 GROUP_LEFT_ARM = 4
uint32 GROUP_RIGHT_ARM = 8
uint32 GROUP_DUAL_ARM = 12

uint32 GROUP_LEFT_ARM_WAIST_LIFT = 20
uint32 GROUP_LEFT_ARM_WAIST_PITCH = 36
uint32 GROUP_LEFT_ARM_WAIST = 52
uint32 GROUP_RIGHT_ARM_WAIST_LIFT = 24
uint32 GROUP_RIGHT_ARM_WAIST_PITCH = 40
uint32 GROUP_RIGHT_ARM_WAIST = 56
uint32 GROUP_DUAL_ARM_WAIST_LIFT = 28
uint32 GROUP_DUAL_ARM_WAIST_PITCH = 44
uint32 GROUP_DUAL_ARM_WAIST = 60

uint32 control_group

geometry_msgs/Pose left_end_effector_pose
geometry_msgs/Pose right_end_effector_pose


