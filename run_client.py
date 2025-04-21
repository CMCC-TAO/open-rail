import time
from conf.config import get_client_config
from client.robots.a2d.robot_a2d import RobotA2D
from client.core.realtime_data_manager import RealtimeDataManager
from client.core.vla_client import VLAClient

if __name__ == "__main__":
    config = get_client_config()
    # print(config)
    robot = RobotA2D(config.observer, config.controller)
    rdm = RealtimeDataManager(config.rdm)
    vla_client = VLAClient(config, rdm, robot)
    
    try:
        while True:
            cmd = input("请输入指令：")
            # print(f'输入的指令是：{cmd}')
            if cmd == 'exit':
                break
            elif cmd == 'start' or cmd == 'run':
                vla_client.startObserve()
            elif cmd == 'stop':
                print("停止")
            elif cmd == 'exit':
                print("退出程序")
                break
            else:
                print('未知指令, 请使用一下指令：')
                print(' start/run: 启动程序')
                print(' stop: 结束程序')
                print(' exit: 推出程序')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("程序被中断")
    finally:
        pass
        # robot.close()
        # vla_client.close()