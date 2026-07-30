export CUDA_VISIBLE_DEVICES=0

python run_server.py \
--model_type tao \
--model_path /home/hewei/github/model/model_hunhe/tao_v0_20260630_023503_n8_b64_s10000 \
--embodiment_tag unitree_g1 \
# --debug
