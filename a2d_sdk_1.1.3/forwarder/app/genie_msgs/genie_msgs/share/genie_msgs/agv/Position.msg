std_msgs/Header     header
int32               agv_status        #
float32             position_conf
float32             agv_pos_x
float32             agv_pos_y
float32             agv_pos_z
float32             agv_angle
float32             odom_x
float32             odom_y
float32             odom_z
float32             odom_angle
float32             linear_speed
float32             angular_speed
float32             acc_x
float32             acc_y
float32             acc_z
float32             gyro_x
float32             gyro_y
float32             gyro_z
float32             roll
float32             pitch
float32             yaw
MotorState[]        motor_states       # 底盘电机状态
AGVTaskState        agv_task_state    # AGV任务状态
