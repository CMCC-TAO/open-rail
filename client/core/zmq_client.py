import zmq
import json
import pickle
from ml_collections import ConfigDict

class ZMQClient():
    def __init__(self, config: ConfigDict):
        self.config = config
        self.context = zmq.Context()
        self.dealer = self.context.socket(zmq.DEALER)
        # self.dealer.setsockopt(zmq.SNDTIMEO, 5000)  # 5秒超时
        self.dealer.setsockopt(zmq.SNDHWM, 1)  # 设置发送缓冲区为1条消息
        self.dealer.connect(config.client_addr)
        print(f'ZMQ客户端已启动，连接地址为: {config.client_addr}')

    def recvMessage(self):
        try:
            # 阻塞接收，在线程中使用
            if self.dealer.poll() != 0:
                message = {}
                parts = self.dealer.recv_multipart() # 接收多部分消息
                if len(parts) >= 2:
                    message['data'] = pickle.loads(parts[0]) # 0是二进制数据
                    message['meta'] = json.loads(parts[1].decode('utf8')) # 1是元数据JSON
                    return message
                else:
                    print("返回数据有问题")
                    return None
        except Exception as e:
            print(f"接收消息时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def sendMessage(self, data, meta={}):
        try:
            # 图像send前需编码：_, img_encoded = cv2.imencode('.jpg', data), 收到需要解码: img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            data = pickle.dumps(data) # data字典转为字节流
            meta = json.dumps(meta).encode('utf8')
            self.dealer.send_multipart([data, meta], flags=zmq.NOBLOCK) # 非阻塞发送
        except Exception as e:
            print(f"发送消息时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def close(self):
        self.dealer.close()
        self.context.term()
        print(f'ZMQ客户端已关闭，连接地址为: {self.config.client_addr}')