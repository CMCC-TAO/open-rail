import zmq
import json
import pickle
from ml_collections import ConfigDict

class ZMQServer():
    def __init__(self, config: ConfigDict):
        # 初始化ZMQ客户端，传入配置字典
        self.config = config
        self.context = zmq.Context()
        # 创建ROUTER套接字，除了ROUTER还有很多其他模式，比如PAIR一对一模式
        self.router = self.context.socket(zmq.ROUTER)
        # self.router.setsockopt(zmq.SNDTIMEO, 5000)  # 5秒超时
        self.router.setsockopt(zmq.SNDHWM, 1)  # 设置发送缓冲区为1条消息
        self.router.bind(config.server_addr)
        self.client_id = None # 客户端标识 TODO： 支持多客户端并发请求
        print(f'ZMQ服务端已启动，连接地址为: {config.server_addr}')

    def recvMessage(self):
        try:
            # 接收消息（阻塞），ROUTER套接字接收消息时会包含发送者的标识和多部分消息
            parts = self.router.recv_multipart()
            self.client_id = parts[0] # 0是客户端标识
            message = {}
            if len(parts) >= 2:
                message['data'] = pickle.loads(parts[1]) # 1是二进制数据
                message['meta'] = json.loads(parts[2].decode('utf8')) # 2是元数据JSON
            # print(f"收到消息: {message_obj.keys()}")
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
            # client_id = self.client_identities.get(Config.MAIN_CLIENT_ID)
            if self.client_id is None:
                print("未找到client标识，无法发送消息")
                return
            # 图像send前需编码：_, img_encoded = cv2.imencode('.jpg', data), 收到需要解码: img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            data = pickle.dumps(data) # data字典转为字节流
            meta = json.dumps(meta).encode('utf8')
            self.router.send_multipart([self.client_id, data, meta], flags=zmq.NOBLOCK) # 非阻塞发送
        except Exception as e:
            print(f"发送消息时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def close(self):
        self.router.close()
        self.context.term()
        print(f'ZMQ服务端已关闭，连接地址为: {self.config.client_addr}')