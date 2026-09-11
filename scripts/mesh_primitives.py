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


def loft_tube(
    path: np.ndarray,
    radii: Sequence[float] | np.ndarray,
    radial: int = 8,
    *,
    caps: bool = False,
) -> trimesh.Trimesh:
    """Loft a rounded (circular) tube along a polyline with per-sample radius."""
    pts = np.asarray(path, dtype=np.float64)
    rad = np.asarray(radii, dtype=np.float64)
    if len(pts) < 2:
        raise ValueError("path too short")
    if rad.shape[0] != len(pts):
        rad = np.linspace(float(rad.flat[0]), float(rad.flat[-1]), len(pts))
    tangents = np.gradient(pts, axis=0)
    tangents /= np.clip(np.linalg.norm(tangents, axis=1, keepdims=True), 1e-9, None)
    ref = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(tangents[len(tangents) // 2], ref)) > 0.85:
        ref = np.array([1.0, 0.0, 0.0])
    normals = np.zeros_like(pts)
    binormals = np.zeros_like(pts)
    normals[0] = np.cross(tangents[0], ref)
    normals[0] /= max(np.linalg.norm(normals[0]), 1e-9)
    binormals[0] = np.cross(tangents[0], normals[0])
    for i in range(1, len(pts)):
        n = normals[i - 1] - tangents[i] * np.dot(tangents[i], normals[i - 1])
        n /= max(np.linalg.norm(n), 1e-9)
        normals[i] = n
        binormals[i] = np.cross(tangents[i], n)
        binormals[i] /= max(np.linalg.norm(binormals[i]), 1e-9)
    angles = np.linspace(0.0, 2.0 * math.pi, radial, endpoint=False)
    verts = []
    for p, n, b, r in zip(pts, normals, binormals, rad):
        for ang in angles:
            verts.append(p + r * (math.cos(ang) * n + math.sin(ang) * b))
    verts = np.asarray(verts, dtype=np.float64)
    faces = []
    nseg = len(pts) - 1
    for i in range(nseg):
        for j in range(radial):
            j2 = (j + 1) % radial
            a = i * radial + j
            b0 = i * radial + j2
            c = (i + 1) * radial + j2
            d = (i + 1) * radial + j
            faces.append([a, b0, c])
            faces.append([a, c, d])
    if caps:
        # triangle fans at ends
        c0 = verts[:radial].mean(0)
        c1 = verts[-radial:].mean(0)
        verts = np.vstack([verts, c0, c1])
        i0, i1 = len(verts) - 2, len(verts) - 1
        last = nseg * radial
        for j in range(radial):
            j2 = (j + 1) % radial
            faces.append([i0, j2, j])
            faces.append([i1, last + j, last + j2])
    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=True)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def _profile_thin_mid(t: np.ndarray, end: float, mid: float) -> np.ndarray:
    belly = 4.0 * t * (1.0 - t)
    return end * (1.0 - belly) + mid * belly


def attachment_pad(
    center: Sequence[float],
    tangent: Sequence[float],
    *,
    major: float = 0.011,
    minor: float = 0.0065,
    thickness: float = 0.0026,
    bone_normal: Sequence[float] | None = None,
) -> trimesh.Trimesh:
    """Flattened oval footprint that sits on bone — not a conical fiber tip."""
    c = np.asarray(center, dtype=np.float64)
    t = np.asarray(tangent, dtype=np.float64)
    tn = np.linalg.norm(t)
    t = t / tn if tn > 1e-9 else np.array([0.0, 1.0, 0.0])
    if bone_normal is None:
        n = -t
    else:
        n = np.asarray(bone_normal, dtype=np.float64)
        nn = np.linalg.norm(n)
        n = n / nn if nn > 1e-9 else -t
    x, y, z = _orthonormal_frame(n)
    # Flatten along the incoming fiber so the pad reads as a bony flare.
    mesh = trimesh.creation.cylinder(radius=1.0, height=max(thickness, 0.0016), sections=22)
    scale = np.eye(4)
    scale[0, 0] = major
    scale[1, 1] = minor
    scale[2, 2] = 1.0
    mesh.apply_transform(scale)
    rot = np.eye(4)
    rot[:3, 0] = x
    rot[:3, 1] = y
    rot[:3, 2] = z
    mesh.apply_transform(rot)
    mesh.apply_translation(c + n * (thickness * 0.15))
    return mesh


def fascicle_bundle(
    a: Sequence[float],
    b: Sequence[float],
    *,
    sag: Sequence[float] | None = None,
    wrap: Sequence[float] | None = None,
    n_fibers: int = 12,
    radius_end: float = 0.00185,
    radius_mid: float = 0.00105,
    spread_end: float = 0.0115,
    spread_mid: float = 0.0017,
    samples: int = 28,
    radial: int = 8,
    rings: int = 2,
) -> trimesh.Trimesh:
    """Tapered rounded fascicles along a Bézier — fan at attachments, wrap the joint."""
    pa = np.asarray(a, dtype=np.float64)
    pb = np.asarray(b, dtype=np.float64)
    mid = (pa + pb) / 2.0
    if sag is None:
        length = float(np.linalg.norm(pb - pa))
        sag_v = np.array([0.0, -0.08 * length, -0.04 * length]) if length > 1e-6 else np.zeros(3)
    else:
        sag_v = np.asarray(sag, dtype=np.float64)
    if wrap is not None:
        w = np.asarray(wrap, dtype=np.float64)
        c1 = pa * 0.38 + w * 0.62 + sag_v * 0.22
        c2 = pb * 0.38 + w * 0.62 + sag_v * 0.22
    else:
        c1 = pa * 0.52 + mid * 0.48 + sag_v * 0.55
        c2 = pb * 0.52 + mid * 0.48 + sag_v * 0.55
    center = bezier_cubic(pa, c1, c2, pb, samples)
    tangents = np.gradient(center, axis=0)
    tangents /= np.clip(np.linalg.norm(tangents, axis=1, keepdims=True), 1e-9, None)
    # Parallel-transport a frame so curvature around the joint stays smooth.
    ref = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(tangents[0], ref)) > 0.9:
        ref = np.array([1.0, 0.0, 0.0])
    side0 = np.cross(tangents[0], ref)
    side0 /= max(np.linalg.norm(side0), 1e-9)
    sides = np.zeros_like(center)
    nrms = np.zeros_like(center)
    sides[0] = side0
    nrms[0] = np.cross(tangents[0], sides[0])
    nrms[0] /= max(np.linalg.norm(nrms[0]), 1e-9)
    for i in range(1, len(center)):
        s = sides[i - 1] - tangents[i] * np.dot(tangents[i], sides[i - 1])
        s /= max(np.linalg.norm(s), 1e-9)
        sides[i] = s
        n = np.cross(tangents[i], s)
        nrms[i] = n / max(np.linalg.norm(n), 1e-9)

    ts = np.linspace(0.0, 1.0, samples)
    # Stronger flare at the bony attachments, thinner mid-substance.
    spread = _profile_thin_mid(ts, spread_end, spread_mid)
    radii = _profile_thin_mid(ts, radius_end, radius_mid)
    parts: list[trimesh.Trimesh] = []
    n_fibers = max(4, int(n_fibers))
    ring_specs = [(n_fibers, 1.0)]
    if rings >= 2:
        ring_specs.append((max(n_fibers // 2, 4), 0.42))
    fiber_index = 0
    for count, scale in ring_specs:
        for i in range(count):
            base_ang = (2.0 * math.pi * i) / count + 0.11 * fiber_index
            twist = 0.55 * ts
            ang = base_ang + twist
            pack = (np.cos(ang)[:, None] * sides + np.sin(ang)[:, None] * nrms) * scale
            jitter = nrms * (0.0007 * math.sin(fiber_index * 1.9)) + sides * (
                0.0005 * math.cos(fiber_index * 1.4)
            )
            path = center + pack * spread[:, None] + jitter
            r = radii * (0.78 + 0.22 * (0.5 + 0.5 * math.sin(fiber_index * 2.3)))
            r = r * (0.92 + 0.08 * scale)
            parts.append(loft_tube(path, r, radial=radial, caps=True))
            fiber_index += 1
    # Flattened bony footprints so endings blend onto landmarks instead of tapering to a point.
    t0 = center[1] - center[0]
    t1 = center[-1] - center[-2]
    pad_major = max(spread_end * 1.15, 0.0075)
    pad_minor = max(spread_end * 0.62, 0.0044)
    parts.append(attachment_pad(pa, t0, major=pad_major, minor=pad_minor, bone_normal=-t0))
    parts.append(attachment_pad(pb, t1, major=pad_major, minor=pad_minor, bone_normal=t1))
    merged = trimesh.util.concatenate(parts)
    merged.merge_vertices()
    return merged


def wrap_panel(
    a: Sequence[float],
    b: Sequence[float],
    *,
    radius_a: float,
    radius_b: float,
    theta0: float,
    theta1: float,
    oval: tuple[float, float] = (1.0, 0.78),
    length_samples: int = 16,
    theta_samples: int = 18,
    thickness: float = 0.0017,
    lateral: np.ndarray | None = None,
) -> trimesh.Trimesh:
    """Open wrap sheet (not a closed cylinder) with slightly irregular borders."""
    pa = np.asarray(a, dtype=np.float64)
    pb = np.asarray(b, dtype=np.float64)
    axis = pb - pa
    length = float(np.linalg.norm(axis))
    if length < 1e-6:
        raise ValueError("degenerate wrap")
    z = axis / length
    if lateral is None:
        helper = np.array([1.0, 0.0, 0.0]) if abs(z[0]) < 0.85 else np.array([0.0, 0.0, 1.0])
        lat = np.cross(helper, z)
        lat /= max(np.linalg.norm(lat), 1e-9)
    else:
        lat = np.asarray(lateral, dtype=np.float64)
        lat = lat - z * np.dot(lat, z)
        lat /= max(np.linalg.norm(lat), 1e-9)
    ant = np.cross(z, lat)
    ant /= max(np.linalg.norm(ant), 1e-9)

    verts_a = []
    verts_b = []
    for i in range(length_samples):
        t = i / (length_samples - 1)
        center = pa * (1.0 - t) + pb * t
        radius = radius_a * (1.0 - t) + radius_b * t
        radius *= 1.0 + 0.045 * math.sin(t * 7.3)
        # slightly narrower angular span at the ends
        pinch = 0.1 * (1.0 - 4.0 * t * (1.0 - t))
        ta = theta0 + pinch + 0.06 * math.sin(t * 9.0)
        tb = theta1 - pinch + 0.05 * math.cos(t * 8.0)
        for j in range(theta_samples):
            s = j / (theta_samples - 1)
            th = ta * (1.0 - s) + tb * s
            # scalloped free edges
            edge = min(s, 1.0 - s)
            scallop = 1.0 - 0.08 * (1.0 - smooth_edge(edge)) * abs(math.sin(t * 11.0 + s * 4.0))
            rr = radius * scallop
            offset = (oval[0] * math.cos(th) * lat + oval[1] * math.sin(th) * ant) * rr
            p = center + offset
            n = offset / max(np.linalg.norm(offset), 1e-9)
            verts_a.append(p + n * (thickness * 0.5))
            verts_b.append(p - n * (thickness * 0.5))

    def _grid_faces(base: int) -> list[list[int]]:
        faces = []
        for i in range(length_samples - 1):
            for j in range(theta_samples - 1):
                a0 = base + i * theta_samples + j
                b0 = a0 + 1
                c0 = base + (i + 1) * theta_samples + j + 1
                d0 = c0 - 1
                faces.append([a0, b0, c0])
                faces.append([a0, c0, d0])
        return faces

    n_outer = length_samples * theta_samples
    verts = np.vstack([np.asarray(verts_a), np.asarray(verts_b)])
    faces = _grid_faces(0) + [[x + n_outer, z + n_outer, y + n_outer] for x, y, z in _grid_faces(0)]
    # stitch the two open long edges
    for i in range(length_samples - 1):
        for edge_j in (0, theta_samples - 1):
            a0 = i * theta_samples + edge_j
            b0 = (i + 1) * theta_samples + edge_j
            c0 = b0 + n_outer
            d0 = a0 + n_outer
            if edge_j == 0:
                faces.append([a0, b0, c0])
                faces.append([a0, c0, d0])
            else:
                faces.append([a0, c0, b0])
                faces.append([a0, d0, c0])
    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=True)
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def smooth_edge(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


def grid_sheet(
    cols: Sequence[Sequence[Sequence[float]]],
    thickness: float = 0.0022,
) -> trimesh.Trimesh:
    """Thin sheet from a (rows x cols) grid of points, offset along estimated normals."""
    grid = np.asarray(cols, dtype=np.float64)
    rows, cols_n = grid.shape[:2]
    if rows < 2 or cols_n < 2:
        raise ValueError("grid too small")
    normals = np.zeros_like(grid)
    for i in range(rows):
        for j in range(cols_n):
            du = grid[min(i + 1, rows - 1), j] - grid[max(i - 1, 0), j]
            dv = grid[i, min(j + 1, cols_n - 1)] - grid[i, max(j - 1, 0)]
            n = np.cross(du, dv)
            ln = np.linalg.norm(n)
            normals[i, j] = n / ln if ln > 1e-9 else np.array([0.0, 0.0, 1.0])
    outer = (grid + normals * (thickness * 0.5)).reshape(-1, 3)
    inner = (grid - normals * (thickness * 0.5)).reshape(-1, 3)
    verts = np.vstack([outer, inner])
    faces = []

    def idx(i, j, layer):
        return layer * rows * cols_n + i * cols_n + j

    for i in range(rows - 1):
        for j in range(cols_n - 1):
            a, b, c, d = idx(i, j, 0), idx(i, j + 1, 0), idx(i + 1, j + 1, 0), idx(i + 1, j, 0)
            faces += [[a, b, c], [a, c, d]]
            a, b, c, d = idx(i, j, 1), idx(i + 1, j, 1), idx(i + 1, j + 1, 1), idx(i, j + 1, 1)
            faces += [[a, b, c], [a, c, d]]
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
