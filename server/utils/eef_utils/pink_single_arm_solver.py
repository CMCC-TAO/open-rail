"""Pink IK for reduced single-arm chains."""

from __future__ import annotations

import numpy as np
import pinocchio as pin
import pink
import qpsolvers

from .rotation_transform import rot6d_to_matrix, validate_rot6d_convention


class _SoftPositionLimitTask:
    """Quadratic hinge penalty outside a margin around URDF limits."""

    def __init__(self, model: pin.Model, weight: float, margin: float) -> None:
        if model.nq != model.nv:
            raise ValueError("Soft position limits require nq == nv")
        self.weight = float(weight)
        lower = np.asarray(model.lowerPositionLimit, dtype=float)
        upper = np.asarray(model.upperPositionLimit, dtype=float)
        self.valid = (
            np.isfinite(lower)
            & np.isfinite(upper)
            & (lower > -1e20)
            & (upper < 1e20)
            & (upper > lower)
        )
        margin = np.minimum(float(margin), np.maximum(upper - lower, 0.0) / 4.0)
        self.lower = lower + margin
        self.upper = upper - margin

    def compute_qp_objective(
        self, configuration: pink.Configuration
    ) -> tuple[np.ndarray, np.ndarray]:
        q = np.asarray(configuration.q, dtype=float)
        below = self.valid & (q < self.lower)
        above = self.valid & (q > self.upper)
        active = below | above
        error = np.zeros_like(q)
        error[below] = q[below] - self.lower[below]
        error[above] = q[above] - self.upper[above]
        return self.weight * np.diag(active), self.weight * error


class PinkSingleArmKineSolver:
    """Reduced single-arm Pink solver for EEF trajectories."""

    def __init__(
        self,
        urdf_path: str,
        base_link: str,
        tip_link: str,
        q_init: np.ndarray | None = None,
        rot6d_convention: str = "rows",
        *,
        max_iterations: int = 100,
        stagnation_iterations: int = 0,
        dt: float = 0.033,
        qp_solver: str = "daqp",
        position_cost: float = 1.0,
        orientation_cost: float = 1.0,
        task_gain: float = 1.0,
        lm_damping: float = 1e-6,
        damping: float = 1e-8,
        trans_error_tolerance: float = 1e-5,
        rot_error_tolerance: float = 1e-5,
        enforce_output_velocity_limits: bool = True,
        return_seed_on_failure: bool = True,
        limit_weight: float = 1e-6,
        limit_margin: float = 0.01,
    ) -> None:
        if qp_solver not in qpsolvers.available_solvers:
            raise ValueError(
                f"QP solver '{qp_solver}' is unavailable. Installed solvers: "
                f"{qpsolvers.available_solvers}"
            )
        if max_iterations <= 0:
            raise ValueError("max_iterations must be positive")
        if stagnation_iterations < 0:
            raise ValueError("stagnation_iterations must be non-negative")
        if dt <= 0.0:
            raise ValueError("dt must be positive")
        if not 0.0 < task_gain <= 1.0:
            raise ValueError("task_gain must be in (0, 1]")
        if position_cost < 0.0 or orientation_cost < 0.0:
            raise ValueError("task costs must be non-negative")
        if position_cost == 0.0 and orientation_cost == 0.0:
            raise ValueError("At least one frame-task cost must be positive")
        if damping < 0.0 or lm_damping < 0.0:
            raise ValueError("damping values must be non-negative")
        if trans_error_tolerance <= 0.0 or rot_error_tolerance <= 0.0:
            raise ValueError("IK error tolerances must be positive")
        if limit_weight <= 0.0 or limit_margin < 0.0:
            raise ValueError("Invalid soft position-limit parameters")
        if not np.isfinite(
            (
                dt,
                position_cost,
                orientation_cost,
                task_gain,
                lm_damping,
                damping,
                trans_error_tolerance,
                rot_error_tolerance,
                limit_weight,
                limit_margin,
            )
        ).all():
            raise ValueError("Pink solver parameters must be finite")

        self.urdf_path = str(urdf_path)
        self.base_link_name = base_link
        self.tip_link_name = tip_link
        self.rot6d_convention = validate_rot6d_convention(rot6d_convention)
        self.max_iterations = int(max_iterations)
        self.stagnation_iterations = int(stagnation_iterations)
        self.dt = float(dt)
        self.qp_solver = qp_solver
        self.position_cost = float(position_cost)
        self.orientation_cost = float(orientation_cost)
        self.task_gain = float(task_gain)
        self.lm_damping = float(lm_damping)
        self.damping = float(damping)
        self.trans_error_tolerance = float(trans_error_tolerance)
        self.rot_error_tolerance = float(rot_error_tolerance)
        self.enforce_output_velocity_limits = bool(enforce_output_velocity_limits)
        self.return_seed_on_failure = bool(return_seed_on_failure)
        self.limit_weight = float(limit_weight)
        self.limit_margin = float(limit_margin)

        self.full_model = pin.buildModelFromUrdf(self.urdf_path)
        self._validate_frames(self.full_model)
        full_q_init = (
            pin.neutral(self.full_model)
            if q_init is None
            else self._validate_q(q_init, self.full_model, "q_init")
        )
        joints_on_path = self._search_joints_in_model(
            self.full_model, self.base_link_name, self.tip_link_name
        )
        joints_to_lock = [
            joint_id
            for joint_id in range(1, self.full_model.njoints)
            if joint_id not in joints_on_path
        ]
        self.model = pin.buildReducedModel(
            self.full_model, joints_to_lock, full_q_init
        )
        self._validate_frames(self.model)
        self.data = self.model.createData()
        self._frame_task = pink.tasks.FrameTask(
            self.tip_link_name,
            position_cost=self.position_cost,
            orientation_cost=self.orientation_cost,
            lm_damping=self.lm_damping,
            gain=self.task_gain,
        )
        self._tasks = [
            self._frame_task,
            _SoftPositionLimitTask(self.model, self.limit_weight, self.limit_margin),
        ]
        self._velocity_limits = [pink.limits.VelocityLimit(self.model)]
        self._workspace_center, self._workspace_radius = self._position_workspace_bound()
        self.last_iterations = np.empty(0, dtype=int)
        self.last_stop_reasons: list[str] = []

    def _position_workspace_bound(self) -> tuple[np.ndarray | None, float]:
        """Conservative reach sphere for a fixed chain of revolute joints."""
        frame = self.model.frames[self.model.getFrameId(self.tip_link_name)]
        radius = float(np.linalg.norm(frame.placement.translation))
        joint_id = frame.parentJoint
        if joint_id == 0:
            return None, np.inf
        while True:
            if not self.model.joints[joint_id].shortname().startswith("JointModelR"):
                return None, np.inf
            parent_id = self.model.parents[joint_id]
            if parent_id == 0:
                return self.model.jointPlacements[joint_id].translation.copy(), radius
            radius += float(np.linalg.norm(self.model.jointPlacements[joint_id].translation))
            joint_id = parent_id

    def solve_ik_batch(
        self,
        target_ee_poses: np.ndarray,
        prev_pos: np.ndarray,
        ref_frame: str = "world",
        rotation_type: str = "rot6d",
        dt: float | None = None,
    ) -> tuple[np.ndarray, list[bool]]:
        if ref_frame != "world":
            raise ValueError("Pink WA2 fixture solver only supports ref_frame='world'")
        if rotation_type != "rot6d":
            raise ValueError(
                "Pink WA2 fixture solver only supports rotation_type='rot6d'"
            )

        step_dt = self.dt if dt is None else float(dt)
        if not np.isfinite(step_dt) or step_dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        targets = np.asarray(target_ee_poses, dtype=float)
        if targets.ndim != 2 or targets.shape[1] != 9:
            raise ValueError("target_ee_poses must have shape (steps, 9)")

        current_q = self._validate_q(prev_pos, self.model, "prev_pos")
        results = np.empty((len(targets), self.model.nq))
        success_flags: list[bool] = []
        iterations = []
        stop_reasons = []
        for index, target_pose in enumerate(targets):
            target = self._parse_rot6d_pose(target_pose)
            current_q, success = self._solve_target(target, current_q, step_dt)
            results[index] = current_q
            success_flags.append(success)
            iterations.append(self._iteration_count)
            stop_reasons.append(self._stop_reason)
        self.last_iterations = np.asarray(iterations, dtype=int)
        self.last_stop_reasons = stop_reasons
        return results, success_flags

    def _solve_target(
        self, target: pin.SE3, q_init: np.ndarray, dt: float
    ) -> tuple[np.ndarray, bool]:
        self._iteration_count = 0
        self._stop_reason = "iteration_limit"
        if (
            self.return_seed_on_failure
            and self._workspace_center is not None
            and np.linalg.norm(target.translation - self._workspace_center)
            > self._workspace_radius + self.trans_error_tolerance
        ):
            self._stop_reason = "unreachable_position"
            return q_init.copy(), False

        configuration = pink.Configuration(self.model, self.data, q_init)
        self._frame_task.set_target(target)

        raw_success = False
        best_error = np.inf
        stalled = 0
        for iteration in range(self.max_iterations + 1):
            position_error, orientation_error = self._target_error(
                configuration, target
            )
            if (
                position_error < self.trans_error_tolerance
                and orientation_error < self.rot_error_tolerance
            ):
                raw_success = True
                self._stop_reason = "converged"
                break
            if iteration == self.max_iterations:
                break
            if self.stagnation_iterations:
                error = (
                    self.position_cost * position_error**2
                    + self.orientation_cost * orientation_error**2
                )
                if error < best_error * (1.0 - 1e-6):
                    best_error = error
                    stalled = 0
                else:
                    stalled += 1
                if stalled >= self.stagnation_iterations:
                    self._stop_reason = "stalled"
                    break
            problem = pink.build_ik(
                configuration,
                self._tasks,
                dt,
                damping=self.damping,
                limits=self._velocity_limits,
            )
            self._iteration_count += 1
            solution = qpsolvers.solve_problem(problem, solver=self.qp_solver)
            if not solution.found or solution.x is None:
                self._stop_reason = "qp_failure"
                break
            configuration.integrate_inplace(np.asarray(solution.x) / dt, dt)

        result, success = self._finalize_result(
            target,
            q_init,
            np.asarray(configuration.q, dtype=float),
            raw_success,
            dt,
        )
        if raw_success and not success:
            self._stop_reason = "velocity_limited"
        return result, success

    def _finalize_result(
        self,
        target: pin.SE3,
        q_init: np.ndarray,
        raw_q: np.ndarray,
        raw_success: bool,
        dt: float,
    ) -> tuple[np.ndarray, bool]:
        raw_is_finite = bool(np.isfinite(raw_q).all())
        if not raw_is_finite:
            raw_success = False

        result_q = (
            q_init.copy()
            if not raw_success and self.return_seed_on_failure
            else raw_q.copy()
        )
        if self.enforce_output_velocity_limits and np.isfinite(result_q).all():
            output_delta = pin.difference(self.model, q_init, result_q)
            velocity_limits = np.asarray(self.model.velocityLimit, dtype=float)
            has_velocity_limit = (velocity_limits > 1e-10) & (velocity_limits < 1e20)
            max_delta = np.where(has_velocity_limit, velocity_limits * dt, np.inf)
            limited_delta = np.clip(output_delta, -max_delta, max_delta)
            result_q = pin.integrate(self.model, q_init, limited_delta)

        if not np.isfinite(result_q).all():
            return result_q, False

        configuration = pink.Configuration(self.model, self.data, result_q)
        position_error, orientation_error = self._target_error(configuration, target)
        success = bool(
            raw_success
            and position_error < self.trans_error_tolerance
            and orientation_error < self.rot_error_tolerance
        )
        return result_q, success

    def _target_error(
        self, configuration: pink.Configuration, target: pin.SE3
    ) -> tuple[float, float]:
        current = configuration.get_transform_frame_to_world(self.tip_link_name)
        position_error = float(
            np.linalg.norm(target.translation - current.translation)
        )
        rotation_delta = target.rotation @ current.rotation.T
        orientation_error = float(np.linalg.norm(pin.log3(rotation_delta)))
        return position_error, orientation_error

    def _parse_rot6d_pose(self, target_ee_pose: np.ndarray) -> pin.SE3:
        target = np.asarray(target_ee_pose, dtype=float).reshape(-1)
        if target.size != 9:
            raise ValueError(
                f"rot6d target pose must contain 9 values, got {target.size}"
            )
        if not np.isfinite(target).all():
            raise ValueError("target_ee_pose must contain only finite values")
        rotation = rot6d_to_matrix(target[3:], self.rot6d_convention)
        return pin.SE3(rotation, target[:3])

    @staticmethod
    def _validate_q(q: np.ndarray, model: pin.Model, name: str) -> np.ndarray:
        result = np.asarray(q, dtype=float).reshape(-1).copy()
        if result.size != model.nq:
            raise ValueError(
                f"{name} length mismatch: expected {model.nq}, got {result.size}"
            )
        if not np.isfinite(result).all():
            raise ValueError(f"{name} must contain only finite values")
        return result

    def _validate_frames(self, model: pin.Model) -> None:
        if not model.existFrame(self.base_link_name):
            raise RuntimeError(f"Base link not found: {self.base_link_name}")
        if not model.existFrame(self.tip_link_name):
            raise RuntimeError(f"Tip link not found: {self.tip_link_name}")

    @staticmethod
    def _get_ancestor_joints(model: pin.Model, frame_name: str) -> set[int]:
        joint_id = model.frames[model.getFrameId(frame_name)].parentJoint
        ancestors: set[int] = set()
        while joint_id > 0:
            ancestors.add(joint_id)
            joint_id = model.parents[joint_id]
        return ancestors

    @classmethod
    def _search_joints_in_model(
        cls, model: pin.Model, base_link: str, tip_link: str
    ) -> set[int]:
        tip_ancestors = cls._get_ancestor_joints(model, tip_link)
        base_ancestors = cls._get_ancestor_joints(model, base_link)
        return tip_ancestors - base_ancestors


__all__ = ["PinkSingleArmKineSolver"]
