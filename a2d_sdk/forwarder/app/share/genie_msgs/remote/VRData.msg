std_msgs/Header     header
uint32              status                  # 遥设备状态
uint32              err_code                # 遥设备错误码

VRControllerState[] vr_controller_states    # 手柄状态， 0 = left，1 = right
