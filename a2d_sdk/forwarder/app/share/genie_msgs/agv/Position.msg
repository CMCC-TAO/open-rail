std_msgs/Header     header
int32               agv_status        #底盘状态 0:Reseting(复位), 1:Edged(触变), 2: Scram(急停), 3:Mapping(建图), 4:NeedRelocate(需要重定位), 5:Avoid(避障), 6: Charging(充电), 7:Walking(行走), 8: Idle(空闲), 9:NotReady(手动等)
float32             position_conf     #定位置信度 0-100
float32             agv_pos_x         #地图系坐标x, 单位(m)
float32             agv_pos_y         #地图系坐标y, 单位(m)
float32             agv_pos_z         #地图系坐标z, 单位(m) 未使用
float32             agv_angle         #地图系坐标朝向角度, 单位(弧度)
float32             odom_x            #odom坐标系x 单位(m)
float32             odom_y            #odom坐标系y 单位(m)
float32             odom_z            #odom坐标系z 单位(m)
float32             odom_angle        #odom坐标系朝向角度, 单位(弧度)
float32             linear_speed      #底盘线速度 单位(m/s)
float32             angular_speed     #底盘角速度 单位(弧度/s)
float32             acc_x             #IMU坐标加速度x 单位(m)
float32             acc_y             #IMU坐标加速度y 单位(m)
float32             acc_z             #IMU坐标加速度z 单位(m)
float32             gyro_x            #IMU坐标角速度x方向 单位(m)
float32             gyro_y            #IMU坐标角速度y方向 单位(m)
float32             gyro_z            #IMU坐标角速度z方向 单位(m)
float32             roll              #IMU旋转状态 翻滚角
float32             pitch             #IMU旋转状态 俯仰角
float32             yaw               #IMU旋转状态 航向角
int32               map_id            #当前地图ID
int32               chassis_error     #故障码
MotorState[]        motor_states      # 底盘电机状态 目前只有速度，电流，温度
