std_msgs/Header     header
uint8               fim_fw

# fim_fw_byte bit-wise
# bit0: meta.json丢失
# bit1: 相机标定文件损坏
# bit2: nvme磁盘空间不足
# bit3: nvme未挂载
uint32              err_code_byte