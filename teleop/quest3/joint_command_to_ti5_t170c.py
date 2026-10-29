#!/usr/bin/env python3
"""Forward Quest3 bridge JointState commands to TI5 T170C trajectory actions."""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass

from conf.robots_conf import get_robot_config

BRIDGE_LEFT_ARM_JOINTS = [f"left_arm_joint{i}" for i in range(1, 8)]
BRIDGE_RIGHT_ARM_JOINTS = [f"right_arm_joint{i}" for i in range(1, 8)]

TI5_LEFT_ARM_JOINTS = [f"Joint{i}_L" for i in range(1, 8)]
TI5_RIGHT_ARM_JOINTS = [f"Joint{i}_R" for i in range(1, 8)]

_TI5_RESET_POSITION = list(get_robot_config('ti5_t170c').reset_robot_pos)
LEFT_ARM_RESET_POS = _TI5_RESET_POSITION[:7]
RIGHT_ARM_RESET_POS = _TI5_RESET_POSITION[7:14]

# Kept for parity with the TI5 reset definition, but this forwarder only commands arms.
WAIST_RESET_POS = [0.0, 0.0, 0.0]
NECK_RESET_POS = [0.0, 0.0, 0.0]
LEFT_HAND_RESET_POS = [_TI5_RESET_POSITION[14]]
RIGHT_HAND_RESET_POS = [_TI5_RESET_POSITION[20]]


@dataclass(frozen=True)
class ActionServers:
    left_arm: str
    right_arm: str


def _duration_from_seconds(seconds: float):
    from builtin_interfaces.msg import Duration

    seconds = max(float(seconds), 0.0)
    sec = int(math.floor(seconds))
    nanosec = int(round((seconds - sec) * 1_000_000_000))
    if nanosec >= 1_000_000_000:
        sec += 1
        nanosec -= 1_000_000_000
    return Duration(sec=sec, nanosec=nanosec)


class JointCommandToTi5T170CNode:
    """Convert bridge JointState commands into TI5 FollowJointTrajectory goals."""

    def __init__(
        self,
        *,
        topic: str,
        reset_topic: str,
        reset_threshold: float,
        action_servers: ActionServers,
        time_from_start_sec: float,
        reset_duration_sec: float,
        min_send_period_sec: float,
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
        self.node = _Node("quest3_joint_command_to_ti5_t170c")
        self.time_from_start = _duration_from_seconds(time_from_start_sec)
        self.reset_time_from_start = _duration_from_seconds(reset_duration_sec)
        self.reset_threshold = float(reset_threshold)
        self.min_send_period_sec = max(float(min_send_period_sec), 0.0)
        self._reset_pressed = False
        self._last_send_s = 0.0
        self._last_warn_s = 0.0

        self.left_arm_client = ActionClient(self.node, FollowJointTrajectory, action_servers.left_arm)
        self.right_arm_client = ActionClient(self.node, FollowJointTrajectory, action_servers.right_arm)
        self.clients = {
            "left_arm": self.left_arm_client,
            "right_arm": self.right_arm_client,
        }

        if wait_timeout_sec > 0.0:
            for name, client in self.clients.items():
                if not client.wait_for_server(timeout_sec=float(wait_timeout_sec)):
                    self.node.get_logger().warning(f"Action server not ready: {name}")

        self.node.create_subscription(JointState, topic, self._joint_command_cb, 10)
        self.node.create_subscription(Float64, reset_topic, self._reset_cb, 10)
        self.node.get_logger().info(f"Forwarding JointState commands from {topic} to TI5 T170C actions.")
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

        joint_data = {
            "left_arm": self._lookup_positions(positions, BRIDGE_LEFT_ARM_JOINTS) or [],
            "right_arm": self._lookup_positions(positions, BRIDGE_RIGHT_ARM_JOINTS) or [],
        }
        if self.send_joint_positions(joint_data):
            self._last_send_s = now

    def _reset_cb(self, msg) -> None:
        pressed = float(msg.data) > self.reset_threshold
        if pressed and not self._reset_pressed:
            self.node.get_logger().info("Reset rising edge received; sending TI5 arm reset positions.")
            if self._send_arm_reset_positions():
                self._last_send_s = time.monotonic()
        self._reset_pressed = pressed

    def send_joint_positions(self, joint_data: dict[str, list[float]]) -> bool:
        """Send parsed joint position groups to the TI5 T170C action servers."""
        left_arm_data = joint_data.get("left_arm", [])
        right_arm_data = joint_data.get("right_arm", [])

        if len(left_arm_data) < 7 or len(right_arm_data) < 7:
            self._warn_throttled(
                f"Incomplete joint data received. Left: {len(left_arm_data)}, Right: {len(right_arm_data)}"
            )
            return False

        sent = False
        sent = self.send_trajectory_goal(
            self.left_arm_client,
            TI5_LEFT_ARM_JOINTS,
            left_arm_data[:7],
            "left_arm",
        ) or sent
        sent = self.send_trajectory_goal(
            self.right_arm_client,
            TI5_RIGHT_ARM_JOINTS,
            right_arm_data[:7],
            "right_arm",
        ) or sent

        if sent:
            self.node.get_logger().info("Sent joint positions to TI5 T170C robot")
        return sent

    def _send_arm_reset_positions(self) -> bool:
        sent = False
        sent = self.send_trajectory_goal(
            self.left_arm_client,
            TI5_LEFT_ARM_JOINTS,
            LEFT_ARM_RESET_POS,
            "left_arm_reset",
            time_from_start=self.reset_time_from_start,
        ) or sent
        sent = self.send_trajectory_goal(
            self.right_arm_client,
            TI5_RIGHT_ARM_JOINTS,
            RIGHT_ARM_RESET_POS,
            "right_arm_reset",
            time_from_start=self.reset_time_from_start,
        ) or sent
        return sent

    @staticmethod
    def _lookup_positions(positions: dict[str, float], joint_names: list[str]) -> list[float] | None:
        out = []
        for name in joint_names:
            if name not in positions:
                return None
            out.append(float(positions[name]))
        return out

    def send_trajectory_goal(
        self,
        client,
        joint_names: list[str],
        positions: list[float],
        label: str,
        *,
        time_from_start=None,
    ) -> bool:
        """Send one FollowJointTrajectory goal to an action server."""
        if not client.server_is_ready():
            self._warn_throttled(f"Action server is not ready for {label}; dropping command.")
            return False

        goal_msg = self.FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = joint_names

        point = self.JointTrajectoryPoint()
        point.positions = [float(value) for value in positions]
        point.time_from_start = time_from_start if time_from_start is not None else self.time_from_start
        goal_msg.trajectory.points = [point]

        future = client.send_goal_async(goal_msg)
        future.add_done_callback(lambda done, group=label: self._goal_response_cb(done, group))
        return True

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
        description="Forward Quest3 /target_robot/joint_commands JointState messages to TI5 T170C actions."
    )
    parser.add_argument("--joint-command-topic", default="/target_robot/joint_commands")
    parser.add_argument("--reset-topic", default="/custom/custom_a")
    parser.add_argument("--reset-threshold", type=float, default=0.5)
    parser.add_argument(
        "--left-arm-action",
        default="/ti5_t170c_left_arm_controller/follow_joint_trajectory",
    )
    parser.add_argument(
        "--right-arm-action",
        default="/ti5_t170c_right_arm_controller/follow_joint_trajectory",
    )
    parser.add_argument("--time-from-start-sec", type=float, default=0.1)
    parser.add_argument("--reset-duration-sec", type=float, default=2.0)
    parser.add_argument("--min-send-period-sec", type=float, default=0.0)
    parser.add_argument("--wait-timeout-sec", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    import rclpy

    rclpy.init(args=None)
    node = JointCommandToTi5T170CNode(
        topic=args.joint_command_topic,
        reset_topic=args.reset_topic,
        reset_threshold=args.reset_threshold,
        action_servers=ActionServers(
            left_arm=args.left_arm_action,
            right_arm=args.right_arm_action,
        ),
        time_from_start_sec=args.time_from_start_sec,
        reset_duration_sec=args.reset_duration_sec,
        min_send_period_sec=args.min_send_period_sec,
        wait_timeout_sec=args.wait_timeout_sec,
    )
    try:
        node.spin()
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
