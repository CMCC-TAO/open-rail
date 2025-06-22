
std_msgs/Header     res_header
# 0: success, 1: 控制器返回错误或参数错误 2:数据发送失败
# 3: 数据接收失败或超时 4:返回值解析失败 5:程序发生异常 6:不支持的手臂标定类型
# 7: 未知错误 8: 不支持的标定类型 9:不支持的标定cmd
uint8               exec_result    