#retarget pose from input device to robot
#Group type
uint8 NONE = 0
uint8 DURAL_ARM = 1
uint8 LEFT_ARM = 2
uint8 RIGHT_ARM = 3
uint8 WAIST = 4
uint8 HEAD = 5
uint8 WAIST_HEAD = 6

#device type
uint8 VR = 101
uint8 MOCAP = 102

std_msgs/Header    header 
uint8              group_arms    #臂的输入类型    0~3
uint8              group_body    #身体的输入类型  0、4~6
uint8              device     # 输入设备类型      101~102
geometry_msgs/Pose left_ee_pose # 左臂 SE3 Pose
geometry_msgs/Pose right_ee_pose # 右臂 SE3 Pose
geometry_msgs/Pose left_upper_arm # 左大臂 SE3 Pose
geometry_msgs/Pose right_upper_arm # 右大臂 SE3 Pose
string[] body_joint_names # 头 腰，等关节names
float64[] body_joint_positions #头 腰，等关节cmd，顺序与names一致


