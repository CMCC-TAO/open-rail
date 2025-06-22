std_msgs/Header header

builtin_interfaces/Time measuring_ts   # 触发时间戳（PTP时钟）
builtin_interfaces/Time publish_ts     # 接收时间戳
string frame_id                        # 地图参考坐标系（如 "map"）

# 地图元信息
float32 resolution                     # 米/格
uint32 width
uint32 height

# 地图原点
geometry_msgs/Pose origin              # 原点 pose（包含 position 和 quaternion orientation）

# 原点姿态（欧拉角表示，可选补充信息）
geometry_msgs/Vector3 orientation_euler

# 地图栅格数据
int8[] data                            # 栅格地图数据，长度 = width * height
                                       # -1: 未知，0: 空闲，100: 障碍