from ml_collections import ConfigDict

# 点心
def get_robotB_config():
    config = ConfigDict()
    config.robot_name = "ARM_B"
    config.reset_pose = {
        "default": [0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pick_custardbun": [0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pick_shrimpdumpling": [0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "place_custardbun": None, # None表示不复位
        "place_shrimpdumpling": None,
    }
    config.thre_progress_finish = {
        "default": 0.9,
        "pick_custardbun": 0.9,
        "pick_shrimpdumpling": 0.9,
        "place_custardbun": 0.9,
        "place_shrimpdumpling": 0.9,
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
    config.reset_pose = {
        "default": [0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pour_water_greentea": [0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "pour_water_blacktea": [0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "place_greentea": [0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
        "place_blacktea": [0] * 14 + [0, 0] + [0.0, 0.4363] + [0.2967, 20.0] + [0.0, 0.0],
    }
    config.thre_progress_finish = {
        "default": 0.9,
        "pour_water_greentea": 0.9,
        "pour_water_blacktea": 0.9,
        "place_greentea": 0.9,
        "place_blacktea": 0.9,
    }
    config.language = {
        "default": "",
        "pour_water_greentea": "Use the left arm to grasp the teapot of green tea first, and then carefully pour the green tea into the cup",
        "pour_water_blacktea": "Use the right arm to grasp the teapot of black tea first, and then carefully pour the black tea into the cup",
        "place_greentea": "Place the green tea cup on the tray with left arm",
        "place_blacktea": "Place the black tea cup on the tray with right arm",
    }
    return config

# 水果
def get_robotD_config():
    config = ConfigDict()
    config.robot_name = "ARM_D"
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
        "default": 0.9,
        "pick_apple": 0.9,
        "pick_orange": 0.9,
        "pick_peach": 0.9,
        "place_apple": 0.9,
        "place_orange": 0.9,
        "place_peach": 0.9,
        "open_door": 0.9,
        "close_door": 0.9,
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

def get_dispatch_config():
    target = 'robotD'
    config = ConfigDict()
    config.server_task_address = "tcp://192.168.1.122:5555"
    config.server_response_address = "tcp://192.168.1.122:5556"
    if target == 'robotB':
        config.robot = get_robotB_config()
    elif target == 'robotC':
        config.robot = get_robotC_config()
    elif target == 'robotD':
        config.robot = get_robotD_config()
    return config
