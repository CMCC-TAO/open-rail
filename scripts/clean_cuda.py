import torch
import gc
print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA是否可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA版本: {torch.version.cuda}")
    print(f"设备名称: {torch.cuda.get_device_name(0)}")
gc.collect() # 清理Python垃圾
torch.cuda.empty_cache() # 清理CUDA缓存

# sudo lsof /dev/nvidia-uvm
# sudo fuser -v /dev/nvidia-uvm
# sudo kill -9 1231
# sudo rmmod nvidia_uvm
# sudo modprobe nvidia_uvm