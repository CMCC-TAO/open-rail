#!/bin/bash

tmux capture-pane -t vla_action_sim -p -S - > /tmp/action_server.log

cat /tmp/action_server.log
