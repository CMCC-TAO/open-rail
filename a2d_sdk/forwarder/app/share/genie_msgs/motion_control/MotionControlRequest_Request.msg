std_msgs/Header header # frame id 无用, timestamp发送时间

# 控制组信息
# 对于单点RetargetInfo有一些要求:
# group_id在不同group内不能一样
RetargetInfo[] retarget_groups
# 0-1  1最快
float64 speed_scale

