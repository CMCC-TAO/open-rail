std_msgs/Header header  # frame id 默认填写base_link, timestamp发送时间

# 反馈末端位姿状态
string[] frame_names   #运控参数配置定义
geometry_msgs/Pose[] frame_poses

# 反馈自碰撞状态
# [collision_pair_1， collision_pair_2]组成一组碰撞对的frame名称
string[] collision_pairs_1
string[] collision_pairs_2

# 运控模式
uint8 MODE_STOP=0
uint8 MODE_SERVO=1
uint8 MODE_PLANNING=2
uint8 mode

# 实时控制的运控错误码
# 0: no error 
uint8 error_code
string error_msg
