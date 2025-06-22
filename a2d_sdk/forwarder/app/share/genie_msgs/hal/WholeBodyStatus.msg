std_msgs/Header     header

# 机械臂状态
uint32              right_arm_error      # 右臂错误码
uint32              left_arm_error       # 左臂错误码
bool                right_arm_control    # 右臂处在正在控制中
bool                left_arm_control     # 左臂处在正在控制中
bool                right_arm_estop      # 右臂处于急停模式中
bool                left_arm_estop       # 左臂处于急停模式中

# 末端状态
uint32              right_end_error      # 右末端错误码
uint32              left_end_error       # 左末端错误码

# 末端模型
string              right_end_model      # 右末端模型 120s (注:知行夹爪120s)， omnipicker， Roh (注:傲意灵巧手)， SkillHandS6 (注:因时S6灵巧手)
string              left_end_model       # 左末端模型 120s (注:知行夹爪120S)， omnipicker， Roh (注:傲意灵巧手)， SkillHandS6 (注:因时S6灵巧手)


# 腰部状态
uint32              waist_error          # 腰部错误码 

# 升降状态
uint32              lift_error           # 升降错误码

# 颈部状态
uint32              neck_error           # 颈部错误码

# 底盘状态
uint32              chassis_error        # 底盘错误码

