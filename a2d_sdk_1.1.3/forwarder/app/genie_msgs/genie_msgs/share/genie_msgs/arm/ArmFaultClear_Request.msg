# Provide arm fault clear cmd services
# service name: /hal/arm_fault_clear

std_msgs/Header     header
uint32              arm_sel       # 0 = left, 1 = right, 2 = both
