#提供通话连接的服务。 
#服务名: /voice/call_req

uint32 CALL_CONNECT_START = 1
uint32 CALL_CONNECT_FINISH = 2

std_msgs/Header     header
uint32 call_req      # 1. 请求开始通话  2. 请求结束通话
string requester       # 1. # 请求方的名称
