import os
import time
import argparse
import cosine_bus
import signal
import numpy as np

# 尝试导入OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Warning: OpenCV (cv2) is not available. Image saving feature will be disabled.")

def signal_handler(sig, frame):
    print("Received SIGINT, exiting...")
    os._exit(1)  # 使用 os._exit 强制退出

signal.signal(signal.SIGINT, signal_handler)

def main(topic, fps, save_path, save_image, discovery_uri, locator_ip):
    # 检查是否可以保存图像
    if save_image and not OPENCV_AVAILABLE:
        print("Error: Cannot save images because OpenCV is not available.")
        print("Please install OpenCV (cv2) if you want to save images.")
        return 1

    # 如果环境变量已经设置，则不重复设置
    if 'AORTA_DISCOVERY_URI' not in os.environ:
        os.environ['AORTA_DISCOVERY_URI'] = discovery_uri
    if 'LOCATOR_IP' not in os.environ:
        os.environ['LOCATOR_IP'] = locator_ip
    
    os.environ['AORTA_NETWORK_CHECK_TIMEOUT'] = "5"

    # 处理topic列表
    topics = [t.strip() for t in topic.split(",")]
    receivers = []
    for t in topics:
        print(f"topic={t}")
        receivers.append(cosine_bus.image_subscriber(t))
    
    # 处理保存路径
    save_paths = []
    if save_image:
        if not save_path:
            # 如果没有指定保存路径，使用当前路径
            save_paths = ["."] * len(receivers)
            print("No save path specified, using current directory")
        else:
            # 如果指定了保存路径，处理多路径情况
            save_paths = [path.strip() if path.strip() else "." for path in save_path.split(",")]
            # 如果路径数量不够，用最后一个路径补齐
            if len(save_paths) < len(receivers):
                save_paths.extend([save_paths[-1]] * (len(receivers) - len(save_paths)))
            # 如果路径数量过多，截断
            save_paths = save_paths[:len(receivers)]
        
        # 确保保存路径存在
        for path in save_paths:
            try:
                os.makedirs(path, exist_ok=True)
                print(f"Save path created/verified: {path}")
            except Exception as e:
                print(f"Error creating directory {path}: {e}")
                return 1
    
    interval = 1.0 / fps
    try:
        while True:
            for i, receiver in enumerate(receivers):
                packet = receiver.read_latest_frame()
                if packet is not None and packet.type == cosine_bus.PacketType.IMAGE:
                    # 获取图像信息
                    encoding = packet.encoding_format
                    color_format = packet.color_format
                    bit_depth = packet.bit_depth
                    width = packet.image_width
                    height = packet.image_height
                    image_data = packet.get_image_data()
                    
                    if image_data is not None:
                        print(f"Received image: topic={topics[i]} (fps={receiver.get_fps():.2f}), encoding={encoding}, "
                              f"color_format={color_format}, bit_depth={bit_depth}, width={width}, height={height}")
                        print(f"Packet info: seq={packet.sequence_number}, "
                              f"send_ts={packet.send_timestamp}, "
                              f"recv_ts={packet.recv_timestamp}, "
                              f"source_ts={packet.source_timestamp}")
                        
                        # 获取延时统计信息（使用5秒窗口）
                        latency_stats = receiver.get_latency_stats(5.0)
                        print(f"Latency stats (5s window): max={latency_stats['max_latency_ms']:.2f}ms, "
                              f"avg={latency_stats['avg_latency_ms']:.2f}ms, "
                              f"p99={latency_stats['p99_latency_ms']:.2f}ms, "
                              f"p99.9={latency_stats['p999_latency_ms']:.2f}ms, "
                              f"p99.99={latency_stats['p9999_latency_ms']:.2f}ms")
                        
                        if save_image and OPENCV_AVAILABLE:
                            timestamp = int(time.time() * 1000)
                            save_file = os.path.join(save_paths[i], f"image_{timestamp}.png")
                            
                            try:
                                # 根据编码格式处理图像数据
                                if encoding == cosine_bus.EncodingFormat.JPEG or encoding == cosine_bus.EncodingFormat.PNG:
                                    frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                                    if frame is not None:
                                        cv2.imwrite(save_file, frame)
                                        print(f"Saved compressed image to {save_file}")
                                    else:
                                        print(f"Failed to decode {encoding} image")
                                elif encoding == cosine_bus.EncodingFormat.UNCOMPRESSED:
                                    # 根据颜色格式处理图像数据
                                    if color_format in [cosine_bus.ColorFormat.RGB, cosine_bus.ColorFormat.BGR]:
                                        frame = image_data.reshape(height, width, 3)
                                        if color_format == cosine_bus.ColorFormat.RGB:
                                            # OpenCV使用BGR格式，需要转换
                                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                                        cv2.imwrite(save_file, frame)
                                        print(f"Saved {color_format} image to {save_file}")
                                    else:
                                        print(f"Unsupported color format: {color_format}")
                            except Exception as e:
                                print(f"Failed to save image: {e}")
                else:
                    print("No valid image packet received")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Image subscription is terminated.")
        return 0

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="/camera/image", help="Topic name(s), separated by commas")
    parser.add_argument("--fps", type=int, default=10, help="Frame rate")
    parser.add_argument("--save_path", type=str, default="", help="Save path(s), separated by commas, same length as topic")
    parser.add_argument("--save_image", action="store_true", help="Whether to save received images (requires OpenCV)")
    parser.add_argument("--discovery_uri", type=str, default="10.42.0.101:2379", help="Discovery URI")
    parser.add_argument("--locator_ip", type=str, default="10.42.0.102", help="Use local ip as locator ip")
    args = parser.parse_args()
    return main(args.topic, args.fps, args.save_path, args.save_image, args.discovery_uri, args.locator_ip)

if __name__ == "__main__":
    cli()