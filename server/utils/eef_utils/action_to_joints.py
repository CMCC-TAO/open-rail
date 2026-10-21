import numpy as np
import pink
from scipy.spatial.transform import Rotation

from .pink_single_arm_solver import PinkSingleArmKineSolver
from .rotation_transform import matrix_to_rot6d, rot6d_to_matrix


def get_pose_dim(rotation_type: str) -> int:
    if rotation_type in ("rpy_euler", "axis_angle"):
        return 6
    if rotation_type == "quat":
        return 7
    if rotation_type == "rot6d":
        return 9
    raise ValueError(f"Unsupported rotation_type: {rotation_type}")


def action_to_ee_poses(action: np.ndarray, rotation_type: str = "rpy_euler"):
    action = np.asarray(action, dtype=np.float64).ravel()
    pose_dim = get_pose_dim(rotation_type)
    if action.size < 2 * pose_dim + 2 or not np.isfinite(action).all():
        raise ValueError("action must contain two finite poses and two grippers")
    return (
        action[:pose_dim],
        action[pose_dim : 2 * pose_dim],
        action[2 * pose_dim],
        action[2 * pose_dim + 1],
    )


class ActionIKSolver:
    def __init__(
        self,
        urdf_path,
        reset_position,
        link_name,
        eef_action_key,
        joint_state_key,
        rotation_type="rpy_euler",
        ref_frame="world",
        *,
        dt=0.033,
        qp_solver="daqp",
        rot6d_convention="columns",
        max_iterations=100,
        stagnation_iterations=0,
    ):
        """Convert dual-arm EEF poses to joints with Pink.

        reset_position follows the full URDF configuration order. Quaternions
        use xyzw; Rot6D keeps the previous CasADi column convention by default.
        """
        pose_dim = get_pose_dim(rotation_type)
        if ref_frame not in ("world", "local"):
            raise ValueError(f"Unsupported ref_frame: {ref_frame}")
        self.rotation_type = rotation_type
        self.ref_frame = ref_frame
        self.ik_solver_type = "pink"
        self.link_name = link_name
        self.eef_action_key = {
            "left_arm": (0, pose_dim),
            "right_arm": (pose_dim, 2 * pose_dim),
            **eef_action_key,
        }
        self.joint_state_key = joint_state_key
        self.q_init = np.asarray(reset_position, dtype=np.float64).reshape(-1).copy()
        self._action_slices = self._make_slices(self.eef_action_key)
        self._state_slices = self._make_slices(joint_state_key)
        self.left_solver = PinkSingleArmKineSolver(
            urdf_path, link_name["left_base"], link_name["left_tip"], self.q_init,
            rot6d_convention=rot6d_convention, dt=dt, qp_solver=qp_solver,
            max_iterations=max_iterations, stagnation_iterations=stagnation_iterations,
        )
        self.right_solver = PinkSingleArmKineSolver(
            urdf_path, link_name["right_base"], link_name["right_tip"], self.q_init,
            rot6d_convention=rot6d_convention, dt=dt, qp_solver=qp_solver,
            max_iterations=max_iterations, stagnation_iterations=stagnation_iterations,
        )
        for side, solver in (("left", self.left_solver), ("right", self.right_solver)):
            arm_key = f"{side}_arm"
            action_slice = self._action_slices[arm_key]
            state_slice = self._state_slices[arm_key]
            if action_slice.stop - action_slice.start != pose_dim:
                raise ValueError(f"{arm_key} action width must be {pose_dim}")
            if state_slice.stop - state_slice.start != solver.model.nq:
                raise ValueError(f"{arm_key} state width must be {solver.model.nq}")
        self.q_left_init = self._initial_arm_configuration(self.left_solver)
        self.q_right_init = self._initial_arm_configuration(self.right_solver)
        self.last_successes = np.empty((0, 2), dtype=bool)

    @staticmethod
    def _make_slices(mapping):
        slices = {}
        for key in ("left_arm", "right_arm", "left_hand", "right_hand"):
            start, stop = mapping[key]
            if not isinstance(start, (int, np.integer)) or not isinstance(stop, (int, np.integer)):
                raise ValueError(f"{key} indices must be integers")
            if start < 0 or stop < start:
                raise ValueError(f"Invalid {key} slice: {mapping[key]}")
            slices[key] = slice(start, stop)
        return slices

    def _initial_arm_configuration(self, solver):
        joints = (
            solver.full_model.joints[solver.full_model.getJointId(name)]
            for name in solver.model.names[1:]
        )
        return np.concatenate([
            self.q_init[joint.idx_q : joint.idx_q + joint.nq] for joint in joints
        ])

    def _validate_state(self, state):
        state = np.asarray(state, dtype=np.float64)
        expected_dim = max(part.stop for part in self._state_slices.values())
        if state.ndim != 1 or state.size < expected_dim or not np.isfinite(state).all():
            raise ValueError(f"state must be a finite vector with at least {expected_dim} values")
        return state

    def _to_world_rot6d(self, poses, solver, seed):
        if len(poses) == 0:
            return np.empty((0, 9))
        position = poses[:, :3]
        orientation = poses[:, 3:]
        if self.rotation_type == "rot6d":
            rotation = rot6d_to_matrix(orientation, solver.rot6d_convention)
        elif self.rotation_type == "rpy_euler":
            rotation = Rotation.from_euler("xyz", orientation).as_matrix()
        elif self.rotation_type == "axis_angle":
            rotation = Rotation.from_rotvec(orientation).as_matrix()
        else:
            rotation = Rotation.from_quat(orientation).as_matrix()
        if self.ref_frame == "local":
            configuration = pink.Configuration(solver.model, solver.data, seed)
            base = configuration.get_transform_frame_to_world(solver.base_link_name)
            position = position @ base.rotation.T + base.translation
            rotation = base.rotation @ rotation
        return np.concatenate([
            position, matrix_to_rot6d(rotation, solver.rot6d_convention)
        ], axis=1)

    def process_chunk_batch(self, action_chunk, state=None):
        action_chunk = np.atleast_2d(np.asarray(action_chunk, dtype=np.float64))
        if action_chunk.ndim != 2 or not np.isfinite(action_chunk).all():
            raise ValueError("action_chunk must be a finite matrix")
        expected_dim = max(part.stop for part in self._action_slices.values())
        if action_chunk.shape[1] < expected_dim:
            return None
        if state is not None:
            state = self._validate_state(state)
        joints = []
        successes = []
        for side, solver, fallback in (
            ("left", self.left_solver, self.q_left_init),
            ("right", self.right_solver, self.q_right_init),
        ):
            arm_key = f"{side}_arm"
            seed = fallback if state is None else state[self._state_slices[arm_key]]
            poses = self._to_world_rot6d(
                action_chunk[:, self._action_slices[arm_key]], solver, seed
            )
            arm_joints, arm_successes = solver.solve_ik_batch(poses, seed)
            arm_joints = np.asarray(arm_joints, dtype=np.float64)
            if arm_joints.shape != (len(action_chunk), solver.model.nq):
                raise ValueError(f"Unexpected {arm_key} IK output shape: {arm_joints.shape}")
            if not np.isfinite(arm_joints).all():
                raise ValueError(f"Non-finite {arm_key} IK output")
            joints.append(arm_joints)
            successes.append(arm_successes)
        self.last_successes = np.asarray(successes, dtype=bool).T
        return np.concatenate([
            *joints,
            action_chunk[:, self._action_slices["left_hand"]],
            action_chunk[:, self._action_slices["right_hand"]],
        ], axis=1)

    process_chunk = process_chunk_batch

    def process_joint_state(self, joint):
        joint = self._validate_state(joint)
        poses = []
        for side, solver in (("left", self.left_solver), ("right", self.right_solver)):
            q = joint[self._state_slices[f"{side}_arm"]]
            configuration = pink.Configuration(solver.model, solver.data, q)
            if self.ref_frame == "local":
                transform = configuration.get_transform(solver.tip_link_name, solver.base_link_name)
            else:
                transform = configuration.get_transform_frame_to_world(solver.tip_link_name)
            rotation = Rotation.from_matrix(transform.rotation)
            if self.rotation_type == "rot6d":
                orientation = matrix_to_rot6d(transform.rotation, solver.rot6d_convention)
            elif self.rotation_type == "rpy_euler":
                orientation = rotation.as_euler("xyz")
            elif self.rotation_type == "axis_angle":
                orientation = rotation.as_rotvec()
            else:
                orientation = rotation.as_quat()
            poses.append(np.concatenate([transform.translation, orientation]))
        return np.concatenate([
            *poses,
            joint[self._state_slices["left_hand"]],
            joint[self._state_slices["right_hand"]],
        ])
