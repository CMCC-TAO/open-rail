std_msgs/Header     header

MotorState[]        motor_states          # 每个关节的状态
float64[]           force_data            # 六维力数据
int32               force_coordinate      # 六维力坐标系
int32               force_state           # 六维力传感器状态：0 = 成功，1 = 失败，-1 = 通信失败，-2 = 数据接受失败，-3 = 返回值解析失败
#   kNormal                         = 0x0000    # 正常, 但是控制链路未建立
#   kNormalInControl                = 0x0001    # 正常，控制链路已建立
#   kJointCommErr                   = 0x1001	#关节通信异常。
#   kTargetAngleOutOfBounds         = 0x1002	#目标角度超过限位。
#   kSingularPointDetected          = 0x1003	#该处不可达，为奇异点。
#   kRTKernelCommError              = 0x1004	#实时内核通信错误。
#   kJointCommBusError              = 0x1005	#关节通信总线错误。
#   kPlanningLayerKernelError       = 0x1006	#规划层内核错误。
#   kJointOverSpeed                 = 0x1007	#关节超速。
#   kEndInterfaceBoardConnFailure   = 0x1008	#末端接口板无法连接。
#   kSpeedLimitExceeded             = 0x1009	#超速度限制。
#   kAccelLimitExceeded             = 0x100A	#超加速度限制。
#   kJointBrakeNotReleased          = 0x100B	#关节抱闸未打开。
#   kTeachModeOverSpeed             = 0x100C	#拖动示教时超速。
#   kRobotArmCollision              = 0x100D	#机械臂发生碰撞。
#   kWorkCoordSysNotFound           = 0x100E	#无该工作坐标系。
#   kToolCoordSysNotFound           = 0x100F	#无该工具坐标系。
#   kJointEnableLostError           = 0x1010	#关节发生掉使能错误。
#   kArcPlanningError               = 0x1011	#圆弧规划错误。
#   kSelfCollisionError             = 0x1012	#自碰撞错误。
#   kElecFenceCollisionError        = 0x1013	#碰撞到电子围栏错误。
#   kJointSoftLimitExceeded         = 0x1014	#超关节软限位错误。
#   kSixDimForceModuleAbnormal      = 0x2003	#六维力模块异常。
#                                   # 0x2004	#一维力模块异常。
#   kOutputCurrentAbnormal          = 0x2005	#输出电流异常。
#   kControllerOverTemp             = 0x5003	#控制器过温。
#   kControllerOverCurrent          = 0x5005	#控制器过流。
#   kControllerUnderCurrent         = 0x5006	#控制器欠流。
#   kControllerOverVoltage          = 0x5007	#控制器过压。
#   kControllerUnderVoltage         = 0x5008	#控制器欠压。
#   kOtherErr                       = 0x9000

uint32              arm_state             # 机械臂状态, 参考以上枚举
int32               system_error          # 系统错误码
