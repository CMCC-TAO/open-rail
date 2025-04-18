std_msgs/Header     header
float32             energy        # 单位: %, 0~100 @TODO: 和供应商统一
float32             voltage       # 单位: V
float32             current       # 单位: A
float32             capacity      # 单位: Ah
float32             temperature   # 单位: ℃
uint8               status        # 0: unknown, 1: charging, 2: discharging, 3: not charging, 4: full, 5: empty
