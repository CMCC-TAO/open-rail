import ctypes
import os
from typing import Optional, Tuple

class CosineImageSubscriber:
    """Cosine Bus Python封装的图像订阅器类"""
    
    def __init__(self, topic: str):
        # 加载动态库
        lib_path = os.getenv('COSINE_BUS_PY_LIB', 'libcosine_bus_py.so')
        self._lib = ctypes.CDLL(lib_path)
        
        # 设置函数参数和返回类型
        self._lib.create_subscriber.argtypes = [ctypes.c_char_p]
        self._lib.create_subscriber.restype = ctypes.c_void_p
        
        self._lib.destroy_subscriber.argtypes = [ctypes.c_void_p]
        self._lib.destroy_subscriber.restype = None
        
        self._lib.read_latest_frame.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), 
                                              ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_void_p)]
        self._lib.read_latest_frame.restype = ctypes.c_bool
        
        self._lib.end_frame_read.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self._lib.end_frame_read.restype = None
        
        # 创建订阅器实例
        self._handle = self._lib.create_subscriber(topic.encode())
        if not self._handle:
            raise RuntimeError("Failed to create subscriber")
            
    def __del__(self):
        if hasattr(self, '_handle') and self._handle:
            self._lib.destroy_subscriber(self._handle)
            
    def read_latest_frame(self) -> Optional[Tuple[bytes, int, int]]:
        """读取最新的图像帧
        
        Returns:
            如果成功，返回(数据, 实际大小, 消息句柄)的元组
            如果失败，返回None
        """
        data_ptr = ctypes.c_void_p()
        size = ctypes.c_int()
        msg_handle = ctypes.c_void_p()
        
        if self._lib.read_latest_frame(self._handle, ctypes.byref(data_ptr), ctypes.byref(size), ctypes.byref(msg_handle)):
            # 从指针创建bytes对象
            buffer = (ctypes.c_char * size.value).from_address(data_ptr.value)
            data = bytes(buffer)
            return data, size.value, msg_handle.value
        return None
        
    def end_frame_read(self, msg_handle: int):
        """结束帧数据读取
        
        Args:
            msg_handle: 消息句柄，通过read_latest_frame获取
        """
        if msg_handle:
            self._lib.end_frame_read(self._handle, ctypes.c_void_p(msg_handle))