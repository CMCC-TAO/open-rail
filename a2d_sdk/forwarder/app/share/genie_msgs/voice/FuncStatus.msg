#语音交互状态信息
# 消息名：/voice/func_status
std_msgs/Header     header
uint32 func_status   #0: 空闲， 1.1. 电话模式（接管mic+扬声器）2.2. 语音唤醒 + 知识库问答, 3. 语音唤醒 + ASR, 4. 语音播报 5. 多轮语音交互 6. 音频播放  9.异常
string requester  
uint32 publish_ptp_ts
string publisher_id
uint32 counter
uint32 publish_ts