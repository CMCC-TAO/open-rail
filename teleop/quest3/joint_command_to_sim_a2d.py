#!/usr/bin/env python3
"""Forward /target_robot/joint_commands JointState messages to trajectory actions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
import time
from typing import Iterable


LEFT_ARM_JOINTS = [f"left_arm_joint{i}" for i in range(1, 8)]
RIGHT_ARM_JOINTS = [f"right_arm_joint{i}" for i in range(1, 8)]
LEFT_HAND_JOINT = "left_hand_joint1"
RIGHT_HAND_JOINT = "right_hand_joint1"
HEAD_JOINTS = ["joint_head_yaw", "joint_head_pitch"]
BODY_JOINTS = ["joint_lift_body", "joint_body_pitch"]
HOME_JOINT_NAMES = [
    *LEFT_ARM_JOINTS,
    *RIGHT_ARM_JOINTS,
    LEFT_HAND_JOINT,
    RIGHT_HAND_JOINT,
]
HOME_ACTION = [
    -1.0748,
    0.6107,
    0.2816,
    -1.2823,
    0.7292,
    1.4957,
    -0.1869,
    1.0720,
    -0.6103,
    -0.2780,
    1.2822,
    -0.7299,
    -1.4929,
    0.1873,
    1.0,
    1.0,
]


@dataclass(frozen=True)
class ActionServers:
    left_arm: str
    right_arm: str
    head: str
    body: str


def _duration_from_seconds(seconds: float):
    from builtin_interfaces.msg import Duration

    seconds = max(float(seconds), 0.0)
    sec = int(math.floor(seconds))
    nanosec = int(round((seconds - sec) * 1_000_000_000))
    if nanosec >= 1_000_000_000:
        sec += 1
        nanosec -= 1_000_000_000
    return Duration(sec=sec, nanosec=nanosec)


class JointCommandToTrajectoryNode:
    def __init__(
        self,
        *,
        topic: str,
        joint_states_topic: str,
        reset_topic: str,
        reset_threshold: float,
        action_servers: ActionServers,
        time_from_start_sec: float,
        default_left_hand: float,
        default_right_hand: float,
        min_send_period_sec: float,
        reset_interp_steps: int,
        reset_interp_duration_sec: float,
        reset_start_hold_sec: float,
        wait_timeout_sec: float,
    ):
        import rclpy
        from control_msgs.action import FollowJointTrajectory
        from rclpy.action import ActionClient
        from rclpy.node import Node
        from sensor_msgs.msg import JointState
        from std_msgs.msg import Float64
        from trajectory_msgs.msg import JointTrajectoryPoint

        class _Node(Node):
            pass

        self.rclpy = rclpy
        self.FollowJointTrajectory = FollowJointTrajectory
        self.JointTrajectoryPoint = JointTrajectoryPoint
        self.node = _Node("quest3_joint_command_to_trajectory")
        self.time_from_start = _duration_from_seconds(time_from_start_sec)
        self.default_left_hand = float(default_left_hand)
        self.default_right_hand = float(default_right_hand)
        self.min_send_period_sec = max(float(min_send_period_sec), 0.0)
        self.reset_threshold = float(reset_threshold)
        self.reset_interp_steps = max(int(reset_interp_steps), 1)
        self.reset_interp_duration_sec = max(float(reset_interp_duration_sec), 0.0)
        self.reset_start_hold_sec = max(float(reset_start_hold_sec), 0.0)
        self._reset_pressed = False
        self._last_send_s = 0.0
        self._last_warn_s = 0.0
        if len(HOME_JOINT_NAMES) != len(HOME_ACTION):
            raise ValueError("HOME_JOINT_NAMES and HOME_ACTION must have the same length.")
        self.home_positions = dict(zip(HOME_JOINT_NAMES, HOME_ACTION))
        self.latest_positions = self.home_positions.copy()
        self.actual_positions = {}

        self.left_arm_client = ActionClient(self.node, FollowJointTrajectory, action_servers.left_arm)
        self.right_arm_client = ActionClient(self.node, FollowJointTrajectory, action_servers.right_arm)
        self.head_client = ActionClient(self.node, FollowJointTrajectory, action_servers.head)
        self.body_client = ActionClient(self.node, FollowJointTrajectory, action_servers.body)
        self.clients = {
            "left_arm": self.left_arm_client,
            "right_arm": self.right_arm_client,
            "head": self.head_client,
            "body": self.body_client,
        }

        if wait_timeout_sec > 0.0:
            for name, client in self.clients.items():
                if not client.wait_for_server(timeout_sec=float(wait_timeout_sec)):
                    self.node.get_logger().warning(f"Action server not ready: {name}")

        self.node.create_subscription(JointState, topic, self._joint_command_cb, 10)
        self.node.create_subscription(JointState, joint_states_topic, self._joint_state_cb, 10)
        self.node.create_subscription(Float64, reset_topic, self._reset_cb, 10)
        self.node.get_logger().info(f"Forwarding JointState commands from {topic} to trajectory actions.")
        self.node.get_logger().info(f"Reading current joint state from {joint_states_topic}.")
        self.node.get_logger().info(f"Listening for reset rising edges on {reset_topic}.")

    def spin(self) -> None:
        try:
            self.rclpy.spin(self.node)
        finally:
            self.node.destroy_node()

    def _joint_command_cb(self, msg) -> None:
        now = time.monotonic()
        if self.min_send_period_sec > 0.0 and now - self._last_send_s < self.min_send_period_sec:
            return

        positions = dict(zip(msg.name, msg.position))
        if not positions:
            return

        self.latest_positions.update({name: float(value) for name, value in positions.items()})
        if self._forward_positions(positions):
            self._last_send_s = now

    def _joint_state_cb(self, msg) -> None:
        positions = dict(zip(msg.name, msg.position))
        if positions:
            self.actual_positions.update({name: float(value) for name, value in positions.items()})

    def _reset_cb(self, msg) -> None:
        pressed = float(msg.data) > self.reset_threshold
        if pressed and not self._reset_pressed:
            self.node.get_logger().info("Reset rising edge received; interpolating to home joint trajectory.")
            if self._send_interpolated_home():
                self._last_send_s = time.monotonic()
                self.latest_positions.update(self.home_positions)
        self._reset_pressed = pressed

    def _forward_positions(self, positions: dict[str, float]) -> bool:
        sent = False
        matched = False
        left_arm = self._lookup_positions(positions, LEFT_ARM_JOINTS)
        if left_arm is not None:
            matched = True
            left_arm.append(float(positions.get(LEFT_HAND_JOINT, self.default_left_hand)))
            sent = self._send_trajectory_goal(
                self.left_arm_client,
                [*LEFT_ARM_JOINTS, LEFT_HAND_JOINT],
                left_arm,
                "left_arm",
            ) or sent

        right_arm = self._lookup_positions(positions, RIGHT_ARM_JOINTS)
        if right_arm is not None:
            matched = True
            right_arm.append(float(positions.get(RIGHT_HAND_JOINT, self.default_right_hand)))
            sent = self._send_trajectory_goal(
                self.right_arm_client,
                [*RIGHT_ARM_JOINTS, RIGHT_HAND_JOINT],
                right_arm,
                "right_arm",
            ) or sent

        head = self._lookup_positions(positions, HEAD_JOINTS)
        if head is not None:
            matched = True
            sent = self._send_trajectory_goal(self.head_client, HEAD_JOINTS, head, "head") or sent

        body = self._lookup_positions(positions, BODY_JOINTS)
        if body is not None:
            matched = True
            sent = self._send_trajectory_goal(self.body_client, BODY_JOINTS, body, "body") or sent

        if not matched:
            self._warn_throttled(
                "JointState did not contain a complete left arm, right arm, head, or body command."
            )
        return sent

    def _send_interpolated_home(self) -> bool:
        sent = False
        groups = (
            (
                self.left_arm_client,
                [*LEFT_ARM_JOINTS, LEFT_HAND_JOINT],
                "left_arm_reset",
            ),
            (
                self.right_arm_client,
                [*RIGHT_ARM_JOINTS, RIGHT_HAND_JOINT],
                "right_arm_reset",
            ),
        )
        for client, joint_names, label in groups:
            points = self._interpolate_group(joint_names)
            sent = self._send_trajectory_points(client, joint_names, points, label) or sent
        return sent

    def _interpolate_group(self, joint_names: list[str]) -> list[tuple[list[float], float]]:
        start = [
            float(self.actual_positions.get(name, self.latest_positions.get(name, self.home_positions[name])))
            for name in joint_names
        ]
        target = [float(self.home_positions[name]) for name in joint_names]
        points = []
        if self.reset_start_hold_sec > 0.0:
            points.append((start, self.reset_start_hold_sec))
        for step in range(1, self.reset_interp_steps + 1):
            alpha = step / self.reset_interp_steps
            positions = [
                (1.0 - alpha) * start_value + alpha * target_value
                for start_value, target_value in zip(start, target)
            ]
            time_from_start = self.reset_start_hold_sec + self.reset_interp_duration_sec * alpha
            points.append((positions, time_from_start))
        return points

    @staticmethod
    def _lookup_positions(positions: dict[str, float], joint_names: Iterable[str]) -> list[float] | None:
        out = []
        for name in joint_names:
            if name not in positions:
                return None
            out.append(float(positions[name]))
        return out

    def _send_trajectory_goal(self, client, joint_names: list[str], positions: list[float], label: str) -> bool:
        return self._send_trajectory_points(
            client,
            joint_names,
            [(positions, self._duration_to_seconds(self.time_from_start))],
            label,
        )

    def _send_trajectory_points(
        self,
        client,
        joint_names: list[str],
        points: list[tuple[list[float], float]],
        label: str,
    ) -> bool:
        if not client.server_is_ready():
            self._warn_throttled(f"Action server is not ready for {label}; dropping command.")
            return False

        goal_msg = self.FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = joint_names
        goal_msg.trajectory.points = []
        for positions, time_from_start in points:
            point = self.JointTrajectoryPoint()
            point.positions = [float(value) for value in positions]
            point.time_from_start = _duration_from_seconds(time_from_start)
            goal_msg.trajectory.points.append(point)
        future = client.send_goal_async(goal_msg)
        future.add_done_callback(lambda done, group=label: self._goal_response_cb(done, group))
        return True

    @staticmethod
    def _duration_to_seconds(duration) -> float:
        return float(duration.sec) + float(duration.nanosec) / 1_000_000_000.0

    def _goal_response_cb(self, future, label: str) -> None:
        try:
            handle = future.result()
        except Exception as exc:
            self._warn_throttled(f"Failed to send {label} trajectory goal: {exc}")
            return
        if not handle.accepted:
            self._warn_throttled(f"{label} trajectory goal was rejected.")

    def _warn_throttled(self, message: str, period_s: float = 1.0) -> None:
        now = time.monotonic()
        if now - self._last_warn_s >= period_s:
            self._last_warn_s = now
            self.node.get_logger().warning(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Forward /target_robot/joint_commands JointState messages to FollowJointTrajectory actions."
    )
    parser.add_argument("--joint-command-topic", default="/target_robot/joint_commands")
    parser.add_argument("--joint-states-topic", default="/joint_states")
    parser.add_argument("--reset-topic", default="/custom/custom_a")
    parser.add_argument("--reset-threshold", type=float, default=0.5)
    parser.add_argument("--left-arm-action", default="/left_arm_controller/follow_joint_trajectory")
    parser.add_argument("--right-arm-action", default="/right_arm_controller/follow_joint_trajectory")
    parser.add_argument("--head-action", default="/head_controller/follow_joint_trajectory")
    parser.add_argument("--body-action", default="/body_controller/follow_joint_trajectory")
    parser.add_argument("--time-from-start-sec", type=float, default=0.1)
    parser.add_argument("--default-left-hand", type=float, default=1.0)
    parser.add_argument("--default-right-hand", type=float, default=1.0)
    parser.add_argument("--min-send-period-sec", type=float, default=0.0)
    parser.add_argument("--reset-interp-steps", type=int, default=20)
    parser.add_argument("--reset-interp-duration-sec", type=float, default=2.0)
    parser.add_argument("--reset-start-hold-sec", type=float, default=0.1)
    parser.add_argument("--wait-timeout-sec", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    import rclpy

    rclpy.init(args=None)
    node = JointCommandToTrajectoryNode(
        topic=args.joint_command_topic,
        joint_states_topic=args.joint_states_topic,
        reset_topic=args.reset_topic,
        reset_threshold=args.reset_threshold,
        action_servers=ActionServers(
            left_arm=args.left_arm_action,
            right_arm=args.right_arm_action,
            head=args.head_action,
            body=args.body_action,
        ),
        time_from_start_sec=args.time_from_start_sec,
        default_left_hand=args.default_left_hand,
        default_right_hand=args.default_right_hand,
        min_send_period_sec=args.min_send_period_sec,
        reset_interp_steps=args.reset_interp_steps,
        reset_interp_duration_sec=args.reset_interp_duration_sec,
        reset_start_hold_sec=args.reset_start_hold_sec,
        wait_timeout_sec=args.wait_timeout_sec,
    )
    try:
        node.spin()
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
