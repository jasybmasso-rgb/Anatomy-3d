"""Lightweight mesh primitives for schematic anatomy (no Blender)."""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
import trimesh


def _orthonormal_frame(direction: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    d = np.asarray(direction, dtype=np.float64)
    n = np.linalg.norm(d)
    if n < 1e-9:
        d = np.array([0.0, 1.0, 0.0])
    else:
        d = d / n
    helper = np.array([0.0, 1.0, 0.0]) if abs(d[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x = np.cross(helper, d)
    x /= np.linalg.norm(x)
    y = np.cross(d, x)
    y /= np.linalg.norm(y)
    return x, y, d


def capsule_between(
    a: Sequence[float],
    b: Sequence[float],
    radius: float,
    sections: int = 10,
    radial: int = 10,
) -> trimesh.Trimesh:
    pa = np.asarray(a, dtype=np.float64)
    pb = np.asarray(b, dtype=np.float64)
    vec = pb - pa
    length = float(np.linalg.norm(vec))
    if length < 1e-6:
        return trimesh.creation.icosphere(subdivisions=2, radius=radius)
    mesh = trimesh.creation.capsule(radius=radius, height=length, count=[sections, radial])
    x, y, z = _orthonormal_frame(vec)
    rot = np.eye(4)
    rot[:3, 0] = x
    rot[:3, 1] = y
    rot[:3, 2] = z
    mesh.apply_transform(rot)
    mesh.apply_translation((pa + pb) / 2.0)
    return mesh


def bezier_cubic(p0, p1, p2, p3, n: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, n)
    omt = 1.0 - t
    pts = (
        (omt**3)[:, None] * p0
        + (3 * omt**2 * t)[:, None] * p1
        + (3 * omt * t**2)[:, None] * p2
        + (t**3)[:, None] * p3
    )
    return pts


def loft_ribbon(
    path: np.ndarray,
    width: float,
    thickness: float,
    binormal: np.ndarray | None = None,
) -> trimesh.Trimesh:
    """Loft a thin rectangular ribbon along a 3D polyline."""
    pts = np.asarray(path, dtype=np.float64)
    if len(pts) < 2:
        raise ValueError("path too short")
    tangents = np.gradient(pts, axis=0)
    tangents /= np.clip(np.linalg.norm(tangents, axis=1, keepdims=True), 1e-9, None)
    if binormal is None:
        ref = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(tangents[len(tangents) // 2], ref)) > 0.85:
            ref = np.array([1.0, 0.0, 0.0])
        normals = np.cross(tangents, ref)
        normals /= np.clip(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9, None)
        binormals = np.cross(tangents, normals)
        binormals /= np.clip(np.linalg.norm(binormals, axis=1, keepdims=True), 1e-9, None)
    else:
        b = np.asarray(binormal, dtype=np.float64)
        b = b / max(np.linalg.norm(b), 1e-9)
        binormals = np.tile(b, (len(pts), 1))
        normals = np.cross(binormals, tangents)
        normals /= np.clip(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9, None)
        binormals = np.cross(tangents, normals)
        binormals /= np.clip(np.linalg.norm(binormals, axis=1, keepdims=True), 1e-9, None)

    hw, ht = width / 2.0, thickness / 2.0
    verts = []
    for p, n, b in zip(pts, normals, binormals):
        verts.append(p + hw * n + ht * b)
        verts.append(p - hw * n + ht * b)
        verts.append(p - hw * n - ht * b)
        verts.append(p + hw * n - ht * b)
    verts = np.array(verts, dtype=np.float64)
    faces = []
    nseg = len(pts) - 1
    for i in range(nseg):
        a = i * 4
        c = (i + 1) * 4
        for j in range(4):
            j2 = (j + 1) % 4
            faces.append([a + j, a + j2, c + j2])
            faces.append([a + j, c + j2, c + j])
    # caps
    faces.append([0, 1, 2])
    faces.append([0, 2, 3])
    last = nseg * 4
    faces.append([last + 0, last + 2, last + 1])
    faces.append([last + 0, last + 3, last + 2])
    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=True)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def fiber_bundle(
    a: Sequence[float],
    b: Sequence[float],
    *,
    sag: Sequence[float] | None = None,
    width: float = 0.012,
    thickness: float = 0.0035,
    n_fibers: int = 5,
    spread: float = 0.008,
    samples: int = 18,
) -> trimesh.Trimesh:
    """Multi-fiber lofted ribbons along a cubic Bézier — schematic ligament bundle."""
    pa = np.asarray(a, dtype=np.float64)
    pb = np.asarray(b, dtype=np.float64)
    mid = (pa + pb) / 2.0
    if sag is None:
        vec = pb - pa
        length = float(np.linalg.norm(vec))
        sag_v = np.array([0.0, 0.0, 0.0])
        if length > 1e-6:
            # slight posterior/inferior sag
            sag_v = np.array([0.0, -0.08 * length, -0.04 * length])
    else:
        sag_v = np.asarray(sag, dtype=np.float64)
    c1 = pa * 0.55 + mid * 0.45 + sag_v * 0.35
    c2 = pb * 0.55 + mid * 0.45 + sag_v * 0.35
    center = bezier_cubic(pa, c1, c2, pb, samples)
    tangents = np.gradient(center, axis=0)
    tangents /= np.clip(np.linalg.norm(tangents, axis=1, keepdims=True), 1e-9, None)
    ref = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(tangents[len(tangents) // 2], ref)) > 0.9:
        ref = np.array([1.0, 0.0, 0.0])
    side = np.cross(tangents[len(tangents) // 2], ref)
    side /= max(np.linalg.norm(side), 1e-9)

    parts: list[trimesh.Trimesh] = []
    if n_fibers == 1:
        offsets = [0.0]
    else:
        offsets = np.linspace(-spread, spread, n_fibers)
    fiber_w = width / max(n_fibers * 0.95, 1.0)
    mid_t = tangents[len(tangents) // 2]
    nrm = np.cross(side, mid_t)
    nrm /= max(np.linalg.norm(nrm), 1e-9)
    for i, off in enumerate(offsets):
        stagger = nrm * (0.0022 * ((i % 3) - 1))
        path = center + side * off + stagger
        parts.append(loft_ribbon(path, width=max(fiber_w, 0.0016), thickness=thickness * 0.82))
    merged = trimesh.util.concatenate(parts)
    merged.merge_vertices()
    return merged


def torus_ring(
    center: Sequence[float],
    normal: Sequence[float],
    major: float,
    minor: float,
    major_sec: int = 28,
    minor_sec: int = 10,
) -> trimesh.Trimesh:
    mesh = trimesh.creation.torus(
        major_radius=major,
        minor_radius=minor,
        major_sections=major_sec,
        minor_sections=minor_sec,
    )
    n = np.asarray(normal, dtype=np.float64)
    n = n / max(np.linalg.norm(n), 1e-9)
    x, y, z = _orthonormal_frame(n)
    rot = np.eye(4)
    rot[:3, 0] = x
    rot[:3, 1] = y
    rot[:3, 2] = z
    mesh.apply_transform(rot)
    mesh.apply_translation(np.asarray(center, dtype=np.float64))
    return mesh


def wrap_sheet(
    points: Sequence[Sequence[float]],
    thickness: float,
) -> trimesh.Trimesh:
    """Convex hull of landmark cloud, then shrink along PCA to a thin shell."""
    cloud = np.asarray(points, dtype=np.float64)
    if len(cloud) < 4:
        raise ValueError("need ≥4 points")
    hull = trimesh.convex.convex_hull(cloud)
    hull.update_faces(hull.nondegenerate_faces())
    centroid = hull.centroid
    verts = hull.vertices.copy()
    centered = verts - centroid
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    thin_axis = vh[-1]
    projected = centered - np.outer(centered @ thin_axis, thin_axis)
    verts = centroid + projected + thin_axis * (thickness / 2.0) * np.sign(
        np.clip(centered @ thin_axis, -1, 1) + 1e-9
    )
    other = centroid + projected - thin_axis * (thickness / 2.0) * np.sign(
        np.clip(centered @ thin_axis, -1, 1) + 1e-9
    )
    all_v = np.vstack([verts, other])
    sheet = trimesh.convex.convex_hull(all_v)
    sheet.update_faces(sheet.nondegenerate_faces())
    return sheet


def band(a: Sequence[float], b: Sequence[float], radius: float) -> trimesh.Trimesh:
    """Legacy alias used by synthetic muscle stand-ins."""
    return capsule_between(a, b, radius)


def ribbon(
    a: Sequence[float],
    b: Sequence[float],
    width: float,
    thickness: float,
) -> trimesh.Trimesh:
    pa = np.asarray(a, dtype=np.float64)
    pb = np.asarray(b, dtype=np.float64)
    path = np.linspace(0.0, 1.0, 8)[:, None] * (pb - pa) + pa
    return loft_ribbon(path, width=width, thickness=thickness)


def disc(
    center: Sequence[float],
    normal: Sequence[float],
    radius: float,
    thickness: float,
) -> trimesh.Trimesh:
    mesh = trimesh.creation.cylinder(radius=radius, height=max(thickness, 0.0015), sections=20)
    n = np.asarray(normal, dtype=np.float64)
    x, y, z = _orthonormal_frame(n)
    rot = np.eye(4)
    rot[:3, 0] = x
    rot[:3, 1] = y
    rot[:3, 2] = z
    mesh.apply_transform(rot)
    mesh.apply_translation(np.asarray(center, dtype=np.float64))
    return mesh


def cylinder_sleeve(
    a: Sequence[float],
    b: Sequence[float],
    radius: float,
    thickness: float = 0.0025,
    sections: int = 28,
) -> trimesh.Trimesh:
    """Thin annular sleeve (deep fascia schematic), no boolean engine required."""
    pa = np.asarray(a, dtype=np.float64)
    pb = np.asarray(b, dtype=np.float64)
    vec = pb - pa
    height = float(np.linalg.norm(vec))
    if height < 1e-6:
        raise ValueError("degenerate sleeve")
    r_in = max(radius - thickness, radius * 0.82)
    sleeve = trimesh.creation.annulus(
        r_min=r_in, r_max=radius, height=height, sections=sections
    )
    x, y, z = _orthonormal_frame(vec)
    rot = np.eye(4)
    rot[:3, 0] = x
    rot[:3, 1] = y
    rot[:3, 2] = z
    sleeve.apply_transform(rot)
    sleeve.apply_translation((pa + pb) / 2.0)
    return sleeve
