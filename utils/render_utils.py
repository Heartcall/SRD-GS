import os

import imageio.v2 as imageio
import numpy as np


def _as_numpy(image):
    if hasattr(image, "detach"):
        image = image.detach().cpu().numpy()
    return np.asarray(image)


def save_img_u8(image, path):
    """Save an image in uint8 format for mesh export visualization."""
    array = _as_numpy(image)
    array = np.nan_to_num(array, nan=0.0, posinf=1.0, neginf=0.0)
    if array.dtype != np.uint8:
        array = np.clip(array, 0.0, 1.0)
        array = (array * 255.0 + 0.5).astype(np.uint8)
    if array.ndim == 3 and array.shape[-1] == 1:
        array = array[..., 0]
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    imageio.imwrite(path, array)


def save_img_f32(image, path):
    """Save a float32 image. Needs Runtime Verification for TIFF consumers."""
    array = _as_numpy(image)
    array = np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    imageio.imwrite(path, array)


def focus_point_fn(poses):
    """Compute the least-squares focus point of camera optical axes."""
    poses = np.asarray(poses)
    directions = poses[:, :3, 2:3]
    directions = directions / np.linalg.norm(directions, axis=1, keepdims=True)
    origins = poses[:, :3, 3:4]
    identity = np.eye(3, dtype=poses.dtype)[None]
    projection = identity - directions @ np.swapaxes(directions, -2, -1)
    normal_matrix = np.swapaxes(projection, -2, -1) @ projection
    focus = np.linalg.solve(
        normal_matrix.mean(axis=0),
        (normal_matrix @ origins).mean(axis=0),
    )
    return focus[:, 0]


def transform_poses_pca(poses):
    """
    Align poses with PCA and return transformed poses plus transform matrix.

    This compatibility helper follows the common NeRF preprocessing convention.
    Current mesh extraction only imports it; full unbounded-scene behavior still
    needs Runtime Verification with real cameras.
    """
    poses = np.asarray(poses)
    origins = poses[:, :3, 3]
    center = origins.mean(axis=0)
    centered = origins - center
    covariance = centered.T @ centered
    eigval, eigvec = np.linalg.eigh(covariance)
    order = np.argsort(eigval)[::-1]
    rotation = eigvec[:, order].T
    if np.linalg.det(rotation) < 0:
        rotation[-1] *= -1

    transform = np.eye(4, dtype=poses.dtype)
    transform[:3, :3] = rotation
    transform[:3, 3] = -rotation @ center

    homog = np.concatenate(
        [poses[:, :3, :4], np.broadcast_to(np.array([0, 0, 0, 1], dtype=poses.dtype), (poses.shape[0], 1, 4))],
        axis=1,
    )
    transformed = transform[None] @ homog
    return transformed[:, :3, :4], transform
