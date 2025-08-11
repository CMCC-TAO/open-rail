import numpy as np
import pandas as pd
import argparse
import os
import sys
import time
import cv2
from pathlib import Path
import matplotlib.pyplot as plt
try:
    import zarr
except:
    pass

'''
# Different models need to modify model path and obs mapping at TODO locations in the code
python vis_eval.py \
--model_path /hy0505/checkpoints/gr00t_finetune/pickbottle_499_chunk64_20250507_192258_b24/checkpoint-60000 \
--gt_root /hy0505/dataset/A2d_zyhy_data/gr00t/task_158284_depth_test/task_158284_test \
--lookahead_idx 64 \
--episode_id 0 \
--chunk_id 0 \
--joint_dim 16 \
--dt_length -1 \
--split_ids 0-7,7-14,14-15 \
--language 'pick bottle into the box' \
--note ''
'''
def main(args):
    """Main function for VLA model evaluation.
    
    Args:
        args: Command line arguments containing model path, data paths, and evaluation parameters.
    """
    # Add project root directory to system path
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    # TODO: Modify model path
    from server.models.gr00t import gr00t_n1_5
    model = gr00t_n1_5.ModelVLA({'model_path': args.model_path})  # model

    parquet_file = f'{args.gt_root}/data/chunk-{str(args.chunk_id).zfill(3)}/episode_{str(args.episode_id).zfill(6)}.parquet'
    print(f"Loading gt data: {parquet_file}...")
    df_gt = pd.read_parquet(parquet_file, columns=['action', 'observation.state'])
    if df_gt is None:
        print(f"Failed to load gt data, please check file path: {parquet_file}")
        return
    depth_array = None
    depth_file = f'{args.gt_root}/videos/chunk-{str(args.chunk_id).zfill(3)}/observation.images.cam_top_depth/episode_{str(args.episode_id).zfill(6)}.zarr'
    try:
        print(f"Loading depth data: {depth_file}...")
        depth_array = zarr.open_array(depth_file, mode='r')
    except:
        print(f"Failed to load depth data, please check file path: {depth_file}")
    # Get cam data
    cam_frames = {}
    cameras = ['top_head', 'hand_left', 'hand_right']
    for name in cameras:
        cam_frames[name] = []
        video_path = f'{args.gt_root}/videos/chunk-{str(args.chunk_id).zfill(3)}/observation.images.{name}/episode_{str(args.episode_id).zfill(6)}.mp4'
        print(f"Loading cam.{name} data: {video_path}...")
        capture = cv2.VideoCapture(video_path)
        while True:
            ret, frame = capture.read()
            if not ret:
                break
            cam_frames[name].append(frame)
        capture.release()
    print(f"gt data length: {len(df_gt)}, cam length: {len(cam_frames['top_head'])}")

    dt_length = min(len(df_gt), args.dt_length) if args.dt_length > 0 else len(df_gt)
    joint_dim = args.joint_dim
    x_gt_vals = [[] for _ in range(joint_dim)]
    y_action_vals = [[] for _ in range(joint_dim)]
    y_state_vals = [[] for _ in range(joint_dim)]
    x_pred_vals = [[] for _ in range(joint_dim)]
    y_pred_vals = [[] for _ in range(joint_dim)]
    x_trans_vals = [[] for _ in range(joint_dim)]
    y_trans_vals = [[] for _ in range(joint_dim)]
    gripper_vmin, gripper_vmax = 35, 120
    chunk_size = 0
    for ind, value in enumerate(df_gt.values):
        if ind > dt_length:
            break
        for joint_idx in range(joint_dim):
            y_action_vals[joint_idx].append(float(value[0][joint_idx]))
            state_val = float(value[1][joint_idx])
            if joint_idx >= joint_dim - 2:
                state_val = (state_val - gripper_vmin) / (gripper_vmax - gripper_vmin) # norm
            y_state_vals[joint_idx].append(state_val)
            x_gt_vals[joint_idx].append(ind)
        if ind % args.lookahead_idx == 0:
            # TODO: Different models modify obs mapping here, consistent with obs in __main__ of vla_model.py
            obs = {
                'cam.head': cam_frames[cameras[0]][ind], # (480, 640, 3)
                'cam.hand_left': cam_frames[cameras[1]][ind], # (480, 640, 3)
                'cam.hand_right': cam_frames[cameras[2]][ind], # (480, 640, 3)
                'cam.depth.head': depth_array[ind] if depth_array is not None else None, # (480, 640)
                'state': np.array(value[1]), # (20,)
                'language': [args.language],
                # 'language': ['Perform the default behavior.'],
            }
            result = model.infer([{'obs': obs, 'ref_timestamp': []}])
            chunk_size = result['pred_action'].shape[0]
            assert args.lookahead_idx <= chunk_size, f"lookahead_idx({args.lookahead_idx}) must be less than or equal to chunk_size({chunk_size})"
            for joint_idx in range(joint_dim):
                for i in range(args.lookahead_idx):
                    y_pred_vals[joint_idx].append(float(result['pred_action'][i, joint_idx]))
                    x_pred_vals[joint_idx].append(ind + i)
                x_trans_vals[joint_idx].append(ind)
                y_trans_vals[joint_idx].append(float(result['pred_action'][0, joint_idx]))

    max_cols = 1
    rows = (joint_dim + max_cols - 1) // max_cols
    fig, axes = plt.subplots(rows, max_cols, figsize=(15, 80))
    # fig.suptitle(f"VLA EVAL ({parquet_file.replace(args.gt_root, '')})", fontsize=16)
    if rows == 1 and max_cols == 1:
        axes = np.array([[axes]])
    elif rows == 1:
        axes = np.array([axes])
    elif max_cols == 1:
        axes = np.array([[ax] for ax in axes])

    # Draw subplot for each joint
    for joint_idx in range(joint_dim):
        row_idx = joint_idx // max_cols
        col_idx = joint_idx % max_cols
        ax = axes[row_idx, col_idx]
        
        ax.plot(x_gt_vals[joint_idx], y_state_vals[joint_idx], 
                color='blue', linewidth=1.5, 
                marker='.', markersize=3,
                linestyle='-', label='gt_state')
        ax.plot(x_gt_vals[joint_idx], y_action_vals[joint_idx], 
                color='green', linewidth=1.5, 
                marker='.', markersize=3,
                linestyle='-', label='gt_action')
        ax.plot(x_pred_vals[joint_idx], y_pred_vals[joint_idx], 
                color='purple', linewidth=1.5, 
                marker='.', markersize=3,
                linestyle='-', label='pred_action')
        ax.plot(x_trans_vals[joint_idx], y_trans_vals[joint_idx], 
                color='red', linewidth=1.5, 
                marker='o', markersize=8,
                linestyle='', label='trans_point')

        # MSE between y_pred_vals and y_action_vals
        mse = np.mean((np.array(y_pred_vals[joint_idx])[:dt_length] - np.array(y_action_vals[joint_idx])[:dt_length])**2)
        ax.text(0.01, 0.95, f'MSE: {mse:.3e}', transform=ax.transAxes, fontsize=12, verticalalignment='top')
        ax.set_title(f'joint {joint_idx}')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.legend()
        ax.grid(True)
    
    # Calculate MSE separately based on joint ID
    str_mse = ''
    splits_ids = args.split_ids.split(',')
    for split_id in splits_ids:
        start_id, end_id = split_id.split('-')
        start_id, end_id = int(start_id), int(end_id)
        if start_id < 0 or end_id > joint_dim:
            print(f'ERROR: Joint ID out of range: {start_id}-{end_id}')
            continue
        mean_mse = np.mean([np.mean((np.array(y_pred_vals[joint_idx])[:dt_length] - np.array(y_action_vals[joint_idx])[:dt_length])**2) for joint_idx in range(start_id, end_id)])
        str_mse += f'{start_id}-{end_id}: {mean_mse:.3e}, '
    str_mse = str_mse[:-2]
    args_note = f', {args.note}' if args.note != '' else ''
    # mean_mse = np.mean([np.mean((np.array(y_pred_vals[joint_idx])[:dt_length] - np.array(y_action_vals[joint_idx])[:dt_length])**2) for joint_idx in range(joint_dim - 2)])
    str_info = f"VLA EVAL ({parquet_file.replace(args.gt_root, '')}) \nLEN: {dt_length}, Mean MSE: [{str_mse}], Lookahead/Chunk: {args.lookahead_idx}/{chunk_size}\nLanguage: '{args.language}'{args_note}"
    fig.suptitle(str_info, fontsize=16)
    print(str_info)
    # Hide extra subplots
    for joint_idx in range(joint_dim, rows * max_cols):
        row_idx = joint_idx // max_cols
        col_idx = joint_idx % max_cols
        fig.delaxes(axes[row_idx, col_idx])
    # Leave space for title
    plt.tight_layout(rect=(0, 0, 1, 0.98))
    # Save and display chart
    img_name = 'img_vis_eval'
    if args.note != '':
        img_name = f'{img_name}_{args.note}'
    plt.savefig(f'{img_name}.png', dpi=100, bbox_inches='tight')
    print(f'EVAL chart saved to: {os.getcwd()}/{img_name}.png')
    # plt.show()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VLA model offline evaluation visualization tool")
    parser.add_argument("--model_path", type=str, required=True, help="Model path")
    parser.add_argument("--lookahead_idx", type=int, default=16, help="Lookahead index, can be set to chunk_size")
    parser.add_argument("--gt_root", type=str, required=True, help="Ground truth data root directory")
    parser.add_argument("--episode_id", type=int, default=0, help="Trajectory ID")
    parser.add_argument("--chunk_id", type=int, default=0, help="Chunk ID")
    parser.add_argument("--joint_dim", type=int, default=16, help="Joint dimension")
    parser.add_argument("--dt_length", type=int, default=-1, help="Visualization frame length, -1: visualize full trajectory data length")
    parser.add_argument("--split_ids", type=str, default='0-7,7-14,14-15', help="Split MSE calculation based on joint IDs")
    parser.add_argument("--language", type=str, default='pick bottle into the box', help="Custom language instruction")
    parser.add_argument("--note", type=str, default='', help="Custom note, will be displayed on image and filename")
    args = parser.parse_args()
    main(args)
