"""
抓取任务 - 根据 target 选择语言指令，调用 VLA 模型推理执行抓取

grasp 是一个大类，通过 target 字段区分具体的抓取动作（单手/双手、目标物体）。
"""

import sys
import os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from action_server.action_base import (
    AbstractTaskHandler, TaskResult, run_vla_inference,
    ERR_MISSING_TARGET, ERR_UNKNOWN_TARGET,
    ERR_GRASP_TIMEOUT, ERR_ONE_HAND_FAILED,
    ERR_TWO_HAND_LEFT_FAILED, ERR_TWO_HAND_RIGHT_FAILED,
    ERR_TWO_HAND_BOTH_FAILED,
)


# ==============================================
# Target → 手数映射
# ==============================================
# 显式映射，不依赖字符串前缀判断
TARGET_HAND_MAP: dict[str, str] = {
    "one water": "one hand",
    "one Coca-Cola": "one hand",
    "two water": "two hand",
    "two Coca-Cola": "two hand",
}

# ==============================================
# target → 语言指令映射表
# ==============================================
# key 为 params.target（不区分大小写），value 为对应的语言指令
TARGET_LANGUAGE_MAP: dict[str, str] = {
    "one water": "Use one hand to grab one bottle from a pile of Wahaha drinks.",
    "one Coca-Cola": "Use one hand to grab one bottle from a pile of Coca-Cola drinks.",
    "two water": "Use both hands to grab the two nearest bottles from a pile of Wahaha drinks.",
    "two Coca-Cola": "Use both hands to grab the two nearest bottles from a pile of Coca-Cola drinks.",
}


def _get_language_instruction(target: str) -> str | None:
    """根据 target 名称获取语言指令

    Args:
        target: params 中的 target 字段值

    Returns:
        语言指令字符串，未找到则返回 None
    """
    return TARGET_LANGUAGE_MAP.get(target.strip())


def _reset_arms_to_default(robot_body, context, duration=2.0):
    """将双臂在指定时间内线性过渡到默认位置，手掌保持当前控制量不变

    Args:
        robot_body: RobotBody 实例
        context: VLAContext 实例
        duration: 过渡时间（秒）
    """
    import numpy as np
    import time

    # 获取默认位置配置
    robot_type = context.config.robots.type.value
    robot_cfg = getattr(context.config.robots, robot_type)
    default_pose = np.array(robot_cfg.reset_robot_pos, dtype=np.float64)

    # 获取当前机器人完整状态（26维）
    current_state = robot_body._get_reset_current_state()
    if current_state is None:
        print('[GraspHandler] WARN: 无法获取当前机器人状态，跳过手臂复位')
        return

    current_arm = current_state[:14]  # 当前手臂位置

    # 获取当前手掌控制量（保持手掌不变）
    # 优先从 robot 的缓存状态中读取（由 VLA 推理过程中更新）
    left_hand = getattr(robot_body.robot, 'current_left_hand_state', None)
    right_hand = getattr(robot_body.robot, 'current_right_hand_state', None)

    # 如果缓存中无手掌状态，从当前状态中取
    if left_hand is None and len(current_state) >= 20:
        left_hand = current_state[14:20]
    if right_hand is None and len(current_state) >= 26:
        right_hand = current_state[20:26]

    # 兜底使用默认姿态的手掌值
    if left_hand is None:
        left_hand = default_pose[14:20]
    if right_hand is None:
        right_hand = default_pose[20:26]

    left_hand = np.asarray(left_hand, dtype=float)
    right_hand = np.asarray(right_hand, dtype=float)

    target_arm = default_pose[:14]

    # 计算手臂距离，如果已经接近则跳过
    arm_dist = np.max(np.abs(current_arm - target_arm))
    if arm_dist < np.deg2rad(0.5):
        print(f'[GraspHandler] 手臂已在默认位置附近 (max_diff={arm_dist:.4f} rad)，跳过复位')
        return

    n_steps = max(1, int(duration / 0.02))  # 50Hz
    print(f'[GraspHandler] 双臂回归默认位置 ({duration}s, {n_steps} steps)...')

    for i in range(1, n_steps + 1):
        t = i / n_steps
        action = np.zeros(26)
        action[:14] = current_arm + t * (target_arm - current_arm)
        action[14:20] = left_hand
        action[20:26] = right_hand
        robot_body.robot.send_robot_action(action)
        time.sleep(0.02)

    print('[GraspHandler] 双臂回归默认位置完成')


def _apply_smooth_start_blend(vla_client, robot_body, blend_duration=3.0):
    """Monkey-patch vla_client 首帧推理，添加从当前 action → 模型轨迹的平滑过渡。

    对于控制精度低的机械臂，state（传感器读数）与 action（下发指令）偏差很大且存在延迟/噪声。
    使用最近下发的 action 作为起点，可以避免因 state-action 差异导致的启动抖动。
    
    本函数在首帧推理中把 action_chunk 前 N 步从当前 action 线性插值到模型原始轨迹，消除突变。

    通过临时替换 _process_action_chunk 实例方法实现，不影响类的其他实例。

    Args:
        vla_client: VLAClientAsync 实例
        robot_body: RobotBody 实例
        blend_duration: 过渡时长（秒），默认 3.0
    """
    import types
    import numpy as np
    import time

    print(f'[SmoothStart] === Enter _apply_smooth_start_blend ===')

    # 捕获当前正在执行的 action（而非 sensor state）
    # 原因：对于控制精度低的机器人，state 有延迟和噪声，而 action 是实时下发的控制目标
    # 使用 action 作为起点可以避免因 state-action 偏差导致的启动抖动
    current_action = None
    try:
        # 优先从 robot_body 获取最近下发的 action（reset 阶段刚执行完，有缓存）
        # _get_reset_current_action() 的优先级：
        #   1. Action cache — /joint_action + /left_hand/set_angle + /right_hand/set_angle
        #      （最近一次通过 send_robot_action 下发到机器人的指令）
        #   2. VLA cached state
        #   3. retrieve_observation() fallback
        act = robot_body._get_reset_current_action()
        if act is not None:
            current_action = np.asarray(act, dtype=np.float64)
            print(f'[SmoothStart] Current action captured from robot_body._get_reset_current_action(), '
                  f'dim={len(current_action)}, first 4 values: {current_action[:4].round(4).tolist()}')
        else:
            # Fallback: try realtime_data_manager (VLA 已开始但不一定有缓存)
            rdm = vla_client.realtime_data_manager
            currt_act, _, _ = rdm.get_current_state()
            if currt_act is not None:
                current_action = np.asarray(currt_act, dtype=np.float64)
                print(f'[SmoothStart] Current action captured from RDM, dim={len(current_action)}, '
                      f'first 4 values: {current_action[:4].round(4).tolist()}')
            else:
                print(f'[SmoothStart] WARN: both robot_body and RDM returned None for current action')
    except Exception as e:
        print(f'[SmoothStart] WARN: failed to capture current action: {e}')

    if current_action is None:
        print('[SmoothStart] SKIP: no current action available, smooth start disabled')
        return

    observe_period = vla_client.observe_period
    original_infer_first = vla_client._inference_first
    print(f'[SmoothStart] observe_period={observe_period:.4f}s')

    def _patched_inference_first(self):
        """带平滑启动的 _inference_first 包装。"""
        print(f'[SmoothStart] >>> _patched_inference_first called (infer_count={self.realtime_data_manager.infer_count})')

        # 保存原始的 _process_action_chunk（bound method）
        original_process = self._process_action_chunk

        def _blended_process(action_raw):
            """在 _process_action_chunk 返回值上叠加线性插值 blend。

            注意：这里直接赋值为实例属性（不用 MethodType），
            所以 action_raw 是原始的 action_data 参数，不会多一个 self。
            """
            t0 = time.perf_counter()
            action_chunk, ts, loc_ts = original_process(action_raw)

            if action_chunk is not None and len(action_chunk) > 1:
                total = len(action_chunk)
                num_blend = min(int(blend_duration / observe_period), total - 1)

                print(f'[SmoothStart]   _blended_process: total={total}, num_blend={num_blend}, '
                      f'action_chunk[0] first 4 before: '
                      f'{np.array(action_chunk[0], dtype=np.float64)[:4].round(4).tolist()}')

                if num_blend >= 1:
                    for i in range(num_blend + 1):
                        alpha = i / num_blend
                        act = np.array(action_chunk[i], dtype=np.float64)
                        dim = min(len(act), len(current_action))
                        act[:dim] = (1 - alpha) * current_action[:dim] + alpha * act[:dim]
                        action_chunk[i] = act

                    print(f'[SmoothStart]   AFTER blend: action_chunk[0] first 4 = '
                          f'{np.array(action_chunk[0], dtype=np.float64)[:4].round(4).tolist()}')
                    print(f'[SmoothStart]   Blended first {num_blend+1}/{total} steps '
                          f'(duration={blend_duration}s, elapsed={time.perf_counter()-t0:.3f}s)')
                else:
                    print(f'[SmoothStart]   num_blend={num_blend} < 1, skip blend')
            else:
                print(f'[SmoothStart]   SKIP blend: action_chunk={type(action_chunk).__name__}, len={len(action_chunk) if action_chunk else 0}')

            return action_chunk, ts, loc_ts

        # 临时替换实例方法（作为普通函数，不用 MethodType）
        # 这样 self._process_action_chunk(action_data) 调用时，
        # action_data 直接传给 action_raw 参数，不会多绑一个 self
        self._process_action_chunk = _blended_process

        try:
            original_infer_first()
            print(f'[SmoothStart] <<< original _inference_first completed OK')
        except Exception as e:
            import traceback
            print(f'[SmoothStart] ERROR in original _inference_first: {e}')
            traceback.print_exc()
        finally:
            # 删除实例属性，恢复原始类方法
            try:
                del self._process_action_chunk
                print(f'[SmoothStart]   _process_action_chunk restored')
            except AttributeError:
                print(f'[SmoothStart]   _process_action_chunk restore skipped (no instance attr)')

    vla_client._inference_first = types.MethodType(_patched_inference_first, vla_client)
    print(f'[SmoothStart] === Patch applied successfully ===')
    print(f'[SmoothStart]    blend_duration={blend_duration}s, observe_period={observe_period:.4f}s, '
          f'expected blend steps={int(blend_duration/observe_period)}')


class GraspHandler(AbstractTaskHandler):
    """'grasp' 任务处理器 — 抓取大类

    流程:
        1. 根据 params.target 查找对应的语言指令
        2. 创建 VLA 推理组件（vla_client 等）
        3. 调用 run_vla_inference() 执行推理
        4. 清理 per-task 组件
    """

    @property
    def task_name(self) -> str:
        return "grasp"

    def execute(self, goal_handle, params: dict, context) -> TaskResult:
        import time
        import threading as _thr
        _tname = _thr.current_thread().name
        _t0 = time.time()
        print(f'[DEBUG GraspHandler] ENTER on {_tname}, params={params}')
        
        # ===== 步骤 1: 解析 target 并获取语言指令 =====
        target = params.get("target", "")
        if not target:
            self.send_feedback(goal_handle, 0, "缺少 target 字段")
            print(f'[DEBUG GraspHandler] EXIT early: missing target')
            return TaskResult(False, error_code=ERR_MISSING_TARGET,
                              error_message='Missing "target" field in params')

        instruction = _get_language_instruction(target)
        if instruction is None:
            self.send_feedback(goal_handle, 0,
                               f"未知 target: {target}")
            print(f'[DEBUG GraspHandler] EXIT early: unknown target={target}')
            return TaskResult(False, error_code=ERR_UNKNOWN_TARGET,
                              error_message=f'Unknown target="{target}". '
                                            f'Supported: {list(TARGET_LANGUAGE_MAP.keys())}')

        self.send_feedback(goal_handle, 5,
                           f"抓取目标: {target}, 语言指令: {instruction}")
        print(f'[DEBUG GraspHandler] target={target} instruction="{instruction}" → creating VLA components...')

        # ===== 步骤 2: 创建 VLA 组件 =====
        components = context.create_vla_components()
        vla_client = components["vla_client"]
        task_language_manager = components["task_language_manager"]
        robot_body = context.robot_body

        # Override language instruction in task_language_manager
        # （因为 create_vla_components() 中 auto_mode=False，但初始化时已经从 config.language.task_id="pour_tea"
        # 读取了默认指令，需要手动覆盖为当前任务的指令）
        print(f'[DEBUG GraspHandler] Overriding language instruction: "{instruction}"')
        task_language_manager.currt_language_instruction = instruction
        task_language_manager.config.sub_task_id = 0  # Reset sub_task_id to avoid confusion

        # Apply smooth start: blend from current state to model trajectory (first N steps)
        # 消除启动时因模型输出与实际 state 差异大导致的抖动和图像模糊
        _apply_smooth_start_blend(vla_client, robot_body, blend_duration=3.0)

        print(f'[DEBUG GraspHandler] VLA components created, starting inference...')

        try:
            # ===== 步骤 3: 执行 VLA 推理 =====
            context._active_vla_client = vla_client  # 供 ObsDataBridge 读取进度
            result = run_vla_inference(
                goal_handle=goal_handle,
                vla_client=vla_client,
                language_instruction=instruction,
                robot_body=robot_body,
                reset_robot=not context._initialized,
                max_duration=30.0,
                thre_progress=1.5,  # 禁止 prob_progress 稳定性检测，靠 >80% 直接完成或 30s 超时
                stable_count_threshold=999,
            )

            # ===== 步骤 4: 分析结果，结合手势判断具体错误 =====
            if not result.success:
                # 超时 → 映射为抓取超时错误码
                if result.error_code == 6:
                    return TaskResult(False, error_code=ERR_GRASP_TIMEOUT,
                                      error_message="Grasp task timed out")
                # 其他错误（复位失败、推理未启动、取消等）→ 原样透传
                return result

            # VLA 推理成功 (prob_progress > 80%)，验证实际抓握状态
            hand_type = TARGET_HAND_MAP.get(target.strip(), "one hand")
            grasp_state = context.grasp_detector.grasp_state  # [left, right]

            if hand_type == "one hand":
                if not (grasp_state[0] or grasp_state[1]):  # 任一手抓到即成功
                    return TaskResult(False, error_code=ERR_ONE_HAND_FAILED,
                                      error_message="One-hand grasp failed")
                return result  # 抓握成功

            # two hand
            if grasp_state[0] and grasp_state[1]:
                return result  # 双手抓握成功
            if not grasp_state[0] and not grasp_state[1]:
                return TaskResult(False, error_code=ERR_TWO_HAND_BOTH_FAILED,
                                  error_message="Both hands grasp failed")
            if not grasp_state[0]:
                return TaskResult(False, error_code=ERR_TWO_HAND_LEFT_FAILED,
                                  error_message="Left hand grasp failed")
            # not grasp_state[1]
            return TaskResult(False, error_code=ERR_TWO_HAND_RIGHT_FAILED,
                              error_message="Right hand grasp failed")

        finally:
            # ===== 步骤 5: 清理 per-task 组件 =====
            context._active_vla_client = None
            _elapsed = time.time() - _t0
            print(f'[DEBUG GraspHandler] EXIT after {_elapsed:.1f}s, running destroy_vla_components...')
            context.destroy_vla_components(components)
            print(f'[DEBUG GraspHandler] destroy_vla_components done')
