#!/bin/zsh
# Script to run A2D SDK robot service
# Changes to a2d_sdk directory, sources environment, and starts robot service with copilot configuration
cd a2d_sdk
source env.zsh
python robot_service.py -s -c ./conf/copilot.pbtxt
cd ..