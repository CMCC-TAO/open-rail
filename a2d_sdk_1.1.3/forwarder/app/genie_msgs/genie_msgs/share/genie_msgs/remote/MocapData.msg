std_msgs/Header     header
uint32              status                  # 遥设备状态   0: normal, 1: not calibrated

# 对于手臂的状态值
#   kNormal                       = 0x0000	#正常
#   kNotCalibrated                = 0x0001	#未标定
uint32              err_code                # 遥设备错误码
MocapJointState[]        mocap_joint_states            # 动捕或者VR手势识别的数据