std_msgs/Header     header
bool                controlled               # true表示正在控制状态
uint32              type          # 0 未知类型， 1:灵巧手， 2:夹爪
string[]            name          # 关节名
MotorState[]        end_state    # 末端状态