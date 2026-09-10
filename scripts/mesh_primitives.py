"""Shared trimesh helpers for synthetic ligaments / fascia."""

from __future__ import annotations

import numpy as np
import trimesh


def band(a: np.ndarray, b: np.ndarray, radius: float, sections: int = 10) -> trimesh.Trimesh:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if np.linalg.norm(b - a) < 1e-4:
        return trimesh.creation.icosphere(subdivisions=1, radius=max(radius, 0.002))
    return trimesh.creation.cylinder(radius=radius, sections=sections, segment=(a, b))


def disc(center: np.ndarray, normal: np.ndarray, radius: float, thickness: float) -> trimesh.Trimesh:
    mesh = trimesh.creation.cylinder(radius=radius, height=thickness, sections=18)
    n = np.asarray(normal, dtype=float)
    if np.linalg.norm(n) < 1e-8:
        n = np.array([0.0, 1.0, 0.0])
    n = n / np.linalg.norm(n)
    rot = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], n)
    mesh.apply_transform(rot)
    mesh.apply_translation(center)
    return mesh


def sheet(corners: list[np.ndarray], thickness: float = 0.002) -> trimesh.Trimesh:
    """Thin quad from 4 corners (winding)."""
    pts = np.asarray(corners, dtype=float)
    if len(pts) != 4:
        raise ValueError("sheet expects 4 corners")
    faces = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 2], [0, 2, 1]])
    mesh = trimesh.Trimesh(vertices=pts, faces=faces, process=True)
    try:
        mesh = mesh.extrude(thickness)
    except Exception:
        pass
    if isinstance(mesh, trimesh.Trimesh):
        return mesh
    return trimesh.util.concatenate([g for g in mesh.geometry.values()])


def ribbon(a: np.ndarray, b: np.ndarray, width: float, thickness: float) -> trimesh.Trimesh:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    axis = b - a
    length = np.linalg.norm(axis)
    if length < 1e-4:
        return trimesh.creation.box(extents=[width, thickness, width])
    box = trimesh.creation.box(extents=[width, length, thickness])
    rot = trimesh.geometry.align_vectors([0.0, 1.0, 0.0], axis / length)
    box.apply_transform(rot)
    box.apply_translation((a + b) / 2)
    return box
