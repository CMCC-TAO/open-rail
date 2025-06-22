# frame id 无用, timestamp发送时间
std_msgs/Header header 

# 控制组信息： std::vector<RetargetInfo> [group]
# 对于单点RetargetInfo有一些要求:
# group_id在不同group内不能一样
RetargetInfo[] retarget_groups

# lifetime 指令超过lifetime 速度指令会停止 
float64 lifetime