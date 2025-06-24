#!/bin/zsh
cd a2d_sdk
source env.zsh
# python robot_service.py -s -c ./conf/hybrid_deploy_depth53.pbtxt
python robot_service.py -s -c ./conf/copilot.pbtxt
cd ..