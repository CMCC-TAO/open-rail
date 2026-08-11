export CUDA_VISIBLE_DEVICES=0

python run_server.py \
--model_type tao \
--model_path /home/ttt/Desktop/model_tao/water_cola_model_0d5/tao_v0d5_20260809_124125_n8_b64_s10000 \
--embodiment_tag unitree_g1 \
# --debug
