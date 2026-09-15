export CUDA_VISIBLE_DEVICES=0

python run_server.py \
--model_type tao \
--model_path /home/hewei/github/model/hand_action_unchanged/tao_v0d5_20260909_201322_n8_b64_s40000 \
--embodiment_tag unitree_g1 \
# --debug
