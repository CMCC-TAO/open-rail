# TODO: 考虑移到调度系统服务端

from ml_collections import ConfigDict

# 点心
def get_robotB_config():
    config = ConfigDict()
    config.robot_name = "ARM_B"
    config.required_stable_count = 20
    config.thre_stability_ratio = 0.004
    config.reset_sleep = 0.0
    config.reset_pose = {
        "default": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 22.0] + [0.0, 0.0],
        "pick_custardbun": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 22.0] + [0.0, 0.0],
        "pick_shrimpdumpling": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 22.0] + [0.0, 0.0],
        "place_custardbun": None, # None表示不复位
        "place_shrimpdumpling": None,
    }
    config.thre_progress_finish = {
        "default": 0.94,
        "pick_custardbun": 0.94,
        "pick_shrimpdumpling": 0.94,
        "place_custardbun": 0.94,
        "place_shrimpdumpling": 0.94,
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
    config.required_stable_count = 20
    config.thre_stability_ratio = 0.004
    config.reset_sleep = 0.0
    config.reset_pose = {
        "default": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pick_cup_greentea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.5, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pick_cup_blacktea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.5, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pour_water_greentea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pour_water_blacktea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "place_greentea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "place_blacktea": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
    }
    config.thre_progress_finish = {
        "default": 0.94,
        "pick_cup_greentea": 0.94,
        "pick_cup_blacktea": 0.94,
        "pour_water_greentea": 0.94,
        "pour_water_blacktea": 0.94,
        "place_greentea": 0.94,
        "place_blacktea": 0.94,
    }
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
    config.required_stable_count = 20
    config.thre_stability_ratio = 0.004
    config.reset_sleep = 2.0
    config.reset_pose = {
        "default": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "pick_apple": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 52.0] + [0.0, 0.0],
        "pick_orange": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "pick_peach": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 2.0] + [0.0, 0.0],
        "place_apple": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [1.0, 0.0] + [0.9599, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "place_orange": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [1.0, 0.0] + [0.9599, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "place_peach": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [1.0, 0.0] + [0.9599, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "open_door": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
        "close_door": [-1.0738, 0.6108, 0.2796, -1.2836, 0.7301, 1.4947, -0.1875, 1.0743, -0.611 , -0.2796, 1.2839, -0.7304, -1.4953, 0.1876] + [0.0, 0.0] + [0.2094, 0.4363] + [0.0, 27.0] + [0.0, 0.0],
    }
    config.thre_progress_finish = {
        "default": 0.8,
        "pick_apple": 0.8,
        "pick_orange": 0.8,
        "pick_peach": 0.8,
        "place_apple": 0.8,
        "place_orange": 0.8,
        "place_peach": 0.8,
        "open_door": 0.8,
        "close_door": 0.8,
    }
    config.language = {
        "default": "",
        "pick_apple": "Grasp the round red apple out of the freezer with the left hand",
        "pick_orange": "Grasp the green orange out of the freezer with the left hand",
        "pick_peach": "Grasp the yellow peach out of the freezer with the left hand",
        "place_apple": "replay:PATH",
        "place_orange": "replay:PATH",
        "place_peach": "replay:PATH",
        "open_door": "replay:PATH",
        "close_door": "replay:PATH",
    }
    return config

def get_robotE_config():
    config = ConfigDict()
    config.robot_name = "ARM_E"
    config.required_stable_count = 20
    config.thre_stability_ratio = 0.004
    config.reset_sleep = 2.0
    config.reset_pose = {
        "default": [-1.0748, 0.6107, 0.2816, -1.2823, 0.7292, 1.4957, -0.1869, 1.0720, -0.6103, -0.2780, 1.2822, -0.7299, -1.4929, 0.1873] + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
    }
    config.thre_progress_finish = {
        "default": 0.94,
    }
    config.language = {
        "default": "",
        "pick_bread": "Grasp a piece of bread out of the freezer with the left hand, and put it into the toaster.",
        "place_plate": "replay:PATH",
    }
    return config

def get_dispatch_config():
    target = 'robotC'
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
