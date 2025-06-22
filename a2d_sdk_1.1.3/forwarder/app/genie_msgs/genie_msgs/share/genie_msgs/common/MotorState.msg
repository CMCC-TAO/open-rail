uint32              id
bool                enable                # 电机使能
float64             position
float64             velocity              
float64             effort                # 力矩
float32             current               # 电流  单位 mA
float32             voltage               # 电压  单位 V
float32             temperature           # 温度  单位 度

# 默认状态值为0 正常
# 对于灵巧手的状态值
#   kOpening = 0       # 正在展开
#   kClosing = 1       # 正在抓取
#   kPosReached = 2    # 位置到位停止
#   kOverCurrent = 3   # 电流保护停止
#   kForceReached = 4  # 力控到位停止
#   kStuck = 5         # 电机堵转停止

# 对于手臂的状态值
#   kJointNormal                  = 0x0000	#关节正常
#   kFOCError                     = 0x0001	#FOC错误
#   kOverVoltage                  = 0x0002	#过压。
#   kUnderVoltage                 = 0x0004	#欠压。
#   kOverTemperature              = 0x0008	#过温。
#   kStartFailure                 = 0x0010	#启动失败。
#   kEncoderError                 = 0x0020	#编码器错误。
#   kOverCurrent                  = 0x0040	#过流。
#   kSoftwareError                = 0x0080	#软件错误。
#   kTemperatureSensorError       = 0x0100	#温度传感器错误。
#   kPositionLimitExceeded        = 0x0200	#位置超限错误。
#   kInvalidJointID               = 0x0400	#关节ID非法。
#   kPositionTrackingError        = 0x0800	#位置跟踪错误。
#   kCurrentDetectionError        = 0x1000	#电流检测错误。
#   kBrakeOpenFailure             = 0x2000	#抱闸打开失败。
#   kPositionCommandStepWarning   = 0x4000	#位置指令阶跃警告。
#   kMultiTurnJointLostCount      = 0x8000	#多圈关节丢圈数。
#   kOtherErr                     = 0xF000	#通信丢帧。
uint32              status               

# 默认错误码为0
# 对于手臂关节错误码
#   kJointNormal                  = 0x0000	#关节正常
#   kFOCError                     = 0x0001	#FOC错误
#   kOverVoltage                  = 0x0002	#过压。
#   kUnderVoltage                 = 0x0004	#欠压。
#   kOverTemperature              = 0x0008	#过温。
#   kStartFailure                 = 0x0010	#启动失败。
#   kEncoderError                 = 0x0020	#编码器错误。
#   kOverCurrent                  = 0x0040	#过流。
#   kSoftwareError                = 0x0080	#软件错误。
#   kTemperatureSensorError       = 0x0100	#温度传感器错误。
#   kPositionLimitExceeded        = 0x0200	#位置超限错误。
#   kInvalidJointID               = 0x0400	#关节ID非法。
#   kPositionTrackingError        = 0x0800	#位置跟踪错误。
#   kCurrentDetectionError        = 0x1000	#电流检测错误。
#   kBrakeOpenFailure             = 0x2000	#抱闸打开失败。
#   kPositionCommandStepWarning   = 0x4000	#位置指令阶跃警告。
#   kMultiTurnJointLostCount      = 0x8000	#多圈关节丢圈数。
#   kOtherErr                     = 0xF000	#通信丢帧
uint32              err_code              # 系统错误码