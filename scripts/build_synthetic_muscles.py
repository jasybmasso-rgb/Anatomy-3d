"""Landmark-anchored muscles missing from BodyParts3D 4.0.

Latissimus / rectus / abdominal wall / mastication: schematic solids on the
same worldMatrix as skeleton.glb. Not cadaver segmentations.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

from mesh_primitives import bezier_cubic, grid_sheet, loft_tube

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"
SKELETON_GLB = ROOT / "public" / "models" / "skeleton.glb"

SYNTH_NOTES = (
    "Schéma pédagogique ancré sur le squelette BodyParts3D (même worldMatrix). "
    "BodyParts3D 4.0 n’a pas d’OBJ dédié. Attachments selon O/I classiques ; "
    "ce n’est pas une segmentation cadavérique."
)

MUSCLE_RED = np.array([196, 72, 58, 255], dtype=np.uint8)
TENDON_WHITE = np.array([245, 236, 214, 255], dtype=np.uint8)

_BONE_VERTS: np.ndarray | None = None


def load_lm() -> dict[str, np.ndarray]:
    data = json.loads(LANDMARKS.read_text(encoding="utf-8"))
    return {item["id"]: np.array(item["position"], dtype=float) for item in data["landmarks"]}


def mix(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    return a * (1.0 - t) + b * t


def off(p: np.ndarray, x: float = 0, y: float = 0, z: float = 0) -> np.ndarray:
    return p + np.array([x, y, z], dtype=float)


def _concat(parts: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    merged = trimesh.util.concatenate(parts)
    merged.merge_vertices()
    return merged


def _sheet(paths: list[np.ndarray], thickness: float) -> trimesh.Trimesh:
    grid = np.stack([np.asarray(path, dtype=np.float64) for path in paths], axis=0)
    return grid_sheet(grid, thickness=thickness)


def paint_tendon(mesh: trimesh.Trimesh, weights: np.ndarray) -> None:
    w = np.clip(np.asarray(weights, dtype=np.float64), 0.0, 1.0)
    if w.shape[0] != len(mesh.vertices):
        w = np.zeros(len(mesh.vertices), dtype=np.float64)
    colors = np.empty((len(mesh.vertices), 4), dtype=np.uint8)
    colors[:, 3] = 255
    colors[:, :3] = (
        MUSCLE_RED[:3][None, :] * (1.0 - w[:, None]) + TENDON_WHITE[:3][None, :] * w[:, None]
    ).astype(np.uint8)
    mesh.visual.vertex_colors = colors


def paint_solid(mesh: trimesh.Trimesh, rgba: np.ndarray = MUSCLE_RED) -> None:
    mesh.visual.vertex_colors = np.tile(rgba, (len(mesh.vertices), 1))


def _bone_verts() -> np.ndarray:
    global _BONE_VERTS
    if _BONE_VERTS is None:
        scene = trimesh.load(SKELETON_GLB, force="scene")
        geom = scene.geometry.get("bones")
        if geom is None:
            geom = next(iter(scene.geometry.values()))
        _BONE_VERTS = np.asarray(geom.vertices, dtype=np.float64)
    return _BONE_VERTS


def _side_mask(verts: np.ndarray, sx: float) -> np.ndarray:
    return verts[:, 0] * sx >= -0.002


def most_lateral(sx: float, y: float, z: float, ywin: float = 0.016, zwin: float = 0.028, extra: float = 0.0024) -> np.ndarray:
    """Outer table of the skull / ramus on this side, then a hair more lateral."""
    v = _bone_verts()
    mask = _side_mask(v, sx) & (np.abs(v[:, 1] - y) < ywin) & (np.abs(v[:, 2] - z) < zwin)
    pts = v[mask]
    if len(pts) < 4:
        mask = _side_mask(v, sx) & (np.abs(v[:, 1] - y) < ywin * 2.2) & (np.abs(v[:, 2] - z) < zwin * 2.2)
        pts = v[mask]
    if len(pts) == 0:
        return np.array([sx * 0.058, y, z], dtype=np.float64)
    p = pts[np.abs(pts[:, 0]).argmax()].copy()
    p[0] += sx * extra
    return p


def nearest_bone(point: np.ndarray, sx: float | None = None, extra: float = 0.0) -> np.ndarray:
    v = _bone_verts()
    if sx is not None:
        v = v[_side_mask(v, sx)]
    d = np.linalg.norm(v - point[None, :], axis=1)
    p = v[int(d.argmin())].copy()
    if sx is not None and extra:
        p[0] += sx * extra
    return p


# Taut anterior wall (pubis → umbilicus → costal arch → xiphoid), slightly
# proud of the bony ring. Not the subcostal "hole" at y≈0.26 which has no sternum.
_WALL_Y = np.array([-0.02, 0.04, 0.10, 0.16, 0.22, 0.28, 0.318], dtype=np.float64)
_WALL_Z = np.array([0.058, 0.074, 0.086, 0.092, 0.112, 0.152, 0.170], dtype=np.float64)
_FLANK_Y = np.array([-0.02, 0.04, 0.10, 0.16, 0.22, 0.28, 0.34], dtype=np.float64)
_FLANK_X = np.array([0.118, 0.128, 0.122, 0.116, 0.124, 0.132, 0.126], dtype=np.float64)
_FLANK_Z = np.array([0.042, 0.058, 0.044, 0.052, 0.082, 0.112, 0.098], dtype=np.float64)


def _wall_z(y: float | np.ndarray) -> np.ndarray | float:
    """Anterior abdominal wall (midline) from pubis to xiphoid."""
    out = np.interp(y, _WALL_Y, _WALL_Z)
    return out if isinstance(y, np.ndarray) else float(out)


def _flank_x(y: float | np.ndarray) -> np.ndarray | float:
    out = np.interp(y, _FLANK_Y, _FLANK_X)
    return out if isinstance(y, np.ndarray) else float(out)


def _flank_z(y: float | np.ndarray) -> np.ndarray | float:
    out = np.interp(y, _FLANK_Y, _FLANK_Z)
    return out if isinstance(y, np.ndarray) else float(out)


def _lat_wrap_path(origin: np.ndarray, insert: np.ndarray, sx: float, n: int = 26) -> np.ndarray:
    """C-shaped path: stay on the back, climb the flank, then tendon to the humerus."""
    back_x = sx * max(abs(float(origin[0])) + 0.05, 0.118)
    c1 = np.array([back_x, float(origin[1]) + 0.028, min(float(origin[2]), -0.026)])
    axilla_x = sx * 0.168
    c2 = np.array(
        [
            axilla_x,
            float(origin[1]) * 0.28 + float(insert[1]) * 0.72,
            0.010,
        ]
    )
    return bezier_cubic(origin, c1, c2, insert, n)


def _latissimus_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Thoracolumbar origin hugging the spinous line T7–L5, wrap to the humerus."""
    suf = "d" if sx < 0 else "g"
    t1, t12 = p["t1"], p["t12"]
    l1, l5 = p["l1"], p["l5"]

    def spinous(t_thoracic: float | None = None, t_lumbar: float | None = None) -> np.ndarray:
        if t_thoracic is not None:
            pt = mix(t1, t12, t_thoracic)
            z = -0.041 + 0.008 * t_thoracic
        else:
            pt = mix(l1, l5, t_lumbar or 0.0)
            z = -0.028 - 0.004 * (t_lumbar or 0.0)
        return np.array([sx * 0.0026, float(pt[1]), z], dtype=np.float64)

    # T7 ≈ 6/11 along T1→T12.
    spine = [
        spinous(t_thoracic=0.52),  # T7
        spinous(t_thoracic=0.62),  # T8
        spinous(t_thoracic=0.72),  # T9
        spinous(t_thoracic=0.82),  # T10
        spinous(t_thoracic=0.91),  # T11
        spinous(t_thoracic=1.00),  # T12
        spinous(t_lumbar=0.00),  # L1
        spinous(t_lumbar=0.25),
        spinous(t_lumbar=0.50),
        spinous(t_lumbar=0.75),
        spinous(t_lumbar=1.00),  # L5
    ]
    sac = off(p["sacrum"], x=sx * 0.010, y=0.010, z=-0.038)
    eips = off(p[f"eips-{suf}"], z=-0.016)
    crest = p[f"crete-iliaque-{suf}"]
    crest_post = mix(eips, crest, 0.38) + np.array([0.0, 0.006, -0.024])
    crest_lat = off(crest, x=sx * 0.010, z=-0.014)
    scap = off(p[f"angle-inf-scapula-{suf}"], x=sx * 0.008, y=-0.004, z=-0.014)
    rib11 = np.array([sx * 0.122, 0.198, -0.010], dtype=np.float64)
    rib9 = np.array([sx * 0.128, 0.246, -0.002], dtype=np.float64)

    head = p[f"tete-humerus-{suf}"]
    insert = head + np.array([sx * 0.010, -0.032, 0.026])

    # Posterior sheet along the spine so L/R meet at the thoracolumbar raphe.
    n_along = len(spine)
    n_across = 5
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i, origin in enumerate(spine):
        outer = origin + np.array([sx * 0.052, 0.0, 0.006])
        for j in range(n_across):
            s = j / (n_across - 1)
            grid[i, j] = mix(origin, outer, s)
    back_sheet = grid_sheet(grid, thickness=0.0056)

    origins = spine + [sac, eips, crest_post, crest_lat, rib11, rib9, scap]
    paths = [_lat_wrap_path(origin, insert, sx) for origin in origins]
    wrap = _sheet(paths, thickness=0.0064)
    fold = _lat_wrap_path(rib9, insert, sx)
    border = loft_tube(fold, np.linspace(0.0048, 0.0022, len(fold)), radial=8, caps=True)
    tendon_path = bezier_cubic(
        np.array([sx * 0.152, 0.39, 0.016]),
        np.array([sx * 0.160, 0.43, 0.028]),
        insert + np.array([sx * 0.006, -0.006, 0.006]),
        insert,
        12,
    )
    tendon = loft_tube(tendon_path, np.linspace(0.0050, 0.0026, 12), radial=8, caps=True)
    mesh = _concat([back_sheet, wrap, border, tendon])
    v = np.asarray(mesh.vertices)
    # Whitish tendon near the humeral insertion.
    dist = np.linalg.norm(v - insert[None, :], axis=1)
    w = np.clip((0.055 - dist) / 0.040, 0.0, 1.0)
    paint_tendon(mesh, w)
    return mesh


def _rectus_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Wide paramedian belly; medial edge meets the linea alba."""
    pub = off(p["symphyse-pubienne"], x=sx * 0.004, y=0.012, z=0.012)
    xiph = off(p["xiphoide"], x=sx * 0.012, z=0.002)
    costal = off(p["xiphoide"], x=sx * 0.048, y=-0.018, z=-0.006)
    # Three inscriptions → four pads / side; the upper three pairs are the six-pack.
    bands = (0.18, 0.40, 0.62)

    n_along = 40
    n_across = 10
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        t = i / (n_along - 1)
        ins = max(np.exp(-(((t - b) / 0.028) ** 2)) for b in bands)
        end = np.exp(-(t / 0.065) ** 2) + np.exp(-(((1.0 - t) / 0.075) ** 2))
        pinch = max(ins, 0.62 * end)
        y = float(mix(pub, mix(xiph, costal, 0.30), t)[1])
        z = float(_wall_z(y)) + 0.0055 * (1.0 - 0.78 * pinch)
        inner = 0.0042
        width = 0.058 * (1.0 - 0.38 * pinch)
        for j in range(n_across):
            s = j / (n_across - 1)
            # Round the lateral profile (less boxy).
            bulge = 0.55 + 0.45 * np.sin(s * np.pi)
            x = sx * (inner + s * width * (0.82 + 0.18 * bulge))
            grid[i, j] = np.array([x, y, z], dtype=np.float64)

    sheet = grid_sheet(grid, thickness=0.0125)
    v = np.asarray(sheet.vertices)
    y0, y1 = float(v[:, 1].min()), float(v[:, 1].max())
    t = (v[:, 1] - y0) / max(y1 - y0, 1e-6)
    w = np.zeros(len(v), dtype=np.float64)
    for b in bands:
        w = np.maximum(w, np.exp(-(((t - b) / 0.016) ** 2)))
    w = np.maximum(w, 0.95 * np.exp(-(t / 0.042) ** 2))
    w = np.maximum(w, 0.95 * np.exp(-(((1.0 - t) / 0.046) ** 2)))
    paint_tendon(sheet, w)
    return sheet


def _linea_alba(p: dict[str, np.ndarray]) -> trimesh.Trimesh:
    pub = off(p["symphyse-pubienne"], y=0.010, z=0.014)
    xiph = off(p["xiphoide"], z=0.004)
    n_along, n_across = 30, 4
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        t = i / (n_along - 1)
        y = float(mix(pub, xiph, t)[1])
        z = float(_wall_z(y)) + 0.0075
        half = 0.0044
        for j in range(n_across):
            s = j / (n_across - 1)
            grid[i, j] = np.array([-half + s * 2.0 * half, y, z], dtype=np.float64)
    sheet = grid_sheet(grid, thickness=0.0032)
    paint_solid(sheet, TENDON_WHITE)
    return sheet


def _abdominal_wrap(
    sx: float,
    y_top: float,
    y_bot: float,
    depth: float,
    *,
    n_along: int = 16,
    n_across: int = 9,
    linea: float = 0.006,
    diagonal: float = 0.0,
    x_scale: float = 1.0,
) -> np.ndarray:
    """Flank → linea alba on the torso envelope.

    diagonal>0 skews fibers superomedial (IO); <0 inferomedial (EO).
    depth>0 sits deep to the rectus wall.
    """
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        ty = i / (n_along - 1)
        y = y_top * (1.0 - ty) + y_bot * ty
        z_ant = float(_wall_z(y)) - depth
        x_lat = float(_flank_x(y)) * x_scale * (0.96 + 0.04 * np.sin(ty * np.pi))
        z_lat = float(_flank_z(y)) - depth * 0.45
        for j in range(n_across):
            s = j / (n_across - 1)
            y_fiber = y + diagonal * (0.5 - s) * 0.048
            # Quarter-ellipse: lateral (s=0) → anterior midline (s=1).
            x = sx * mix(x_lat, linea, s**0.88)
            z = mix(z_lat, z_ant, s**1.22)
            grid[i, j] = np.array([x, y_fiber, z], dtype=np.float64)
    return grid


def _internal_oblique_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Intermediate wall: iliac crest / inguinal → ribs 10–12 and linea alba."""
    grid = _abdominal_wrap(
        sx,
        y_top=0.272,
        y_bot=0.010,
        depth=0.0048,
        n_along=18,
        n_across=11,
        linea=0.006,
        diagonal=0.90,
        x_scale=1.0,
    )
    sheet = grid_sheet(grid, thickness=0.0054)
    v = np.asarray(sheet.vertices)
    w = np.clip((0.050 - np.abs(v[:, 0])) / 0.024, 0.0, 1.0)
    paint_tendon(sheet, w)
    return sheet


def _transversus_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Deepest wall: horizontal fibers; posterior rectus sheath at the midline."""
    grid = _abdominal_wrap(
        sx,
        y_top=0.278,
        y_bot=0.008,
        depth=0.0105,
        n_along=16,
        n_across=11,
        linea=0.0055,
        diagonal=0.0,
        x_scale=0.96,
    )
    sheet = grid_sheet(grid, thickness=0.0042)
    v = np.asarray(sheet.vertices)
    w = np.clip((0.048 - np.abs(v[:, 0])) / 0.022, 0.0, 1.0)
    paint_tendon(sheet, w)
    return sheet


def _eo_aponeurosis_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """White anterior rectus sheath: EO aponeurosis passing superficial to rectus."""
    n_along, n_across = 16, 8
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    y_top, y_bot = 0.302, 0.006
    for i in range(n_along):
        ty = i / (n_along - 1)
        y = y_top * (1.0 - ty) + y_bot * ty + (-0.55) * 0.0
        z = float(_wall_z(y)) + 0.012
        for j in range(n_across):
            s = j / (n_across - 1)
            y_fiber = y + (-0.50) * (0.5 - s) * 0.040
            grid[i, j] = np.array([sx * mix(0.060, 0.0048, s), y_fiber, z - 0.0012 * (1.0 - s)], dtype=np.float64)
    sheet = grid_sheet(grid, thickness=0.0024)
    paint_solid(sheet, TENDON_WHITE)
    return sheet


def enhance_external_oblique(mesh: trimesh.Trimesh, p: dict[str, np.ndarray] | None = None) -> trimesh.Trimesh:
    """Keep BP3D fleshy flank; snap medial sheet onto the wall as white aponeurosis."""
    m = mesh.copy()
    v = np.asarray(m.vertices, dtype=np.float64).copy()
    xabs = np.abs(v[:, 0])
    y = v[:, 1]
    z_wall = np.interp(y, _WALL_Y, _WALL_Z)
    abdomen = ((y > -0.03) & (y < 0.335) & (v[:, 2] > -0.03)).astype(np.float64)
    # White only over rectus (|x| ≲ 5–6 cm). Flank stays red.
    w = np.clip((0.058 - xabs) / 0.016, 0.0, 1.0) * abdomen
    target_z = z_wall + 0.012
    v[:, 2] = v[:, 2] * (1.0 - w) + target_z * w
    # Pull remaining anterior blobs down onto the wall (BP3D EO is a thick volume).
    too_front = np.clip((v[:, 2] - (z_wall + 0.024)) / 0.05, 0.0, 1.0) * abdomen * (1.0 - 0.35 * w)
    v[:, 2] -= too_front * (v[:, 2] - (z_wall + 0.007))
    m.vertices = v
    paint_tendon(m, w)
    if p is not None:
        apo = _concat([_eo_aponeurosis_side(p, -1.0), _eo_aponeurosis_side(p, 1.0)])
        m = _concat([m, apo])
    return m


def _temporalis_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Fan on the temporal fossa (up to the superior temporal line) → coronoid."""
    coronoid = most_lateral(sx, 0.624, 0.086, ywin=0.014, zwin=0.030, extra=0.0018)
    origins = [
        most_lateral(sx, 0.754, 0.022, ywin=0.012, zwin=0.028, extra=0.0010),
        most_lateral(sx, 0.746, 0.052, extra=0.0011),
        most_lateral(sx, 0.742, -0.008, extra=0.0011),
        most_lateral(sx, 0.728, 0.038, extra=0.0012),
        most_lateral(sx, 0.712, -0.012, extra=0.0011),
        most_lateral(sx, 0.698, 0.048, extra=0.0011),
        most_lateral(sx, 0.676, 0.008, extra=0.0010),
        most_lateral(sx, 0.662, 0.040, extra=0.0009),
    ]
    paths = []
    for origin in origins:
        c1 = mix(origin, coronoid, 0.30) + np.array([sx * 0.004, -0.002, 0.002])
        c2 = mix(origin, coronoid, 0.68)
        paths.append(bezier_cubic(origin, c1, c2, coronoid, 18))
    mesh = _sheet(paths, thickness=0.0064)
    paint_solid(mesh)
    return mesh


def _masseter_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    zyg_ant = most_lateral(sx, 0.644, 0.092, ywin=0.012, zwin=0.028, extra=0.0016)
    zyg_post = most_lateral(sx, 0.656, 0.052, ywin=0.012, zwin=0.024, extra=0.0016)
    angle = most_lateral(sx, 0.572, 0.068, ywin=0.014, zwin=0.028, extra=0.0016)
    ramus = most_lateral(sx, 0.604, 0.074, ywin=0.012, zwin=0.024, extra=0.0016)
    super_paths = []
    for t in (0.08, 0.34, 0.58, 0.86):
        o = mix(zyg_ant, zyg_post, t)
        dest = mix(angle, ramus, 0.18 + 0.40 * t)
        c1 = mix(o, dest, 0.40) + np.array([sx * 0.002, 0.0, 0.002])
        super_paths.append(bezier_cubic(o, c1, mix(o, dest, 0.78), dest, 14))
    deep_o = mix(zyg_ant, zyg_post, 0.72) + np.array([-sx * 0.003, 0.0, -0.004])
    deep = bezier_cubic(deep_o, mix(deep_o, ramus, 0.45), mix(deep_o, ramus, 0.75), ramus, 12)
    mesh = _concat(
        [_sheet(super_paths, thickness=0.0078), loft_tube(deep, np.full(12, 0.0038), radial=8, caps=True)]
    )
    paint_solid(mesh)
    return mesh


def _pterygoid_medial_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    sph = nearest_bone(np.array([sx * 0.022, 0.628, 0.056], dtype=np.float64), sx)
    maxil = nearest_bone(np.array([sx * 0.026, 0.612, 0.078], dtype=np.float64), sx)
    angle = nearest_bone(np.array([sx * 0.034, 0.566, 0.052], dtype=np.float64), sx)
    angle[0] -= sx * 0.004  # medial surface of the angle
    paths = []
    for origin in (sph, mix(sph, maxil, 0.55), maxil):
        c1 = mix(origin, angle, 0.42) + np.array([sx * 0.006, -0.004, -0.004])
        paths.append(bezier_cubic(origin, c1, mix(origin, angle, 0.75), angle, 14))
    mesh = _sheet(paths, thickness=0.0054)
    paint_solid(mesh)
    return mesh


def _pterygoid_lateral_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    sph = nearest_bone(np.array([sx * 0.024, 0.646, 0.050], dtype=np.float64), sx)
    sph_inf = nearest_bone(np.array([sx * 0.022, 0.632, 0.056], dtype=np.float64), sx)
    condyle = most_lateral(sx, 0.646, 0.032, ywin=0.012, zwin=0.022, extra=0.0008)
    condyle[0] -= sx * 0.006  # fovea on the condylar neck, slightly medial to the joint
    paths = []
    for origin in (sph, sph_inf, mix(sph, sph_inf, 0.5)):
        c1 = mix(origin, condyle, 0.45) + np.array([sx * 0.005, 0.001, 0.001])
        paths.append(bezier_cubic(origin, c1, mix(origin, condyle, 0.78), condyle, 14))
    mesh = _sheet(paths, thickness=0.0048)
    paint_solid(mesh)
    return mesh


def _bilateral(builder, p: dict[str, np.ndarray]) -> trimesh.Trimesh:
    return _concat([builder(p, -1.0), builder(p, 1.0)])


def build() -> dict[str, trimesh.Trimesh]:
    p = load_lm()
    _ = _bone_verts()
    rectus = _concat([_rectus_side(p, -1.0), _rectus_side(p, 1.0), _linea_alba(p)])
    v = np.asarray(rectus.vertices)
    y0, y1 = float(v[:, 1].min()), float(v[:, 1].max())
    t = (v[:, 1] - y0) / max(y1 - y0, 1e-6)
    w = np.zeros(len(v), dtype=np.float64)
    for b in (0.18, 0.40, 0.62):
        w = np.maximum(w, np.exp(-(((t - b) / 0.016) ** 2)))
    w = np.maximum(w, 0.95 * np.exp(-(t / 0.042) ** 2))
    w = np.maximum(w, 0.95 * np.exp(-(((1.0 - t) / 0.046) ** 2)))
    w = np.maximum(w, np.clip((0.0055 - np.abs(v[:, 0])) / 0.003, 0.0, 1.0))
    paint_tendon(rectus, w)
    return {
        "grand-dorsal": _bilateral(_latissimus_side, p),
        "droit-abdomen": rectus,
        "oblique-interne": _bilateral(_internal_oblique_side, p),
        "transverse-de-l-abdomen": _bilateral(_transversus_side, p),
        "temporal": _bilateral(_temporalis_side, p),
        "masseter": _bilateral(_masseter_side, p),
        "pterygoide-medial": _bilateral(_pterygoid_medial_side, p),
        "pterygoide-lateral": _bilateral(_pterygoid_lateral_side, p),
    }


MASTICATION_KEYS = {
    "temporal": "temporalis",
    "masseter": "masseter",
    "pterygoide-medial": "medial pterygoid",
    "pterygoide-lateral": "lateral pterygoid",
}

SYNTH_KEYS = {
    "grand-dorsal": "latissimus dorsi",
    "droit-abdomen": "rectus abdominis",
    "oblique-interne": "internal oblique",
    "transverse-de-l-abdomen": "transversus abdominis",
    **MASTICATION_KEYS,
}
