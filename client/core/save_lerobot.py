import os
import numpy as np
from PIL import Image
import json
import cv2
import json
import time
import bisect
from ml_collections import ConfigDict
from collections import deque
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import threading
# 初始化固定长度队列
MAX_LEN = 900 
class LeRobotDatasetWriter:
    def __init__(self, save_config):
        """
        初始化数据存储目录，并创建相关文件夹。
        :param save_dir: 保存数据集的根目录
        """
        # with open(save_config, 'r') as f:
        #     self.config = json.load(f)
        self.config = save_config
        self.save_path = self.config["save_path"]
        
        self.save_meta_path = os.path.join(self.save_path,'meta')

        # 检查保存目录下是否有meta文件
        self.checkdir_and_update_config()
        # 返回info下面字典所有的key
        self.camera_name_list= []
        for key in self.config["info"]['features'].keys():
            if "cam" in key:
                self.camera_name_list.append(key)
        
        self.obs_time = deque(maxlen=MAX_LEN)
        self.state = deque(maxlen=MAX_LEN)
        self.action_list = deque(maxlen=10)
        self.action_time = deque(maxlen=10)
        self.action_align = deque(maxlen=MAX_LEN)
        self.start_write_time = None
        self.stop = False
        # 创建视频写入字典
        self.init_parquet_content()
        self.total_frames = self.config['info']['total_frames']
        self.counter = self.config['info']['total_episodes']
        
        self.episode_chunk = self.counter // self.config.info.chunks_size
        self.parquet_savepath = os.path.join(self.save_path,self.config.info.data_path.format(episode_chunk=self.episode_chunk,episode_index=self.counter))
        os.makedirs(os.path.dirname(self.parquet_savepath), exist_ok=True)
        self.save_video_path = os.path.join(self.save_path,'videos',f'chunk-{self.episode_chunk:03d}')
        self.save_video_path_list = []
        self.videos_writer = self.gener_video_write_dict()
        self.parquet_writer = pq.ParquetWriter(self.parquet_savepath, self.schema)
        self.parquet_list= []
        self.state_in_action_index= 0
        self.writer_thread = threading.Thread(target=self.write, daemon=True)
        self.writer_thread.start()
    def get_obs(self, obs_data):
        """
        处理观测数据，包括相机图像、机器人状态和时间帧。
        :param obs_data: 包含以下键的字典：
                    'type': string,
                    'loc_timestamp': int,
                    'obs': {
                        **obs_cams,
                        'state': numpyarray,
                        'annotation.human.task_description': string,
                    },
        """
        timestamp = obs_data['loc_timestamp']
        robot_state = obs_data['obs']
        obs_type = obs_data["type"]
        if len(self.obs_time)>0:
            assert self.obs_time[-1] < timestamp, \
            f"obs 时间戳不递增: 上一个={self.obs_time[-1]}, 当前={timestamp}"
        if self.start_write_time:
            self.obs_time.append(timestamp)
            self.state.append(robot_state)
            self.action_align.append(self.action_list.pop())
    def get_action(self, action_data):
        """
        处理动作数据。
        :param action_data: 包含以下键的字典：
                            - 'action': 动作值（例如关节力矩或目标位置）
                            - 'timestamp': 时间帧
        """
        timestamp = action_data['loc_timestamp']
        action = action_data['action']
        # obs_type = action_data["type"]
        if len(self.action_list)==0 and not self.start_write_time:
            self.start_write_time = timestamp
        if len(self.action_time)>0:
            assert self.action_time[-1] < timestamp, \
            f"action 时间戳不递增: 上一个={self.obs_time[-1]}, 当前={timestamp}"
        self.action_list.append(action)


    def write(self):
        """
        设置另一个线程用来写入数据，当self.start_write_time有数据时，则开始写入数据
        """
        # 写入meta.json
        print("waiting for start_write_time")
        while not self.start_write_time:
            time.sleep(0.1)
        frame_index = 0
        while not self.stop:
            if not self.state:
                # print("warning!! no state in self.state")
                continue
            current_save_state = self.state.popleft()
            state_time = self.obs_time.popleft()
            self.task_info = current_save_state['annotation.human.action.task_description']
            # aciton_index = self.find_closest_action(state_time,self.state_in_action_index)
            # if aciton_index == -1:
            #     continue
            # self.state_in_action_index = aciton_index
            # action = self.action_list[aciton_index]
            action = self.action_align.popleft()
            ##写入数据
            ##写入图片
            for camera_name in self.camera_name_list:
                self.videos_writer[camera_name].write(current_save_state[camera_name])
            ##写入parquet文件
            record = {
                'observation.state': current_save_state['state'].tolist(),
                'action': action.tolist(),
                'episode_index': self.counter,
                'frame_index': frame_index,
                'index': self.total_frames,
                'task_index': 0,
                'timestamp': 1/30 * frame_index,
            }
            self.parquet_list.append(record)
            frame_index+=1
            self.total_frames+=1
        self.counter += 1
        self.length = frame_index 
        self.total_frames -=1
        ## 根据self.start_write_time 去找最近的obs时间戳来开始存储数据

    def close(self):
        self.stop = True
        self.release_writers()
        # 释放资源
        while True:
            user_input = input("请输入 yes 保存数据，no 不保存: ").strip().lower()
            if user_input == 'yes':
                print("视频已保存至：{}".format(self.save_video_path))
                df = pd.DataFrame(self.parquet_list)
                table = pa.Table.from_pandas(df, schema=self.schema)
                ## 写入parquet
                self.parquet_writer.write_table(table)
                print(f"写入parquet文件成功，保存路径为: {self.parquet_savepath}")
                self.parquet_writer.close()

                self.write_meta_files()

                break
            elif user_input == 'no':
                for path in self.save_video_path_list:
                    if os.path.exists(path):
                        os.remove(path)
                if os.path.exists(self.parquet_savepath):
                    os.remove(self.parquet_savepath)
                print("已删除刚保存的视频文件。")
                break
                # 直接退出
            else:
                # 其他输入，提示重新输入
                print("输入无效，请重新输入。")
        

    def checkdir_and_update_config(self):
        """
        检查 self.save_meta_path 是否存在，若存在且包含 info.json、episodes.jsonl、tasks.jsonl，
        则用 info.json 的内容更新 self.config['info']
        """
        if  not os.path.exists(self.save_meta_path):
            self.save_data_path = os.path.join(self.save_path,'data','chunk-000')
            self.save_video_path = os.path.join(self.save_path,'videos','chunk-000')
            os.makedirs(self.save_meta_path, exist_ok=True)
            os.makedirs(self.save_data_path, exist_ok=True)
            os.makedirs(self.save_video_path, exist_ok=True)
            print(f"{self.save_meta_path} not exists, create it")
            return
        elif len(os.listdir(self.save_meta_path)) == 0:
            return
        required_files = ['info.json', 'episodes.jsonl', 'tasks.jsonl']
        missing_files = []

        for filename in required_files:
            file_path = os.path.join(self.save_meta_path, filename)
            if not os.path.exists(file_path):
                missing_files.append(filename)

        if missing_files:
            print(f"{self.save_meta_path}缺少以下必要文件: {', '.join(missing_files)}")
            assert False, "缺少必要文件"
            return

        # 读取 info.json 并更新 self.config['info']
        file_path = os.path.join(self.save_meta_path, 'info.json')
        with open(file_path, 'r') as file:
            data = json.loads(file.read())
        # print(f"data type: {type(data)}, content: {data}")
        self.config["info"] = ConfigDict(data,allow_dotted_keys=True)

        print("已成功用 meta files更新 self.config")
    
    def gener_video_write_dict(self):

        filename = f"{'episode'}_{self.counter:06d}.{'mp4'}"
        video_write_dict = {}
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        for camera_name in self.camera_name_list:
            shape_list = self.config['info']["features"][camera_name]["shape"]
            height, width = shape_list[0],shape_list[1]
            os.makedirs(os.path.join(self.save_video_path, camera_name), exist_ok=True)
            video_path = os.path.join(self.save_video_path, camera_name, filename)
            self.save_video_path_list.append(video_path)
            video_write_dict[camera_name] = cv2.VideoWriter(video_path, fourcc, 30.0, (width, height))
        return video_write_dict
    
    def init_parquet_content(self):
        self.schema = pa.schema([
        ('observation.state', pa.list_(pa.float32())),  # NumPy array -> list[float]
        ('action', pa.list_(pa.float32())),              # NumPy array -> list[float]
        ('episode_index', pa.int32()),
        ('frame_index', pa.int32()),
        ('index', pa.int32()),
        ('task_index', pa.int32()),
        ('timestamp', pa.float64())
         ])
    def find_closest_obs_index(self, target_time):
        # 使用二分查找快速找到最接近的 obs 起始位置
        times = [obs['timestamp'] for obs in self.obs_list]
        idx = bisect.bisect_left(times, target_time)
        return idx if idx < len(times) else -1

    def find_closest_action(self, target_time, start_idx=0,tolerance=0.01):
        # 在 action 列表中从指定位置开始查找最接近的时间戳
        for i in range(start_idx, len(self.action_time)):
            if self.action_time[i] >= target_time:
                return i
        return -1
    def release_writers(self):
        for writer in self.videos_writer.values():
            writer.release()
        print("All video writers released.")
    
    def write_meta_files(self):
        info_file_path = os.path.join(self.save_meta_path, 'info.json')
        self.config['info']["total_episodes"] += 1
        self.config['info']["total_frames"] = self.total_frames
        self.config['info']["total_videos"] += len(self.camera_name_list)
        self.config['info']["splits"]== {"test": f"0:{self.config['info']['total_episodes']+1}"}
        with open(info_file_path, 'w') as f:
            json.dump(self.config['info'].to_dict(), f, indent=2, default=str)

        print(f"info.json 已写入: {info_file_path}")

        # 写入 episodes.jsonl
        episodes_file_path = os.path.join(self.save_meta_path, 'episodes.jsonl')
        episodes_content = {
            "episode_index": self.config['info']["total_episodes"],
            "tasks": self.task_info,
            "length": self.length  
        }
        with open(episodes_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(episodes_content, ensure_ascii=False) + '\n')
        print(f"episodes.jsonl 已写入: {episodes_file_path}")

        # 写入 tasks.jsonl
        tasks_file_path = os.path.join(self.save_meta_path, 'tasks.jsonl')
        tasks_content = {
            "task_index": 0,
            "tasks": self.task_info
        }
        with open(tasks_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(tasks_content, ensure_ascii=False) + '\n')
        print(f"tasks.jsonl 已写入: {tasks_file_path}")

def generate_mock_observation(timestamp, frame_index):
    """
    模拟 obs_data 输入
    """
    state = np.random.rand(20).astype(np.float32)  # 7维状态
    image1 = (np.random.rand(480, 640, 3) * 255).astype(np.uint8)  # 240x320 RGB 图像
    image2 = (np.random.rand(480, 640, 3) * 255).astype(np.uint8)  # 240x320 RGB 图像
    image3 = (np.random.rand(480, 640, 3) * 255).astype(np.uint8)  # 240x320 RGB 图像
    obs_cams = {
        "cam.head": image1,
        "cam.hand_left": image2,
        "cam.hand_right": image3
    }

    return {
        "type": "observation",
        "loc_timestamp": timestamp,
        "obs": {
            **obs_cams,
            "state": state,
            "annotation.human.action.task_description": f"test_task_{frame_index}"
        }
    }
def generate_mock_action(timestamp):
    """
    模拟 action_data 输入
    """
    action = np.random.rand(20).astype(np.float32)  # 7维动作
    return {
        "type": "action",
        "loc_timestamp": timestamp,
        "action": action
    }


if __name__ == "__main__":
    print(f"当前工作路径: {os.getcwd()}")
    import sys
    # project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # print(f"项目根目录: {project_root}")
    sys.path.append('/home/rm/wxz/EmbodiedAI/vla_infer_2/vla_infer')
    from conf.config import get_client_config
    save_dir = "/home/rm/wxz/EmbodiedAI/lerobot/vla_infer/tools/test/1"
    # config = create_mock_config(save_dir)
    config = get_client_config()
    # 初始化 writer
    writer = LeRobotDatasetWriter(save_config=config.record)
    
    print("开始模拟数据写入...")

    start_time = time.time()

    # 模拟写入 100 帧 obs 和 200 个 action（action 频率更高）
    for i in range(100):
        obs_data = generate_mock_observation(start_time + i * 0.033, i)  # 约 30Hz
        writer.get_obs(obs_data)

        # 每帧都插入多个 action（约 200Hz）
        for j in range(2):
            action_data = generate_mock_action(start_time + i * 0.033 + j * 0.005)
            writer.get_action(action_data)

    print("等待写入完成...")
    time.sleep(2)  # 给线程时间处理剩余数据
    writer.close()

    print("测试完成，检查输出文件：")
    print(f"- 视频文件路径: {os.path.join(save_dir, 'videos')}")
    print(f"- Parquet 文件路径: {os.path.join(save_dir, 'data')}")
    print(f"- Meta 文件路径: {os.path.join(save_dir, 'meta')}")

    assert os.path.exists(os.path.join(save_dir, 'meta', 'info.json')), "info.json 未生成"
    assert os.path.exists(os.path.join(save_dir, 'meta', 'episodes.jsonl')), "episodes.jsonl 未生成"
    # assert os.path.exists(os.path.join(save_dir, 'data','chunk-000', 'episode_000000.parquet')), "Parquet 文件未生成"
    print("✅ 所有文件验证通过！")
