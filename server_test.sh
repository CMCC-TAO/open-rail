export CUDA_VISIBLE_DEVICES=0

python run_server.py \
--model_type tao \
--model_path /home/ttt/Desktop/model_tao/state_is_action_hand_to_grasp_no3_robot_20000/tao_v0d5_20260902_190159_n8_b64_s20000 \
--embodiment_tag unitree_g1 \
# --debug
