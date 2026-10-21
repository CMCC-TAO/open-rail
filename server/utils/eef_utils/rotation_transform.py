"""Rotation representation conversion helpers."""

import numpy as np


ROT6D_CONVENTIONS = ("rows", "columns")


def validate_rot6d_convention(rot6d_convention: str) -> str:
    """Validate and return a Rot6D row/column convention."""
    if rot6d_convention not in ROT6D_CONVENTIONS:
        raise ValueError(
            f"Unsupported rot6d_convention: {rot6d_convention}. "
            "Expected 'rows' or 'columns'."
        )
    return rot6d_convention


def rot6d_to_matrix(
    rot6d: np.ndarray,
    rot6d_convention: str = "columns",
) -> np.ndarray:
    """Convert Rot6D values to rotation matrices using Gram-Schmidt.

    Args:
        rot6d: Array with shape ``(..., 6)``.
        rot6d_convention: ``"columns"`` interprets the two 3D blocks as the
            first two columns of the matrix. ``"rows"`` interprets them as the
            first two rows. The default is ``"columns"``.

    Returns:
        Rotation matrices with shape ``(..., 3, 3)``.
    """
    convention = validate_rot6d_convention(rot6d_convention)
    rot6d = np.asarray(rot6d, dtype=float)
    if rot6d.shape[-1:] != (6,):
        raise ValueError(f"rot6d must have shape (..., 6), got {rot6d.shape}")
    if not np.isfinite(rot6d).all():
        raise ValueError("rot6d must contain only finite values")

    basis1 = rot6d[..., :3]
    basis2 = rot6d[..., 3:]
    basis1_norm = np.linalg.norm(basis1, axis=-1, keepdims=True)
    if np.any(basis1_norm <= 1e-12):
        raise ValueError("rot6d first basis vector must have non-zero norm")
    basis1 = basis1 / basis1_norm
    basis2 = basis2 - np.sum(
        basis1 * basis2, axis=-1, keepdims=True
    ) * basis1
    basis2_norm = np.linalg.norm(basis2, axis=-1, keepdims=True)
    if np.any(basis2_norm <= 1e-12):
        raise ValueError(
            "rot6d basis vectors must not be parallel or degenerate"
        )
    basis2 = basis2 / basis2_norm
    basis3 = np.cross(basis1, basis2, axis=-1)

    stack_axis = -2 if convention == "rows" else -1
    return np.stack([basis1, basis2, basis3], axis=stack_axis)


def matrix_to_rot6d(
    rotation_matrix: np.ndarray,
    rot6d_convention: str = "columns",
) -> np.ndarray:
    """Encode rotation matrices as two row or column blocks."""
    convention = validate_rot6d_convention(rot6d_convention)
    rotation_matrix = np.asarray(rotation_matrix, dtype=float)
    if rotation_matrix.shape[-2:] != (3, 3):
        raise ValueError(
            "rotation_matrix must have shape (..., 3, 3), "
            f"got {rotation_matrix.shape}"
        )
    if not np.isfinite(rotation_matrix).all():
        raise ValueError("rotation_matrix must contain only finite values")

    if convention == "rows":
        basis1 = rotation_matrix[..., 0, :]
        basis2 = rotation_matrix[..., 1, :]
    else:
        basis1 = rotation_matrix[..., :, 0]
        basis2 = rotation_matrix[..., :, 1]
    return np.concatenate([basis1, basis2], axis=-1)
