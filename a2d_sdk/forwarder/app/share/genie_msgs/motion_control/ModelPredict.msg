std_msgs/Header header   # header timestamp为模型开始推理的时间

string[] body_joint_names # 头旋转 头俯仰 腰俯仰 腰升降，左臂 右臂等关节names
float64[] body_joint_positions #头 腰，臂等关节状态，顺序与names一致

# 模型输出类型
# 0: 相对位置
# 1: 绝对位置
# 2: 绝对关节角
# 3: 相对关节角
uint8 model_output_type

string[] target_link_names
geometry_msgs/Pose[] target_poses   # pose数组 
sensor_msgs/JointState[]  target_joint_states    # 输出目标关节角数组
float32[]  target_velocities   # 输出目标关节速度
float32[]  target_efforts   # 输出目标关节力矩

float64 model_sleep_time             # 两帧之间的等待时间
float64 trajectory_reference_time      # 单帧输出的轨迹参考时间
