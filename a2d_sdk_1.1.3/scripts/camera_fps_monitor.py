import cosine_bus
import sys
from a2d_sdk.robot import CosineCamera
import time

def monitor_camera_fps(camera_names, update_interval=1.0):
    """
    监控指定相机的帧率
    Args:
        camera_names: 相机主题名称列表
        update_interval: 更新间隔（秒）
    """
    # 初始化相机组
    camera_group = CosineCamera(camera_names)
    
    print("开始监控相机帧率...")
    print("按 Ctrl+C 退出")
    
    try:
        while True:
            # 获取并打印每个相机的帧率
            print("\n" + "="*50)
            print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            for camera_name in camera_names:
                fps = camera_group.get_fps(camera_name)
                print(f"{camera_name.split('/')[-1]}: {fps:.2f} FPS")
            
            # 等待指定的更新间隔
            time.sleep(update_interval)
            
    except KeyboardInterrupt:
        print("\n停止监控")

if __name__ == "__main__":
    # 定义要监控的相机列表
    camera_names = [
        "/camera/head_color",
        "/camera/hand_left_color",
        "/camera/hand_right_color",
        "/camera/head_depth",
    ]
    # 接收传入的相机列表，没有传入则使用默认列表
    if len(sys.argv) > 1:
        camera_names = sys.argv[1].split(',')
    
    # 开始监控
    monitor_camera_fps(camera_names) 