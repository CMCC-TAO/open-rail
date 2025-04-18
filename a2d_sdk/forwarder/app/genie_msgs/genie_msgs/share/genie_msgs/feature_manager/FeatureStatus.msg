std_msgs/Header     header
uint8               work_mode           # 0: uninit, 1: EOL, 2: Debug, 3: Test, 4: DataAcq, 5: Inference, 6: SDK, 7: OTA, 8: DEMO
uint8               feature_status      # 0: uninit, 1: initilizing, 2: running, 3: stopping, 4: error