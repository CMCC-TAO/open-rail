# TODO: 考虑移到调度系统服务端

from ml_collections import ConfigDict

# 点心
def get_robotB_config():
    config = ConfigDict()
    config.robot_name = "ARM_B"
    config.reset_pose_start = {
        "default": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 22.0] + [0.0, 0.0],
        "pick_custardbun": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 22.0] + [0.0, 0.0],
        "pick_shrimpdumpling": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 22.0] + [0.0, 0.0],
        "place_custardbun": None, # None表示不复位
        "place_shrimpdumpling": None,
    }
    config.reset_pose_finish = {
        "default": None,
        "pick_custardbun": None,
        "pick_shrimpdumpling": None,
        "place_custardbun": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 22.0] + [0.0, 0.0],
        "place_shrimpdumpling": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 22.0] + [0.0, 0.0],
    }
    config.sleep_reset_pose = {
        "default": [0.0, 0.0],
        "pick_custardbun": [0.0, 0.0],
        "pick_shrimpdumpling": [0.0, 0.0],
        "place_custardbun": [0.0, 0.0],
        "place_shrimpdumpling": [0.0, 0.0],
    }
    config.thre_progress = {
        "default": [0.94, 20, 0.05],
        "pick_custardbun": [0.94, 20, 0.05],
        "pick_shrimpdumpling": [0.94, 20, 0.05],
        "place_custardbun": [0.94, 20, 0.05],
        "place_shrimpdumpling": [0.94, 20, 0.05],
    }
    config.language = {
        "default": "",
        "pick_custardbun": "[PRIMARY_ARM=LEFT] Use the left gripper to  pick up the topmost steamer on the left",
        "pick_shrimpdumpling": "[PRIMARY_ARM=RIGHT] Use the right gripper to  pick up the topmost steamer on the right",
        "place_custardbun": "[PRIMARY_ARM=LEFT] Use the left gripper to  place the topmost steamer on the plate",
        "place_shrimpdumpling": "[PRIMARY_ARM=RIGHT] Use the right gripper to  place the topmost steamer on the plate",
    }
    return config

# 倒茶
def get_robotC_config():
    config = ConfigDict()
    config.robot_name = "ARM_C"
    # 子任务开始前的复位姿态, None表示不复位
    config.reset_pose_start = {
        "default": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pick_cup_greentea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.436, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pick_cup_blacktea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [-0.436, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pour_water_greentea": None,
        "pour_water_blacktea": None,
        "place_greentea": None,
        "place_blacktea": None,
    }
    # 子任务结束后的复位姿态
    config.reset_pose_finish = {
        "default": None,
        "pick_cup_greentea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pick_cup_blacktea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pour_water_greentea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pour_water_blacktea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "place_greentea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "place_blacktea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
    }
    # 子任务复位后的sleep时间：[0]reset_pose_start, [1]reset_pose_finish
    config.sleep_reset_pose = {
        "default": [0.0, 0.0],
        "pick_cup_greentea": [2.0, 2.0],
        "pick_cup_blacktea": [2.0, 2.0],
        "pour_water_greentea": [0.0, 0.0],
        "pour_water_blacktea": [0.0, 0.0],
        "place_greentea": [0.0, 0.0],
        "place_blacktea": [0.0, 0.0],
    }
    # 进度预测相关，3个条件都满足才会结束。[0]开始稳定性检测阈值, [1]稳定性计数, [2]变异系数阈值
    config.thre_progress = {
        "default": [0.94, 20, 0.01],
        "pick_cup_greentea": [0.94, 20, 0.06],
        "pick_cup_blacktea": [0.94, 20, 0.06],
        "pour_water_greentea": [0.94, 20, 0.04],
        "pour_water_blacktea": [0.94, 20, 0.04],
        "place_greentea": [0.9, 20, 0.07],
        "place_blacktea": [0.9, 20, 0.07],
    }
    # 子任务语言指令，replay:PATH表示进行轨迹播放
    config.language = {
        "default": "",
        "pick_cup_greentea": "[PLACE_CUP_ON_TABLE_LEFT] [LEFT_ARM] Using the left arm, place the cup onto the table.",
        "pick_cup_blacktea": "[PLACE_CUP_ON_TABLE_RIGHT] [RIGHT_ARM] With the right arm, place the cup onto the table.",
        "pour_water_greentea": "[POUR_GREEN_TEA] [LEFT_ARM] Using the left arm, lift the green-tea pot and pour into the cup.",
        "pour_water_blacktea": "[POUR_BLACK_TEA] [RIGHT_ARM] With the right arm, pick up the black-tea pot and pour into the cup.",
        "place_greentea": "[PLACE_GREEN_TEA_CUP] [LEFT_ARM] The left arm transfers the green-tea cup onto the tray.",
        "place_blacktea": "[PLACE_BLACK_TEA_CUP] [RIGHT_ARM] The right arm places the black-tea cup onto the tray.",
    }
    return config

# 水果
def get_robotD_config():
    config = ConfigDict()
    config.robot_name = "ARM_D"
    config.reset_pose_start = {
        "default": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "pick_apple": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 52.0] + [0.0, 0.0],
        "pick_dragon_fruit": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "pick_banana": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 2.0] + [0.0, 0.0],
        "place_apple": None,
        "place_dragon_fruit": None,
        "place_banana": None,
        "open_door": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "close_door": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
    }
    config.reset_pose_finish = {
        "default": None,
        "pick_apple": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [1.0, 0.0] + [0.9599, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "pick_dragon_fruit": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [1.0, 0.0] + [0.9599, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "pick_banana": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [1.0, 0.0] + [0.9599, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "place_apple": None,
        "place_dragon_fruit": None,
        "place_banana": None,
        "open_door": None,
        "close_door": None,
    }
    config.sleep_reset_pose = {
        "default": [0.0, 0.0],
        "pick_apple": [3.0, 2.0],
        "pick_dragon_fruit": [3.0, 2.0],
        "pick_banana": [3.0, 2.0],
        "place_apple": [0.0, 0.0],
        "place_dragon_fruit": [0.0, 0.0],
        "place_banana": [0.0, 0.0],
        "open_door": [0.0, 0.0],
        "close_door": [0.0, 0.0],
    }
    config.thre_progress = {
        "default": [0.8, 20, 0.03],
        "pick_apple": [0.8, 20, 0.03],
        "pick_dragon_fruit": [0.8, 20, 0.03],
        "pick_banana": [0.8, 20, 0.03],
        "place_apple": [0.8, 20, 0.03],
        "place_dragon_fruit": [0.8, 20, 0.03],
        "place_banana": [0.8, 20, 0.03],
        "open_door": [0.8, 20, 0.03],
        "close_door": [0.8, 20, 0.03],
    }
    config.language = {
        "default": "",
        "pick_apple": "Grasp red apple (top)",
        "pick_dragon_fruit": "Grasp dragon fruit (mid)",
        "pick_banana": "Grasp yellow banana (bottom)",
        "place_apple": "replay:PATH",
        "place_dragon_fruit": "replay:PATH",
        "place_banana": "replay:PATH",
        "open_door": "replay:PATH",
        "close_door": "replay:PATH",
    }
    return config

# 面包
def get_robotE_config():
    config = ConfigDict()
    config.robot_name = "ARM_E"
    config.reset_pose_start = {
        "default": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pick_rack_to_toaster": None,
        "pick_bread": None,
        "place_bread": None,
    }
    config.reset_pose_finish = {
        "default": None,
        "pick_rack_to_toaster": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pick_bread": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "place_bread": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
    }
    config.sleep_reset_pose = {
        "default": [0.0, 0.0],
        "pick_rack_to_toaster": [0.0, 0.0],
        "pick_bread": [0.0, 0.0],
        "place_bread": [0.0, 0.0],
    }
    config.thre_progress = {
        "default": [0.94, 20, 0.03],
        "pick_rack_to_toaster": [0.94, 20, 0.03],
        "pick_bread": [0.94, 20, 0.05],
        "place_bread": [0.94, 20, 0.05],
    }
    config.language = {
        "default": "",
        "pick_rack_to_toaster": "[PICK_BREAD_INTO_TOASTER] [RIGHT_ARM] With right gripper, pick up the bread and put it into the green toaster. Then push the orange lever down.",
        "pick_bread": "[PICK_BREAD_INTO_PLATE] [LEFT_ARM] With left gripper, pick up the bread from the conveyor and place it on the orange plate on the left.",
        "place_bread": "[PICK_PLATE_ONTO_TRAY] [LEFT_ARM] Pick up the orange plate containing bread on the left and place it on the tray in front.",
    }
    return config

def get_dispatch_config(target='robotC'):
    config = ConfigDict()
    config.server_task_address = "tcp://192.168.0.89:5555"
    config.server_response_address = "tcp://192.168.0.89:5556"
    if target == 'robotB':
        config.robot = get_robotB_config()
    elif target == 'robotC':
        config.robot = get_robotC_config()
    elif target == 'robotD':
        config.robot = get_robotD_config()
    elif target == 'robotE':
        config.robot = get_robotE_config()
    return config
