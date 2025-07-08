### 安装A2D SDK

确认PC与A2D的网络连接后。执行以下命令，部署GDK环境。

```bash
curl -sSL http://10.42.0.101:8849/install.sh | bash
```

注意，拉取安装完sdk后请执行：

```bash
cd a2d_sdk
source env.sh
# 切换SDK工作模式
# python3 robot_service.py -s -c ./conf/hybrid_deploy_depth53.pbtxt # 旧版
python3 robot_service.py -s -c ./conf/copilot.pbtxt
```
