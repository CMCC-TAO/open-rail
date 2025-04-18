string name                    # 控制器名称（例如："left" 或 "right"）
uint32 id                      # 控制器ID

bool key_one                   # 按键1状态
bool key_two                   # 按键2状态
float64 hand_trig              # 手柄扳机值
float64 index_trig             # 食指扳机值
float64 axis_x                 # 摇杆X轴值
float64 axis_y                 # 摇杆Y轴值
bool axis_click                # 摇杆按下
geometry_msgs/Vector3 position # 控制器位置
geometry_msgs/Quaternion orientation # 控制器旋转（四元数）
