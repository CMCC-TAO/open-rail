# /hal/slam/mapping_Control
std_msgs/Header     header
int32 control         # 1 开始建图 2 停止建图
bool save_map       # 当contol 为 2(停止建图时使用)时 true 保存地图  false 丢弃地图
string map_name     # 地图名称 
