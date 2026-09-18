#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A2D 机器人观测降频 / 丢帧测试。

测试内容：
    1. 记录 ``retrieve_observation`` 的单次 / 累计运行时间；
    2. 记录 ``retrieve_observation`` 实际获取到的观测帧数，并按 ``ref_timestamp``
       去重，确保统计到的观测数据不重复；
    3. 按照 30FPS（可通过 ``--fps`` 修改）根据运行时间估算理论观测帧数；
    4. 统计丢帧数与丢帧率；
    5. 丢弃前 5 帧观测数据（可通过 ``--warmup-frames`` 修改），待链路稳定后再开始计时；
    6. 统计相邻两帧返回时间间隔大于 45ms（偏慢）与小于 15ms（偏快）的帧数
       （可通过 ``--gap-high-ms`` / ``--gap-low-ms`` 修改）；
    7. 导出的 JSON records 只保留 ``ref_timestamp`` 非空的记录。

用法::

    python test/test_a2d_observe_fps.py                       # 默认 30FPS，测试 60s
    python test/test_a2d_observe_fps.py --duration 120        # 测试 120s
    python test/test_a2d_observe_fps.py --fps 30 --output /tmp/a2d_obs.json

注意：需要连接 A2D 机器人（或已启动 a2d_sdk 服务），并已安装 ``a2d_sdk``。
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from conf.robots_conf import get_robots_config  # noqa: E402

logger = logging.getLogger('a2d_observe_fps')

DEFAULT_FPS = 30
DEFAULT_WARMUP_FRAMES = 5


def parse_args():
    parser = argparse.ArgumentParser(
        description='A2D robot observation FPS / frame-drop test',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--fps', type=float, default=DEFAULT_FPS,
                        help='用于估算理论帧数的目标帧率')
    parser.add_argument('--duration', type=float, default=60.0,
                        help='正式计时阶段的测试时长（秒）')
    parser.add_argument('--warmup-frames', type=int, default=DEFAULT_WARMUP_FRAMES,
                        help='丢弃的前 N 帧观测数据，用于等待链路稳定')
    parser.add_argument('--warmup-timeout', type=float, default=30.0,
                        help='等待预热帧的超时时间（秒），超时则报错退出')
    parser.add_argument('--settle', type=float, default=0.5,
                        help='预热结束后的额外静置时间（秒）')
    parser.add_argument('--max-frames', type=int, default=0,
                        help='最多采集的不重复观测帧数，0 表示不限（由 --duration 控制）')
    parser.add_argument('--interval', type=float, default=0.0,
                        help='两次 retrieve_observation 调用之间的额外间隔（秒）')
    parser.add_argument('--progress-interval', type=float, default=1.0,
                        help='测试过程中打印进度的间隔（秒），0 表示不打印')
    parser.add_argument('--hand-type', type=str, default=None,
                        choices=['gripper', 'hand_as_gripper', 'hand'],
                        help='覆盖 A2D 配置中的 hand_type（影响相机名与 proprio 名称）')
    parser.add_argument('--gap-high-ms', type=float, default=45.0,
                        help='相邻两帧返回时间间隔的偏慢阈值（ms），统计间隔大于该值的帧数')
    parser.add_argument('--gap-low-ms', type=float, default=15.0,
                        help='相邻两帧返回时间间隔的偏快阈值（ms），统计间隔小于该值的帧数')
    parser.add_argument('--timestamp-unit', type=str, default='ns',
                        choices=['ns', 'us', 'ms', 's', 'auto'],
                        help='ref_timestamp 的时间单位，用于统计观测源帧率')
    parser.add_argument('--output', type=str, default=None,
                        help='将统计结果与逐次调用记录保存为 JSON 文件的路径')
    parser.add_argument('--quiet', action='store_true', help='仅输出最终统计报告')
    return parser.parse_args()


def build_robot(args):
    """构建 A2D RobotBody 实例。"""
    try:
        from client.robots.a2d.body_robot import RobotBody
    except ImportError as exc:  # pragma: no cover - 依赖真实硬件环境
        raise SystemExit(
            f'导入 client.robots.a2d.body_robot 失败: {exc}\n'
            '请确认已安装 a2d_sdk（参考 client/robots/a2d/README.md）。'
        )

    config = get_robots_config().a2d
    if args.hand_type is not None and args.hand_type != config.hand_type:
        config.hand_type = args.hand_type
        config.camera.names = {
            'head': 'head',
            'hand_left': 'hand_left_fisheye' if 'hand' in config.hand_type else 'hand_left',
            'hand_right': 'hand_right_fisheye' if 'hand' in config.hand_type else 'hand_right',
        }
        config.proprio_names = [
            'arm', 'hand' if 'hand' in config.hand_type else 'gripper', 'head', 'waist',
        ]
    logger.info('hand_type=%s, cameras=%s', config.hand_type, dict(config.camera.names))
    return RobotBody(config)


class FrameTracker:
    """基于 ref_timestamp 对 retrieve_observation 返回的观测帧去重。

    A2D 的 ``retrieve_observation`` 内部通过与 ``current_timestamp`` 比较来过滤重复帧
    （见 client/robots/a2d/body_robot.py:143），该判据只在相邻两次调用之间生效。
    这里在测试侧独立记录所有出现过的 ``ref_timestamp``，确保统计到的观测数据不重复，
    并能暴露出 SDK 侧去重失效 / 时间戳回退等问题。
    """

    def __init__(self):
        self.seen = set()
        self.last_ts = None
        self.unique = 0           # 去重后的观测帧数
        self.dup_consecutive = 0  # 与上一帧 ref_timestamp 相同的重复帧
        self.dup_repeated = 0     # 与历史帧 ref_timestamp 相同的重复帧（非连续）
        self.missing_ts = 0       # 返回了观测但没有 ref_timestamp
        self.regressions = 0      # ref_timestamp 相对上一帧倒退（且未重复）

    def push(self, ts):
        """判定一帧观测是否重复，返回状态：unique / dup_* / missing_ts。"""
        if ts is None:
            self.missing_ts += 1
            return 'missing_ts'
        if ts == self.last_ts:
            self.dup_consecutive += 1
            return 'dup_consecutive'
        if ts in self.seen:
            self.dup_repeated += 1
            return 'dup_repeated'
        if self.last_ts is not None and ts < self.last_ts:
            self.regressions += 1
        self.seen.add(ts)
        self.last_ts = ts
        self.unique += 1
        return 'unique'

    @property
    def duplicates(self):
        return self.dup_consecutive + self.dup_repeated


def warmup(robot, warmup_frames, timeout):
    """丢弃前 warmup_frames 帧（按 ref_timestamp 去重后）观测数据，确保链路稳定后再开始计时。"""
    if warmup_frames <= 0:
        logger.info('跳过预热阶段')
        return 0.0

    logger.info('预热中：丢弃前 %d 帧不重复观测数据 ...', warmup_frames)
    tracker = FrameTracker()
    calls = 0
    start = time.perf_counter()
    while tracker.unique < warmup_frames:
        obs = robot.retrieve_observation()
        calls += 1
        if obs is not None:
            tracker.push(obs.get('ref_timestamp'))
        if time.perf_counter() - start > timeout:
            raise TimeoutError(
                f'预热超时：{timeout:.1f}s 内仅获取到 {tracker.unique}/{warmup_frames} '
                '帧不重复观测数据，请检查机器人 / 相机连接。'
            )
    cost = time.perf_counter() - start
    logger.info('预热完成：丢弃 %d 帧，调用 %d 次，耗时 %.3fs', tracker.unique, calls, cost)
    return cost


def measure(robot, args):
    """正式计时阶段：反复调用 retrieve_observation 并采集数据。

    对返回的观测按 ref_timestamp 去重，只有不重复的观测帧才计入帧数统计。
    """
    records = []          # [(t_rel, cost_ms, valid, ref_timestamp, status)]
    call_costs = []       # 每次调用的耗时（秒）
    valid_costs = []      # 非空返回的调用耗时（秒）
    ref_timestamps = []   # 去重后观测帧的参考时间戳
    frame_times = []      # 去重后观测帧的返回时刻（相对计时起点，秒）

    tracker = FrameTracker()
    raw_valid = 0         # 非空返回次数（含重复帧）
    empty_returns = 0

    logger.info('开始计时，目标时长 %.1fs ...', args.duration)
    t_start = time.perf_counter()
    last_progress = t_start
    last_valid = 0
    last_progress_mark = t_start

    while True:
        now = time.perf_counter()
        if now - t_start >= args.duration:
            break
        if args.max_frames > 0 and tracker.unique >= args.max_frames:
            break

        t0 = time.perf_counter()
        obs = robot.retrieve_observation()
        cost = time.perf_counter() - t0
        t_rel = time.perf_counter() - t_start

        call_costs.append(cost)
        status = 'empty'
        ts = None
        if obs is not None:
            raw_valid += 1
            valid_costs.append(cost)
            ts = obs.get('ref_timestamp')
            status = tracker.push(ts)
            if status == 'unique':
                ref_timestamps.append(ts)
                frame_times.append(t_rel)
        else:
            empty_returns += 1
        records.append((t_rel, cost * 1000.0, obs is not None, ts, status))

        if args.progress_interval > 0 and time.perf_counter() - last_progress >= args.progress_interval:
            now = time.perf_counter()
            window = now - last_progress_mark
            inst_fps = (tracker.unique - last_valid) / window if window > 0 else 0.0
            logger.info(
                't=%6.2fs | 不重复帧=%5d | 重复帧=%5d | 空返回=%5d '
                '| 窗口帧率=%5.2f FPS | 累计帧率=%5.2f FPS',
                t_rel, tracker.unique, tracker.duplicates, empty_returns,
                inst_fps, tracker.unique / (now - t_start),
            )
            last_progress = now
            last_progress_mark = now
            last_valid = tracker.unique

        if args.interval > 0:
            time.sleep(args.interval)

    elapsed = time.perf_counter() - t_start
    return {
        'elapsed': elapsed,
        'calls': len(call_costs),
        'raw_valid_frames': raw_valid,
        'valid_frames': tracker.unique,
        'empty_returns': empty_returns,
        'duplicate_frames': tracker.duplicates,
        'dup_consecutive': tracker.dup_consecutive,
        'dup_repeated': tracker.dup_repeated,
        'missing_timestamp': tracker.missing_ts,
        'timestamp_regressions': tracker.regressions,
        'call_costs': call_costs,
        'valid_costs': valid_costs,
        'ref_timestamps': ref_timestamps,
        'frame_times': frame_times,
        'records': records,
    }


def _percentile(values, q):
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)


def _resolve_timestamp_scale(stamps, unit):
    """推断 ref_timestamp 的时间单位换算系数（换算为秒）。

    ``client/robots/a2d/body_robot.py`` 中按 ``(ts - last_ts) / 1e6`` 得到毫秒，
    说明 A2D SDK 的 ref_timestamp 单位为纳秒，因此默认值取 'ns'。
    """
    scales = {'ns': 1e-9, 'us': 1e-6, 'ms': 1e-3, 's': 1.0}
    if unit != 'auto':
        return scales[unit]
    if not stamps:
        return scales['ns']
    ts = stamps[-1]
    if ts > 1e17:
        return scales['ns']
    if ts > 1e14:
        return scales['us']
    if ts > 1e11:
        return scales['ms']
    return scales['s']


def _interval_stats(intervals, high_ms, low_ms):
    """统计相邻两帧的间隔分布（intervals 单位为秒）。

    分别统计间隔 > high_ms（偏慢，观测降频）与 < low_ms（偏快，异常密集）的帧数。
    """
    count = len(intervals)
    if not count:
        return {
            'count': 0, 'gt_high': 0, 'lt_low': 0, 'normal': 0,
            'gt_high_percent': 0.0, 'lt_low_percent': 0.0,
            'avg_ms': 0.0, 'min_ms': 0.0, 'max_ms': 0.0,
        }
    gt_high = sum(1 for v in intervals if v * 1000.0 > high_ms)
    lt_low = sum(1 for v in intervals if v * 1000.0 < low_ms)
    return {
        'count': count,
        'gt_high': gt_high,
        'lt_low': lt_low,
        'normal': count - gt_high - lt_low,
        'gt_high_percent': gt_high / count * 100.0,
        'lt_low_percent': lt_low / count * 100.0,
        'avg_ms': sum(intervals) / count * 1000.0,
        'min_ms': min(intervals) * 1000.0,
        'max_ms': max(intervals) * 1000.0,
    }


def analyze(result, target_fps, ts_unit='ns', gap_high_ms=45.0, gap_low_ms=15.0):
    """根据计时结果计算丢帧统计。"""
    elapsed = result['elapsed']
    valid_frames = result['valid_frames']
    call_costs = result['call_costs']
    valid_costs = result['valid_costs']

    theoretical_frames = elapsed * target_fps
    dropped_frames = theoretical_frames - valid_frames
    drop_rate = (dropped_frames / theoretical_frames * 100.0) if theoretical_frames > 0 else 0.0

    actual_fps = valid_frames / elapsed if elapsed > 0 else 0.0
    total_call_time = sum(call_costs)

    ts_deltas = []
    stamps = [ts for ts in result['ref_timestamps'] if ts is not None]
    ts_scale = _resolve_timestamp_scale(stamps, ts_unit)
    for prev, curr in zip(stamps, stamps[1:]):
        delta = curr - prev
        if delta > 0:
            ts_deltas.append(delta * ts_scale)
    src_fps = (1.0 / (sum(ts_deltas) / len(ts_deltas))) if ts_deltas else 0.0

    # 相邻两帧的返回时间间隔（wall clock）：帧被 retrieve_observation 返回的时刻之差
    wall_intervals = [
        curr - prev
        for prev, curr in zip(result['frame_times'], result['frame_times'][1:])
    ]

    raw_valid = result['raw_valid_frames']
    return {
        'elapsed_s': elapsed,
        'target_fps': target_fps,
        'total_calls': result['calls'],
        'raw_valid_frames': raw_valid,
        'valid_frames': valid_frames,
        'empty_returns': result['empty_returns'],
        'duplicate_frames': result['duplicate_frames'],
        'dup_consecutive': result['dup_consecutive'],
        'dup_repeated': result['dup_repeated'],
        'duplicate_rate_percent': (result['duplicate_frames'] / raw_valid * 100.0) if raw_valid else 0.0,
        'gap_high_ms': gap_high_ms,
        'gap_low_ms': gap_low_ms,
        'interval_wall': _interval_stats(wall_intervals, gap_high_ms, gap_low_ms),
        'interval_timestamp': _interval_stats(ts_deltas, gap_high_ms, gap_low_ms),
        'missing_timestamp': result['missing_timestamp'],
        'timestamp_regressions': result['timestamp_regressions'],
        'valid_rate_percent': (valid_frames / result['calls'] * 100.0) if result['calls'] else 0.0,
        'actual_fps': actual_fps,
        'source_fps_by_timestamp': src_fps,
        'theoretical_frames': theoretical_frames,
        'dropped_frames': dropped_frames,
        'drop_rate_percent': drop_rate,
        'call_time_total_s': total_call_time,
        'call_time_ratio_percent': (total_call_time / elapsed * 100.0) if elapsed > 0 else 0.0,
        'call_avg_ms': (sum(call_costs) / len(call_costs) * 1000.0) if call_costs else 0.0,
        'call_p50_ms': _percentile(call_costs, 0.50) * 1000.0,
        'call_p95_ms': _percentile(call_costs, 0.95) * 1000.0,
        'call_p99_ms': _percentile(call_costs, 0.99) * 1000.0,
        'call_max_ms': (max(call_costs) * 1000.0) if call_costs else 0.0,
        'valid_call_avg_ms': (sum(valid_costs) / len(valid_costs) * 1000.0) if valid_costs else 0.0,
        'valid_call_max_ms': (max(valid_costs) * 1000.0) if valid_costs else 0.0,
        'timestamp_interval_avg_ms': (sum(ts_deltas) / len(ts_deltas) * 1000.0) if ts_deltas else 0.0,
        'timestamp_interval_max_ms': (max(ts_deltas) * 1000.0) if ts_deltas else 0.0,
    }


def print_report(stats, warmup_frames):
    line = '=' * 66
    print('\n' + line)
    print('A2D 观测降频 / 丢帧测试报告')
    print(line)
    print(f'预热丢弃帧数          : {warmup_frames}')
    print(f'测试运行时长          : {stats["elapsed_s"]:.3f} s')
    print(f'目标帧率              : {stats["target_fps"]:.1f} FPS')
    print('-' * 66)
    print(f'retrieve_observation 调用总次数 : {stats["total_calls"]}')
    print(f'  非空返回次数        : {stats["raw_valid_frames"]}')
    print(f'  重复观测帧数        : {stats["duplicate_frames"]}  '
          f'(连续重复 {stats["dup_consecutive"]} / 历史重复 {stats["dup_repeated"]})')
    print(f'  不重复观测帧数      : {stats["valid_frames"]}  (按 ref_timestamp 去重，用于丢帧统计)')
    print(f'  空返回次数          : {stats["empty_returns"]}')
    print(f'  重复率              : {stats["duplicate_rate_percent"]:.2f} % '
          f'(重复帧 / 非空返回)')
    print(f'  不重复帧占调用比    : {stats["valid_rate_percent"]:.2f} %')
    if stats['missing_timestamp']:
        print(f'  [警告] 缺失 ref_timestamp : {stats["missing_timestamp"]} 帧，无法做去重校验')
    if stats['timestamp_regressions']:
        print(f'  [警告] ref_timestamp 倒退 : {stats["timestamp_regressions"]} 帧')
    print('-' * 66)
    print('retrieve_observation 运行时间（单次调用耗时）')
    print(f'  累计耗时            : {stats["call_time_total_s"]:.3f} s '
          f'(占测试时长 {stats["call_time_ratio_percent"]:.2f} %)')
    print(f'  avg / p50           : {stats["call_avg_ms"]:.3f} ms / {stats["call_p50_ms"]:.3f} ms')
    print(f'  p95 / p99           : {stats["call_p95_ms"]:.3f} ms / {stats["call_p99_ms"]:.3f} ms')
    print(f'  max                 : {stats["call_max_ms"]:.3f} ms')
    print(f'  非空返回 avg / max  : {stats["valid_call_avg_ms"]:.3f} ms / {stats["valid_call_max_ms"]:.3f} ms')
    print('-' * 66)
    print('帧数统计')
    print(f'  理论观测帧数        : {stats["theoretical_frames"]:.1f}  '
          f'(= {stats["elapsed_s"]:.3f}s x {stats["target_fps"]:.1f}FPS)')
    print(f'  实际观测帧数        : {stats["valid_frames"]} (已按 ref_timestamp 去重)')
    print(f'  实际观测帧率        : {stats["actual_fps"]:.2f} FPS')
    if stats['source_fps_by_timestamp'] > 0:
        print(f'  观测源帧率(ref ts)  : {stats["source_fps_by_timestamp"]:.2f} FPS  '
              f'(平均间隔 {stats["timestamp_interval_avg_ms"]:.2f} ms, '
              f'最大间隔 {stats["timestamp_interval_max_ms"]:.2f} ms)')
    print('-' * 66)
    high = stats['gap_high_ms']
    low = stats['gap_low_ms']
    print('相邻两帧返回时间间隔分布（均基于去重后的观测帧）')
    for title, key in (('采集间隔(返回时刻)', 'interval_wall'),
                       ('时间戳间隔(ref ts)', 'interval_timestamp')):
        s = stats[key]
        print(f'  {title}')
        print(f'    间隔段数            : {s["count"]}')
        print(f'    > {high:.0f} ms (偏慢)  : {s["gt_high"]} 段 '
              f'({s["gt_high_percent"]:.2f} %)')
        print(f'    < {low:.0f} ms (偏快)  : {s["lt_low"]} 段 '
              f'({s["lt_low_percent"]:.2f} %)')
        print(f'    正常区间            : {s["normal"]} 段')
        print(f'    avg / min / max     : {s["avg_ms"]:.2f} / {s["min_ms"]:.2f} '
              f'/ {s["max_ms"]:.2f} ms')
    print('-' * 66)
    dropped = stats['dropped_frames']
    rate = stats['drop_rate_percent']
    if dropped < 0:
        print(f'  丢帧数              : {dropped:.1f} (实际帧数高于理论帧数，未发生丢帧)')
        print(f'  丢帧率              : 0.00 %')
    else:
        print(f'  丢帧数              : {dropped:.1f}')
        print(f'  丢帧率              : {rate:.2f} %')
    print(line + '\n')


def save_json(path, stats, warmup_frames, result):
    payload = {
        'warmup_frames': warmup_frames,
        'summary': stats,
        # 只保留 ref_timestamp 非空的记录
        'records': [
            {'t_rel_s': t_rel, 'cost_ms': cost, 'valid': valid, 'ref_timestamp': ts, 'status': status}
            for t_rel, cost, valid, ts, status in result['records']
            if ts is not None
        ],
    }
    payload['records_count'] = len(payload['records'])
    payload['records_filtered_out'] = len(result['records']) - len(payload['records'])
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info('结果已保存至 %s', path)


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
    )

    robot = None
    try:
        robot = build_robot(args)
        warmup(robot, args.warmup_frames, args.warmup_timeout)
        if args.settle > 0:
            time.sleep(args.settle)

        result = measure(robot, args)
        stats = analyze(result, args.fps, args.timestamp_unit, args.gap_high_ms, args.gap_low_ms)
        print_report(stats, args.warmup_frames)

        if args.output:
            save_json(args.output, stats, args.warmup_frames, result)

        if stats['duplicate_frames'] > 0:
            logger.warning(
                '检测到 %d 帧重复观测（连续重复 %d / 历史重复 %d）：'
                'retrieve_observation 返回了 ref_timestamp 相同的数据，已按去重后的帧数统计。',
                stats['duplicate_frames'], stats['dup_consecutive'], stats['dup_repeated'],
            )
        if stats['missing_timestamp'] > 0:
            logger.warning('有 %d 帧观测缺少 ref_timestamp，无法完成去重校验。',
                           stats['missing_timestamp'])
        if stats['dropped_frames'] > 0 and stats['drop_rate_percent'] > 10.0:
            logger.warning('丢帧率 %.2f%%，观测存在明显降频，请检查相机 / DDS 链路。',
                           stats['drop_rate_percent'])
        return 0
    except KeyboardInterrupt:
        print('\n测试被用户中断。')
        return 130
    finally:
        if robot is not None:
            try:
                robot.close()
            except Exception as exc:  # pragma: no cover
                logger.warning('关闭机器人失败: %s', exc)


if __name__ == '__main__':
    sys.exit(main())
