# service name: /hal/arm_force_cal
std_msgs/Header     header
int32               cal_cmd       # 1: 标定六维力数据
uint32              force_id      # 0x00 = left | end, 0x01 = right | end, 0x02 = both
int8                count
float32[]           joint
bool                block         #暂时未用，默认阻塞
