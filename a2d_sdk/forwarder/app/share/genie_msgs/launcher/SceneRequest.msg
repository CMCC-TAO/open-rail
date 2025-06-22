std_msgs/Header header

# 0: 场景切换
# 1: 加载某个特定场景
# 2: 重启APP
# 3: 删除某个APP
# 4: 重启某个场景
uint8 SWITCH=0
uint8 LOAD=1
uint8 RESTART_APP=2
uint8 REMOVE_APP=3
uint8 RESTART_SCENE=4
uint8 command

# 作为唯一标识，匹配request和respinse
string uuid
string detail