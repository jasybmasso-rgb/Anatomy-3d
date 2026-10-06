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


def _spinous_z(y: float) -> float:
    """Approximate spinous-process z so L/R latissimus sheets meet on the raphe."""
    ys = np.array([0.03, 0.07, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35], dtype=np.float64)
    zs = np.array([-0.035, -0.025, -0.017, -0.012, -0.021, -0.035, -0.042, -0.042], dtype=np.float64)
    return float(np.interp(y, ys, zs))


def _torso_point(sx: float, x_abs: float, y: float, layer: float) -> np.ndarray:
    """Point on the abdominal/flank envelope, then offset along the outward normal-ish +Z/X.

    layer > 0 sits superficial (EO); layer < 0 sits deep (TA).
    """
    x_lat = float(_flank_x(y))
    s = float(np.clip((x_lat - x_abs) / max(x_lat - 0.006, 0.02), 0.0, 1.0))
    z = float(mix(_flank_z(y), _wall_z(y), s**1.15)) + layer
    return np.array([sx * x_abs, y, z], dtype=np.float64)


_CAGE_PTS: np.ndarray | None = None
_DEEP_CLOUD = None
_DEEP_BACK_IDS = (
    "dentele-posterieur-inferieur",
    "iliocostal-thoracique",
    "iliocostal-lombaire",
    "longissimus-du-thorax",
)


def _cage_pts() -> np.ndarray:
    """Ribs + sternum + costal cartilages (excludes scapula / hanging arm)."""
    global _CAGE_PTS
    if _CAGE_PTS is None:
        v = _bone_verts()
        mask = (
            (v[:, 1] > 0.12)
            & (v[:, 1] < 0.50)
            & (np.abs(v[:, 0]) > 0.016)
            & (np.abs(v[:, 0]) < 0.165)
            & (v[:, 2] > -0.055)
            & (v[:, 2] < 0.175)
        )
        _CAGE_PTS = v[mask]
    return _CAGE_PTS


def _outer_rib(sx: float, y: float, prefer: str = "antero_lateral", extra: float = 0.0034) -> np.ndarray:
    """Outer table of the rib at this height — never the inner thoracic surface."""
    v = _cage_pts()
    mask = _side_mask(v, sx) & (np.abs(v[:, 1] - y) < 0.015)
    pts = v[mask]
    if len(pts) < 10:
        mask = _side_mask(v, sx) & (np.abs(v[:, 1] - y) < 0.028)
        pts = v[mask]
    if len(pts) == 0:
        z0 = 0.03 if prefer == "antero_lateral" else -0.02
        return np.array([sx * 0.12, y, z0], dtype=np.float64)
    axis = np.array([0.0, y, 0.035], dtype=np.float64)
    rel = pts - axis
    rad = np.hypot(rel[:, 0], rel[:, 2])
    if prefer == "antero_lateral":
        score = rad + 0.24 * np.abs(pts[:, 0]) + 0.10 * pts[:, 2]
    else:
        score = rad + 0.18 * np.abs(pts[:, 0]) - 0.18 * pts[:, 2]
    p = pts[int(score.argmax())].copy()
    out = p - axis
    out[1] = 0.0
    n = float(np.linalg.norm(out))
    if n > 1e-9:
        p = p + extra * (out / n)
    return p


def _project_outside_thorax(pt: np.ndarray, sx: float, standoff: float = 0.0030) -> np.ndarray:
    """If a point sits inside the rib envelope, project it onto the outer cage."""
    v = _cage_pts()
    y = float(pt[1])
    band = v[_side_mask(v, sx) & (np.abs(v[:, 1] - y) < 0.016)]
    if len(band) < 10:
        band = v[_side_mask(v, sx) & (np.abs(v[:, 1] - y) < 0.030)]
    if len(band) < 8:
        return np.asarray(pt, dtype=np.float64)
    axis = np.array([0.0, y, 0.040], dtype=np.float64)
    rel = band - axis
    br = np.hypot(rel[:, 0], rel[:, 2])
    bang = np.arctan2(rel[:, 2], rel[:, 0])
    p = np.asarray(pt, dtype=np.float64)
    pr = float(np.hypot(p[0] - axis[0], p[2] - axis[2]))
    pang = float(np.arctan2(p[2] - axis[2], p[0] - axis[0]))
    dth = np.abs((bang - pang + np.pi) % (2.0 * np.pi) - np.pi)
    sel = dth < 0.50
    env_r = float(np.percentile(br[sel] if np.any(sel) else br, 92))
    if pr >= env_r or pr < 1e-6:
        return p
    scale = (env_r + standoff) / pr
    out = p.copy()
    out[0] = axis[0] + (p[0] - axis[0]) * scale
    out[2] = axis[2] + (p[2] - axis[2]) * scale
    return out


def _anterior_costal(sx: float, x_abs: float, y: float) -> np.ndarray | None:
    """Most anterior costal cartilage / xiphoid at this laterality — outer table."""
    v = _bone_verts()
    mask = (
        _side_mask(v, sx)
        & (np.abs(v[:, 1] - y) < 0.014)
        & (np.abs(np.abs(v[:, 0]) - x_abs) < 0.024)
        & (v[:, 2] > 0.10)
        & (np.abs(v[:, 0]) < 0.082)
    )
    pts = v[mask]
    if len(pts) < 5:
        mask = (np.abs(v[:, 1] - y) < 0.022) & (np.abs(v[:, 0]) < 0.078) & (v[:, 2] > 0.10)
        pts = v[mask]
    if len(pts) == 0:
        return None
    p = pts[int(pts[:, 2].argmax())].copy()
    p[0] = sx * x_abs
    p[2] += 0.0022
    return p


def _chart_rib_slip(sx: float, y: float) -> np.ndarray:
    """Pre-outer-ribs EO/IO costal slip (nearest anterolateral rib, not the thorax interior)."""
    guess = np.array([sx * 0.122, y, float(_flank_z(y)) + 0.018], dtype=np.float64)
    return nearest_bone(guess, sx, extra=0.0022)


def _pubic_crest(sx: float, x_abs: float) -> np.ndarray:
    """Superior-anterior pubic crest from the symphysis toward the pubic tubercle."""
    v = _bone_verts()
    x_abs = float(np.clip(x_abs, 0.002, 0.028))
    mask = (
        _side_mask(v, sx)
        & (np.abs(np.abs(v[:, 0]) - x_abs) < 0.010)
        & (v[:, 1] > -0.075)
        & (v[:, 1] < -0.036)
        & (v[:, 2] > 0.050)
    )
    pts = v[mask]
    if len(pts) < 4:
        mask = (
            _side_mask(v, sx)
            & (v[:, 1] > -0.078)
            & (v[:, 1] < -0.032)
            & (v[:, 2] > 0.048)
            & (np.abs(v[:, 0]) < 0.048)
        )
        pts = v[mask]
        if len(pts):
            pts = pts[np.abs(np.abs(pts[:, 0]) - x_abs).argsort()[:14]]
    if len(pts) == 0:
        return np.array([sx * x_abs, -0.050, 0.084], dtype=np.float64)
    # Superior-anterior table of the pubic body (the crest), then a hair proud.
    score = 0.42 * pts[:, 1] + 0.58 * pts[:, 2]
    p = pts[int(score.argmax())].copy()
    p[0] = sx * x_abs
    p[1] += 0.0024
    p[2] += 0.0036
    return p


def _costal_insert(sx: float, x_abs: float) -> np.ndarray:
    """Anterior table of the xiphoid and costal cartilages 5–7 — not past the cage."""
    v = _bone_verts()
    x_abs = float(np.clip(x_abs, 0.002, 0.068))
    mask = (
        _side_mask(v, sx)
        & (np.abs(np.abs(v[:, 0]) - x_abs) < 0.011)
        & (v[:, 1] > 0.276)
        & (v[:, 1] < 0.350)
        & (v[:, 2] > 0.105)
        & (np.abs(v[:, 0]) < 0.078)
    )
    pts = v[mask]
    if len(pts) < 6:
        mask = (
            (v[:, 1] > 0.268)
            & (v[:, 1] < 0.358)
            & (v[:, 2] > 0.098)
            & (np.abs(np.abs(v[:, 0]) - x_abs) < 0.016)
            & (np.abs(v[:, 0]) < 0.082)
        )
        pts = v[mask]
    if len(pts) == 0:
        y = 0.308 + 0.38 * x_abs
        return np.array([sx * x_abs, y, float(_wall_z(y)) + 0.0012], dtype=np.float64)
    zcut = np.percentile(pts[:, 2], 70)
    ant = pts[pts[:, 2] >= zcut]
    # Inferior among the anterior cloud = margin / xiphoid, not a float up the sternum.
    ycut = np.percentile(ant[:, 1], 30)
    band = ant[ant[:, 1] <= ycut + 0.012]
    p = band[int(band[:, 2].argmax())].copy()
    p[0] = sx * x_abs
    p[2] += 0.0020
    return p


def _deep_back_cloud():
    """Bone + erectors / SPI — used so latissimus sits *behind* them."""
    global _DEEP_CLOUD
    if _DEEP_CLOUD is None:
        from body_surface import BodyCloud
        from scipy.spatial import cKDTree

        cloud = BodyCloud(list(_DEEP_BACK_IDS), sx=None)
        mask = (cloud.pts[:, 1] > 0.0) & (cloud.pts[:, 1] < 0.52) & (cloud.pts[:, 2] < 0.045)
        if int(mask.sum()) >= 40:
            cloud.pts = cloud.pts[mask]
            cloud.tree = cKDTree(cloud.pts)
        _DEEP_CLOUD = cloud
    return _DEEP_CLOUD


def _rib_slip(sx: float, y: float) -> np.ndarray:
    """Outer anterolateral costal attachment (ribs 5–12)."""
    return _outer_rib(sx, y, prefer="antero_lateral", extra=0.0036)


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
    """T7–L5 / iliac origin sitting *behind* SPI & iliocostalis, then a fan to the humerus."""
    from body_surface import posterior_midline

    suf = "d" if sx < 0 else "g"
    cloud = _deep_back_cloud()
    t1, t12 = p["t1"], p["t12"]
    l5 = p["l5"]
    t7_y = float(mix(t1, t12, 0.545)[1])
    y_bot = float(l5[1]) + 0.002

    def spinous_pt(y: float) -> np.ndarray:
        spin = posterior_midline(y, ywin=0.014)
        return np.array([sx * 0.0005, y, float(spin[2]) - 0.002], dtype=np.float64)

    n_along, n_across = 20, 13
    ys = np.linspace(t7_y, y_bot, n_along)
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i, y in enumerate(ys):
        t = i / (n_along - 1)
        mid = spinous_pt(float(y))
        half = 0.080 + 0.050 * float(np.sin(t * np.pi) ** 0.75)
        if t < 0.18:
            half = 0.074 + 0.036 * (t / 0.18)
        for j in range(n_across):
            s = j / (n_across - 1)
            x = sx * half * (s**0.90)
            z_env = cloud.posterior_z(float(x) if abs(x) > 0.004 else 0.0, float(y), xwin=0.020, ywin=0.016)
            if z_env is None:
                z_env = float(mid[2])
            # Entire sheet stays posterior to the deep-muscle envelope.
            grid[i, j] = np.array([x, y, z_env - 0.0090], dtype=np.float64)
        grid[i, 0] = mid + np.array([0.0, 0.0, -0.0070], dtype=np.float64)
    back_sheet = grid_sheet(grid, thickness=0.0130)

    sac = off(p["sacrum"], x=sx * 0.006, y=0.008, z=-0.040)
    eips = off(p[f"eips-{suf}"], z=-0.016)
    crest = p[f"crete-iliaque-{suf}"]
    crest_post = mix(eips, crest, 0.38) + np.array([0.0, 0.006, -0.024])
    crest_lat = off(crest, x=sx * 0.012, z=-0.012)
    scap = off(p[f"angle-inf-scapula-{suf}"], x=sx * 0.010, y=-0.006, z=-0.014)
    rib12 = _outer_rib(sx, 0.188, prefer="postero_lateral", extra=0.0030)
    rib10 = _outer_rib(sx, 0.236, prefer="postero_lateral", extra=0.0030)
    head = p[f"tete-humerus-{suf}"]
    insert = head + np.array([sx * 0.008, -0.028, 0.022])

    spine = [spinous_pt(float(y)) + np.array([0.0, 0.0, -0.006]) for y in np.linspace(t7_y, y_bot, 9)]
    origins = spine + [sac, eips, crest_post, crest_lat, rib12, rib10, scap]
    paths = [_lat_wrap_path(origin, insert, sx) for origin in origins]
    wrap = _sheet(paths, thickness=0.0076)
    fold = _lat_wrap_path(rib10, insert, sx)
    border = loft_tube(fold, np.linspace(0.0044, 0.0020, len(fold)), radial=8, caps=True)
    tendon_path = bezier_cubic(
        np.array([sx * 0.150, 0.40, 0.014]),
        np.array([sx * 0.160, 0.44, 0.026]),
        insert + np.array([sx * 0.006, -0.006, 0.006]),
        insert,
        12,
    )
    tendon = loft_tube(tendon_path, np.linspace(0.0046, 0.0024, 12), radial=8, caps=True)
    mesh = _concat([back_sheet, wrap, border, tendon])
    v = np.asarray(mesh.vertices)
    dist = np.linalg.norm(v - insert[None, :], axis=1)
    medial = np.clip((0.030 - np.abs(v[:, 0])) / 0.022, 0.0, 1.0)
    lumbar = np.clip((0.34 - v[:, 1]) / 0.28, 0.0, 1.0)
    w = np.clip(medial * (0.35 + 0.65 * lumbar), 0.0, 1.0)
    w = np.maximum(w, np.clip((0.058 - dist) / 0.042, 0.0, 1.0))
    paint_tendon(mesh, w)
    return mesh


def _rectus_inscription(t: float, bands: tuple[float, ...], sigma: float) -> float:
    return float(max(np.exp(-(((t - b) / sigma) ** 2)) for b in bands))


def _rectus_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Four pads / side. Origin on pubic crest + symphysis; insert on xiphoid + cartilages 5–7."""
    bands = (0.20, 0.42, 0.64)
    n_along = 56
    n_across = 14
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        t = i / (n_along - 1)
        ins = _rectus_inscription(t, bands, 0.034)
        end = np.exp(-(t / 0.072) ** 2) + np.exp(-(((1.0 - t) / 0.080) ** 2))
        pinch = max(ins, 0.55 * end)
        # Pubic crest is ~2.2 cm wide; belly ~5.2 cm; costal 5–7 ~5.0 cm (not past the arch).
        w_pub = 0.022 * (1.0 - 0.18 * pinch)
        w_belly = 0.052 * (1.0 - 0.32 * pinch)
        w_cost = 0.048 * (1.0 - 0.16 * pinch)
        if t < 0.18:
            width = mix(w_pub, w_belly, t / 0.18)
        elif t > 0.78:
            width = mix(w_belly, w_cost, (t - 0.78) / 0.22)
        else:
            width = w_belly
        inner = 0.0034
        for j in range(n_across):
            s = j / (n_across - 1)
            bulge = np.sin(s * np.pi) ** 0.72
            x_abs = inner + s * width * (0.78 + 0.22 * bulge)
            origin = _pubic_crest(sx, x_abs)
            insert = _costal_insert(sx, x_abs)
            y = float(mix(origin[1], insert[1], t))
            z_mid = float(_wall_z(y)) + 0.0052 * (1.0 - 0.70 * pinch)
            z = float(mix(origin[2], mix(z_mid, insert[2], t**1.25), min(1.0, 0.12 + 0.88 * t)))
            if t < 0.10:
                k = t / 0.10
                y = float(mix(origin[1], y, k))
                z = float(mix(origin[2], z, k))
            if t > 0.86:
                k = (t - 0.86) / 0.14
                y = float(mix(y, insert[1], k))
                z = float(mix(z, insert[2], k))
                # Never sit proud of / through the costal outer table.
                z = min(z, float(insert[2]) + 0.0006)
            grid[i, j] = np.array([sx * x_abs, y, z], dtype=np.float64)

    sheet = grid_sheet(grid, thickness=0.0074)
    v = np.asarray(sheet.vertices)
    for i, pt in enumerate(v):
        sx_v = 1.0 if pt[0] >= 0 else -1.0
        x_abs = abs(float(pt[0]))
        if pt[1] < -0.012:
            crest = _pubic_crest(sx_v, x_abs)
            v[i, 1] = min(float(v[i, 1]), float(crest[1]) + 0.004)
            v[i, 2] = float(np.clip(v[i, 2], float(crest[2]) - 0.0012, float(crest[2]) + 0.0025))
        if pt[1] > 0.268:
            cap = _costal_insert(sx_v, min(x_abs, 0.058))
            v[i, 2] = float(np.clip(v[i, 2], float(cap[2]) - 0.0008, float(cap[2]) + 0.0010))
            if v[i, 1] > float(cap[1]) + 0.005:
                v[i, 1] = float(cap[1]) + 0.003
    sheet.vertices = v
    y0, y1 = float(v[:, 1].min()), float(v[:, 1].max())
    t = (v[:, 1] - y0) / max(y1 - y0, 1e-6)
    w = np.zeros(len(v), dtype=np.float64)
    for b in bands:
        w = np.maximum(w, np.exp(-(((t - b) / 0.018) ** 2)))
    w = np.maximum(w, 0.98 * np.exp(-(t / 0.046) ** 2))
    w = np.maximum(w, 0.98 * np.exp(-(((1.0 - t) / 0.050) ** 2)))
    w = np.maximum(w, np.clip((0.011 - np.abs(v[:, 0])) / 0.007, 0.0, 1.0) * 0.62)
    paint_tendon(sheet, w)
    return sheet


def _linea_alba(p: dict[str, np.ndarray]) -> trimesh.Trimesh:
    pub = _pubic_crest(1.0, 0.0036)
    xiph = _costal_insert(1.0, 0.0036)
    n_along, n_across = 40, 5
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        t = i / (n_along - 1)
        y = float(mix(pub[1], xiph[1], t))
        z = float(mix(pub[2], xiph[2], t**1.15))
        z = min(z, float(_wall_z(y)) + 0.0060)
        if t > 0.82:
            z = min(z, float(xiph[2]) + 0.0006)
        half = 0.0050 * (0.85 + 0.15 * np.sin(t * np.pi))
        for j in range(n_across):
            s = j / (n_across - 1)
            grid[i, j] = np.array([-half + s * 2.0 * half, y, z], dtype=np.float64)
    sheet = grid_sheet(grid, thickness=0.0030)
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
    flank_depth: float | None = None,
) -> np.ndarray:
    """Flank → linea alba on the torso envelope.

    diagonal>0 skews fibers superomedial (IO); <0 inferomedial (EO).
    depth>0 sits deep to the rectus wall (smaller anterior z).
    x_scale < 1 insets the flank so deep layers stay inside superficial ones.
    """
    z_flank = depth if flank_depth is None else flank_depth
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        ty = i / (n_along - 1)
        y = y_top * (1.0 - ty) + y_bot * ty
        z_ant = float(_wall_z(y)) - depth
        x_lat = float(_flank_x(y)) * x_scale * (0.96 + 0.04 * np.sin(ty * np.pi))
        z_lat = float(_flank_z(y)) - z_flank
        for j in range(n_across):
            s = j / (n_across - 1)
            y_fiber = y + diagonal * (0.5 - s) * 0.048
            x = sx * mix(x_lat, linea, s**0.88)
            z = mix(z_lat, z_ant, s**1.18)
            grid[i, j] = np.array([x, y_fiber, z], dtype=np.float64)
    return grid


# Posterior rib 12 → anterior rib 10. Each station is snapped to the inferior lip.
_IO_LIP_GUIDES: tuple[tuple[float, float, float], ...] = (
    (0.114, 0.158, 0.042),  # rib 12
    (0.122, 0.176, 0.076),  # rib 11
    (0.123, 0.206, 0.100),  # rib 11 anterior
    (0.118, 0.236, 0.124),  # rib 10
    (0.106, 0.256, 0.138),  # rib 10 anterior lip, just under the costal margin
)


def _io_bone_lip(sx: float, x_abs: float, y: float, z: float) -> np.ndarray:
    """Inferior edge of the rib that passes this station — not a lower rib nearby."""
    v = _cage_pts()
    side = v[_side_mask(v, sx)]
    dx = np.abs(side[:, 0]) - x_abs
    dz = side[:, 2] - z
    dist = np.sqrt(dx * dx + dz * dz)
    near = side[dist < 0.016]
    if len(near) < 4:
        near = side[dist < 0.028]
    band = near[np.abs(near[:, 1] - y) < 0.016] if len(near) else near
    if len(band) < 3:
        band = near[np.abs(near[:, 1] - y) < 0.028] if len(near) else near
    if len(band) == 0:
        return np.array([sx * x_abs, y - 0.003, z], dtype=np.float64)
    ymin = float(band[:, 1].min())
    lip = band[band[:, 1] <= ymin + 0.004]
    score = (np.abs(lip[:, 0]) - x_abs) ** 2 + (lip[:, 2] - z) ** 2
    p = lip[int(score.argmin())].copy()
    # Sit just under that rib's inferior margin.
    p[1] -= 0.0030
    p[0] -= sx * 0.0014
    return p


def _io_costal(sx: float, t: float) -> np.ndarray:
    """Superior border: rib 12 (t=0) → rib 10 (t=1), then the semilunar corner."""
    t = float(np.clip(t, 0.0, 1.0))
    guides = _IO_LIP_GUIDES
    # First 85% rides the bony lips; the last stretch reaches the rectus sheath.
    if t < 0.86:
        u = t / 0.86
        x = u * (len(guides) - 1)
        i = min(int(np.floor(x)), len(guides) - 2)
        local = x - i
        a = np.array(guides[i], dtype=np.float64)
        b = np.array(guides[i + 1], dtype=np.float64)
        g = a * (1.0 - local) + b * local
        return _io_bone_lip(sx, float(g[0]), float(g[1]), float(g[2]))
    u = (t - 0.86) / 0.14
    rib10 = _io_bone_lip(sx, guides[-1][0], guides[-1][1], guides[-1][2])
    corner = _io_seat(sx, 0.056, float(rib10[1]) - 0.004 * u, deep=0.006)
    return mix(rib10, corner, u**0.85)


def _io_seat(sx: float, x_abs: float, y: float, deep: float = 0.008) -> np.ndarray:
    """Deep to external oblique: flank inset, sheath plane medially."""
    y = float(y)
    x_lat = float(_flank_x(y)) * 0.92
    x_abs = float(np.clip(x_abs, 0.004, max(x_lat, 0.02)))
    span = max(x_lat - 0.006, 0.02)
    s = float(np.clip((x_lat - x_abs) / span, 0.0, 1.0))
    z_lat = float(_flank_z(y)) - 0.010
    z_wall = _rectus_ant_z(y) - 0.010
    z = float(mix(z_lat, z_wall, s**1.05)) - deep * 0.25
    return np.array([sx * x_abs, y, z], dtype=np.float64)


def _io_origin(sx: float, t: float) -> np.ndarray:
    """Iliac crest (t=0) → inguinal end of the fleshy belly (t=1)."""
    t = float(np.clip(t, 0.0, 1.0))
    if t < 0.68:
        u = t / 0.68
        z = float(mix(0.022, 0.090, u**0.92))
        crest = _eo_crest(sx, z)
        crest[0] -= sx * 0.005
        crest[2] -= 0.003
        return crest
    u = (t - 0.68) / 0.32
    crest = _eo_crest(sx, 0.090)
    crest[0] -= sx * 0.005
    # Fleshy inguinal end stays lateral to the sheath; apo continues to the pubis.
    inguinal = _io_seat(sx, float(mix(abs(float(crest[0])), 0.058, u)), float(mix(crest[1], 0.028, u**0.9)))
    return mix(crest, inguinal, u)


def _io_aponeurosis_side(sx: float) -> trimesh.Trimesh:
    """Medial sheath: semilunar → linea, rib-10 height → pubis. Tendon white."""
    n_along, n_across = 16, 10
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    top = _io_costal(sx, 1.0)
    bot = _io_origin(sx, 1.0)
    pub = _pubic_crest(sx, 0.010)
    for i in range(n_along):
        u = i / (n_along - 1)
        lat = mix(top, bot, u**0.96)
        y_lat = float(lat[1])
        y_med = float(mix(y_lat - 0.006, float(pub[1]) + 0.004, u**1.05))
        y_med = min(y_med, y_lat - 0.002)
        med = _io_seat(sx, 0.0048, y_med, deep=0.004)
        if u > 0.78:
            med = mix(med, pub + np.array([0.0, 0.002, 0.002]), ((u - 0.78) / 0.22) ** 0.8)
        for j in range(n_across):
            s = j / (n_across - 1)
            y = float(mix(y_lat, float(med[1]), s**0.95))
            x_abs = float(mix(abs(float(lat[0])), abs(float(med[0])), s**0.92))
            pt = _io_seat(sx, x_abs, y, deep=0.005)
            if s < 0.12:
                pt = mix(lat, pt, s / 0.12)
            elif s > 0.88:
                pt = mix(pt, med, (s - 0.88) / 0.12)
            grid[i, j] = pt
    sheet = grid_sheet(grid, thickness=0.0016)
    v = np.asarray(sheet.vertices)
    x = np.abs(v[:, 0])
    x_trans = np.interp(v[:, 1], [-0.02, 0.04, 0.12, 0.22], [0.070, 0.064, 0.058, 0.056])
    blend = np.clip((x_trans - x) / 0.014, 0.0, 1.0) ** 0.6
    medial = np.clip((x_trans - 0.012 - x) / 0.008, 0.0, 1.0)
    paint_tendon(sheet, np.maximum(blend, medial))
    return sheet


def _internal_oblique_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Crest / inguinal → inferior margins of ribs 12–10; apo to the rectus sheath.

    Fibers run superomedially (opposite the external oblique). Fleshy belly is
    fully red; only the sheath is tendon-white.
    """
    del p
    n_along, n_across = 28, 14
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        t = i / (n_along - 1)
        origin = _io_origin(sx, t)
        dest = _io_costal(sx, t)
        for j in range(n_across):
            s = j / (n_across - 1)
            pt = mix(origin, dest, s**0.90)
            if 0.06 < s < 0.90:
                seated = _io_seat(sx, abs(float(pt[0])), float(pt[1]), deep=0.007)
                # Keep y on the fiber; tuck x/z onto the deep wall.
                belly = float(np.sin((s - 0.06) / 0.84 * np.pi))
                pt = np.array(
                    [
                        mix(float(pt[0]), float(seated[0]), 0.55 * belly),
                        float(pt[1]),
                        mix(float(pt[2]), float(seated[2]), 0.65 * belly),
                    ],
                    dtype=np.float64,
                )
            grid[i, j] = pt
    flesh = grid_sheet(grid, thickness=0.0046)
    paint_solid(flesh, MUSCLE_RED)
    return _concat([flesh, _io_aponeurosis_side(sx)])


# Inner face of costal cartilages 12 → 7 (lateral/low → medial/high).
_TA_COSTAL: tuple[tuple[float, float], ...] = (
    (0.108, 0.158),  # rib 12
    (0.110, 0.198),  # rib 11
    (0.106, 0.234),  # rib 10
    (0.096, 0.256),  # rib 9
    (0.086, 0.274),  # rib 8, lateral end of 7
    (0.058, 0.236),  # cartilage 7 meeting the sheath, still under the apo
)

# Right-side EO+IO vertices, used to keep TA tucked under their flesh.
_OBLIQUE_CLOUD: np.ndarray | None = None


def _oblique_cover_cloud(p: dict[str, np.ndarray]) -> np.ndarray:
    """Patient-right oblique vertices. Built once so TA can sit just deep to them."""
    global _OBLIQUE_CLOUD
    if _OBLIQUE_CLOUD is None:
        eo = np.asarray(_external_oblique_side(p, -1.0).vertices)
        io = np.asarray(_internal_oblique_side(p, -1.0).vertices)
        cloud = np.vstack([eo, io])
        _OBLIQUE_CLOUD = cloud[cloud[:, 0] < 0.0]
    return _OBLIQUE_CLOUD


def _ta_y_limit(p: dict[str, np.ndarray], x_abs: float) -> float:
    """Highest y the obliques still cover at this laterality."""
    cloud = _oblique_cover_cloud(p)
    x_abs = float(x_abs)
    band = cloud[np.abs(np.abs(cloud[:, 0]) - x_abs) < 0.014]
    if len(band) < 8:
        band = cloud[np.abs(np.abs(cloud[:, 0]) - x_abs) < 0.026]
    if len(band) < 4:
        return 0.228
    return float(band[:, 1].max()) - 0.006


def _ta_costal_xy(s: float) -> tuple[float, float]:
    guides = _TA_COSTAL
    x = float(np.clip(s, 0.0, 1.0)) * (len(guides) - 1)
    i = min(int(np.floor(x)), len(guides) - 2)
    local = x - i
    a = guides[i]
    b = guides[i + 1]
    return (a[0] * (1.0 - local) + b[0] * local, a[1] * (1.0 - local) + b[1] * local)


def _ta_under_obliques(p: dict[str, np.ndarray], x_abs: float, y: float, s_medial: float) -> float:
    """Depth on the inner abdominal wall: behind oblique flesh, in front of their back lip.

    The old sheet reached the spinous processes and showed behind OE/OI.
    """
    cloud = _oblique_cover_cloud(p)
    y = float(y)
    x_abs = float(x_abs)
    dist = np.hypot(np.abs(cloud[:, 0]) - x_abs, cloud[:, 1] - y)
    tight = cloud[dist < 0.016]
    wide = cloud[dist < 0.030]
    if len(tight) < 8:
        tight = wide
    z_sheath = _rectus_ant_z(y) - 0.016
    if len(wide) < 6:
        return z_sheath
    z_back = float(np.percentile(tight[:, 2], 15))
    z_front = float(np.percentile(wide[:, 2], 94))
    z_tuck = z_back + 0.005
    z = float(mix(z_tuck, z_sheath, float(np.clip(s_medial, 0.0, 1.0)) ** 0.90))
    z_hi = z_front - 0.012
    z_lo = z_back + 0.003
    # Prefer staying behind the superficial face when the sheet is thin.
    if z_hi <= z_lo:
        return z_hi
    return float(min(max(z, z_lo), z_hi))


def _ta_inner_cartilage(p: dict[str, np.ndarray], sx: float, x_abs: float, y: float) -> np.ndarray:
    """Inner face of a costal cartilage: a few millimetres deep to its anterior lip."""
    v = _cage_pts()
    side = v[_side_mask(v, sx)]
    dist = np.hypot(np.abs(side[:, 0]) - x_abs, side[:, 1] - y)
    near = side[dist < 0.018]
    if len(near) < 4:
        near = side[dist < 0.032]
    if len(near) == 0:
        z = _ta_under_obliques(p, x_abs, y, 0.15)
        return np.array([sx * x_abs, y, z], dtype=np.float64)
    z_cut = float(np.percentile(near[:, 2], 82))
    lip = near[near[:, 2] >= z_cut]
    score = (np.abs(lip[:, 0]) - x_abs) ** 2 + 0.35 * (lip[:, 1] - y) ** 2
    pt = lip[int(score.argmin())].copy()
    pt[2] -= 0.006
    pt[0] -= sx * 0.003
    pt[2] = min(float(pt[2]), _ta_under_obliques(p, abs(float(pt[0])), float(pt[1]), 0.2))
    return pt


def _ta_lateral(p: dict[str, np.ndarray], sx: float, t: float) -> np.ndarray:
    """Posterolateral edge: rib 12 inner face → iliac crest (thoracolumbar / crest origin)."""
    t = float(np.clip(t, 0.0, 1.0))
    rib = _ta_inner_cartilage(p, sx, _TA_COSTAL[0][0], _TA_COSTAL[0][1])
    crest = _eo_crest(sx, 0.034)
    crest[0] -= sx * 0.008
    crest[1] -= 0.004
    pt = mix(rib, crest, t**0.96)
    x_abs = min(abs(float(pt[0])), float(_flank_x(float(pt[1]))) * 0.88)
    z = _ta_under_obliques(p, x_abs, float(pt[1]), 0.0)
    return np.array([sx * x_abs, float(pt[1]), z], dtype=np.float64)


def _ta_medial(p: dict[str, np.ndarray], sx: float, t: float) -> np.ndarray:
    """Linea alba from the 7th costal cartilage down to the pubic crest."""
    t = float(np.clip(t, 0.0, 1.0))
    rib = _ta_inner_cartilage(p, sx, _TA_COSTAL[-1][0], _TA_COSTAL[-1][1])
    y = float(mix(float(rib[1]), -0.050, t**1.02))
    x_abs = float(mix(max(abs(float(rib[0])), 0.018), 0.010, t))
    z = _ta_under_obliques(p, x_abs, y, 1.0)
    if t > 0.78:
        pub = _pubic_crest(sx, 0.010)
        pub[2] -= 0.005
        return mix(np.array([sx * x_abs, y, z], dtype=np.float64), pub, ((t - 0.78) / 0.22) ** 0.85)
    return np.array([sx * x_abs, y, z], dtype=np.float64)


def _transversus_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Deep corset: inner costal cartilages 7–12, crest, inguinal → linea alba / pubis.

    Horizontal fibers. The belly sits on the deep face of the anterior wall,
    tucked under the obliques instead of running back to the spine.
    """
    n_along, n_across = 24, 16
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        t = i / (n_along - 1)
        lateral = _ta_lateral(p, sx, t)
        medial = _ta_medial(p, sx, t)
        for j in range(n_across):
            s = j / (n_across - 1)
            pt = mix(lateral, medial, s**0.90)
            # Top fibers originate on the inner costal cartilages.
            if t < 0.20:
                cx, cy = _ta_costal_xy(s)
                cart = _ta_inner_cartilage(p, sx, cx, cy)
                pt = mix(cart, pt, t / 0.20)
            x_abs = abs(float(pt[0]))
            y = min(float(pt[1]), _ta_y_limit(p, x_abs))
            x_abs = min(x_abs, float(_flank_x(y)) * 0.90)
            # Always the tucked depth. Cartilage points only steer x/y; their
            # raw inner-face z sits behind the obliques and would show through.
            z = _ta_under_obliques(p, x_abs, y, s)
            grid[i, j] = np.array([sx * x_abs, y, z], dtype=np.float64)
    sheet = grid_sheet(grid, thickness=0.0026)
    v = np.asarray(sheet.vertices)
    # Posterior rectus sheath: medial to the semilunar line. Flesh stays opaque.
    x_trans = np.interp(v[:, 1], [-0.04, 0.04, 0.14, 0.26], [0.058, 0.056, 0.050, 0.040])
    w = np.clip((x_trans - np.abs(v[:, 0])) / 0.016, 0.0, 1.0) ** 0.85
    paint_tendon(sheet, w)
    return sheet


# Rib 12 (posterior) → rib 5 (anterior). Heights sit between serratus slips.
# notch_depth is how far the valley between this rib and the next one drops.
_EO_RIBS: tuple[tuple[float, float, float], ...] = (
    (0.172, -0.014, 0.042),
    (0.198, -0.006, 0.048),
    (0.230, 0.000, 0.056),
    (0.262, 0.004, 0.060),
    (0.294, 0.006, 0.058),
    (0.318, 0.008, 0.054),
    (0.344, 0.010, 0.048),
    (0.378, 0.012, 0.042),
)

# Anterior surface of rectus — the EO aponeurosis lies just in front of it.
_RECTUS_Y = np.array([-0.055, 0.00, 0.06, 0.12, 0.18, 0.24, 0.30], dtype=np.float64)
_RECTUS_Z = np.array([0.100, 0.098, 0.106, 0.118, 0.136, 0.160, 0.172], dtype=np.float64)


def _rectus_ant_z(y: float) -> float:
    return float(np.interp(y, _RECTUS_Y, _RECTUS_Z))


def _eo_seat(sx: float, x_abs: float, y: float, lift: float = 0.008) -> np.ndarray:
    """Flank envelope laterally, just superficial to rectus when medial.

    Does not project onto the rib cage — that shove was pinning the aponeurosis
    on the flank instead of letting it cross the rectus.
    """
    y = float(y)
    x_lat = float(_flank_x(y))
    x_abs = float(np.clip(x_abs, 0.0035, x_lat * 1.06 + 0.012))
    span = max(x_lat - 0.006, 0.02)
    s = float(np.clip((x_lat - x_abs) / span, 0.0, 1.0))
    z = float(mix(_flank_z(y), _rectus_ant_z(y), s**1.08))
    x_abs = x_abs + lift * (1.0 - s) * 0.70
    z = z + 0.0035 + lift * (0.35 + 0.40 * s)
    return np.array([sx * x_abs, y, z], dtype=np.float64)


def _eo_rib_anchor(sx: float, y: float, z_bias: float) -> np.ndarray:
    """Outer lateral rib, proud of serratus — digitation tip on the profile."""
    v = _cage_pts()
    mask = (
        _side_mask(v, sx)
        & (np.abs(v[:, 1] - y) < 0.016)
        & (v[:, 2] > -0.005)
        & (np.abs(v[:, 0]) > 0.075)
        & (np.abs(v[:, 0]) < 0.152)
    )
    pts = v[mask]
    if len(pts) < 8:
        mask = (
            _side_mask(v, sx)
            & (np.abs(v[:, 1] - y) < 0.030)
            & (v[:, 2] > -0.02)
            & (np.abs(v[:, 0]) > 0.06)
            & (np.abs(v[:, 0]) < 0.158)
        )
        pts = v[mask]
    if len(pts) == 0:
        return _eo_seat(sx, 0.128, y, 0.012)
    score = np.abs(pts[:, 0]) * 1.35 + 0.20 * pts[:, 2]
    p = pts[int(score.argmax())].copy()
    p[0] += sx * 0.012
    p[2] += 0.008 + z_bias
    p[1] = y
    p = _project_outside_thorax(p, sx, standoff=0.0045)
    p[1] = y
    p[0] += sx * 0.004
    return p


def _eo_crest(sx: float, z: float) -> np.ndarray:
    """External lip of the iliac crest at this anteroposterior station."""
    v = _bone_verts()
    mask = (
        _side_mask(v, sx)
        & (np.abs(v[:, 2] - z) < 0.016)
        & (v[:, 1] > 0.025)
        & (v[:, 1] < 0.125)
        & (np.abs(v[:, 0]) > 0.072)
        & (np.abs(v[:, 0]) < 0.158)
    )
    pts = v[mask]
    if len(pts) < 6:
        mask = (
            _side_mask(v, sx)
            & (np.abs(v[:, 2] - z) < 0.032)
            & (v[:, 1] > 0.02)
            & (v[:, 1] < 0.13)
            & (np.abs(v[:, 0]) > 0.065)
            & (np.abs(v[:, 0]) < 0.160)
        )
        pts = v[mask]
    if len(pts) == 0:
        return np.array([sx * 0.112, 0.082, z], dtype=np.float64)
    score = pts[:, 1] + 0.06 * np.abs(pts[:, 0])
    p = pts[int(score.argmax())].copy()
    p[1] += 0.0035
    p[0] += sx * 0.0035
    p[2] += 0.0030
    return p


def _eo_transition(sx: float, u: float) -> np.ndarray:
    """Fleshy → aponeurotic border. u=0 superior (semilunar), u=1 ASIS."""
    u = float(np.clip(u, 0.0, 1.0))
    y = float(mix(0.228, 0.052, u**0.88))
    x_abs = float(mix(0.050, 0.120, u**0.76))
    pt = _eo_seat(sx, x_abs, y, lift=0.011)
    if u > 0.84:
        z = float(mix(0.055, 0.090, (u - 0.84) / 0.16))
        crest = _eo_crest(sx, z)
        pt = mix(pt, crest, ((u - 0.84) / 0.16) ** 0.85)
    return pt


def _eo_origin(sx: float, t: float) -> np.ndarray:
    """Serrated costal border, rib 12 (t=0) → rib 5 (t=1), valleys between slips."""
    ribs = _EO_RIBS
    n = len(ribs)
    x = float(np.clip(t, 0.0, 1.0)) * (n - 1)
    i = min(int(np.floor(x)), n - 2)
    local = x - i
    y0, z0, depth = ribs[i]
    y1, z1, _depth1 = ribs[i + 1]
    y = float(mix(y0, y1, local))
    z_bias = float(mix(z0, z1, local))
    notch = float(np.sin(local * np.pi) ** 1.55)
    base = _eo_rib_anchor(sx, y, z_bias)
    base[1] -= depth * notch
    # Tuck the valley medially so each slip reads as its own finger.
    base[0] -= sx * 0.022 * notch
    base[2] -= 0.006 * notch
    return base


def _eo_dest(sx: float, t: float) -> np.ndarray:
    """Posterior fibers reach the iliac crest; anterior fibers stop at the apo line."""
    t = float(np.clip(t, 0.0, 1.0))
    if t < 0.58:
        u = t / 0.58
        # Lateral lip of the crest (not the posterior medial ilium).
        z = float(mix(0.030, 0.090, u**0.90))
        return _eo_crest(sx, z)
    u = (t - 0.58) / 0.42
    return _eo_transition(sx, 1.0 - u)


def _eo_aponeurosis_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Inferomedial sheet over the rectus: semilunar → linea, ASIS → pubic crest.

    Painted tendon-white so the shared uTendonAlpha uniform can make it 50% opaque.
    A slim lateral blend stays red where it meets the fleshy belly.
    """
    del p
    n_along, n_across = 22, 14
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        u = i / (n_along - 1)
        lat = _eo_transition(sx, u)
        y_lat = float(lat[1])
        pub = _pubic_crest(sx, float(mix(0.020, 0.006, u)))
        y_med = float(mix(y_lat - 0.010, float(pub[1]) + 0.003, u**1.02))
        y_med = min(y_med, y_lat - 0.003)
        med = _eo_seat(sx, 0.0046, max(y_med, float(pub[1]) + 0.002), lift=0.013)
        if u > 0.72:
            k = (u - 0.72) / 0.28
            med = mix(med, pub + np.array([0.0, 0.0022, 0.0035]), k**0.75)
        for j in range(n_across):
            s = j / (n_across - 1)
            y = float(mix(y_lat, float(med[1]), s**0.94))
            x_abs = float(mix(abs(float(lat[0])), abs(float(med[0])), s**0.90))
            pt = _eo_seat(sx, x_abs, y, lift=0.012)
            if s < 0.10:
                pt = mix(lat, pt, s / 0.10)
            elif s > 0.90:
                pt = mix(pt, med, (s - 0.90) / 0.10)
            grid[i, j] = pt
    sheet = grid_sheet(grid, thickness=0.0017)
    v = np.asarray(sheet.vertices)
    x = np.abs(v[:, 0])
    x_trans = np.interp(v[:, 1], [-0.04, 0.04, 0.10, 0.18, 0.26], [0.118, 0.112, 0.090, 0.066, 0.056])
    blend = np.clip((x_trans - x) / 0.016, 0.0, 1.0) ** 0.55
    medial = np.clip((x_trans - 0.014 - x) / 0.010, 0.0, 1.0)
    paint_tendon(sheet, np.maximum(blend, medial))
    return sheet


def _external_oblique_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Chart EO: costal digitations, hands-in-pockets fibers, iliac crest, anterior apo.

    Fleshy belly stays fully red (opaque). Only the aponeurosis is tendon-white.
    """
    n_along, n_across = 40, 16
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        t = i / (n_along - 1)
        origin = _eo_origin(sx, t)
        dest = _eo_dest(sx, t)
        for j in range(n_across):
            s = j / (n_across - 1)
            pt = mix(origin, dest, s**0.88)
            if s < 0.96:
                seated = _eo_seat(sx, abs(float(pt[0])), float(pt[1]), lift=0.009 + 0.003 * (1.0 - s))
                # Keep the sawtooth slips intact over the proximal part of each fiber.
                if s < 0.42:
                    keep = (1.0 - s / 0.42) ** 1.05
                    pt = mix(seated, origin, keep)
                else:
                    pt = seated
            else:
                pt = mix(pt, dest, (s - 0.96) / 0.04)
            grid[i, j] = pt
    flesh = grid_sheet(grid, thickness=0.0060)
    paint_solid(flesh, MUSCLE_RED)
    apo = _eo_aponeurosis_side(p, sx)
    return _concat([flesh, apo])


def enhance_external_oblique(mesh: trimesh.Trimesh, p: dict[str, np.ndarray] | None = None) -> trimesh.Trimesh:
    """EO is fully synthetic (digitations + superficial apo). `mesh` is ignored."""
    del mesh
    if p is None:
        p = load_lm()
    return _bilateral(_external_oblique_side, p)


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
    for b in (0.20, 0.42, 0.64):
        w = np.maximum(w, np.exp(-(((t - b) / 0.018) ** 2)))
    w = np.maximum(w, 0.98 * np.exp(-(t / 0.046) ** 2))
    w = np.maximum(w, 0.98 * np.exp(-(((1.0 - t) / 0.050) ** 2)))
    w = np.maximum(w, np.clip((0.0058 - np.abs(v[:, 0])) / 0.0034, 0.0, 1.0))
    paint_tendon(rectus, w)
    return {
        "grand-dorsal": _bilateral(_latissimus_side, p),
        "droit-abdomen": rectus,
        "oblique-interne": _bilateral(_internal_oblique_side, p),
        "oblique-externe": _bilateral(_external_oblique_side, p),
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
    "oblique-externe": "external oblique",
    "transverse-de-l-abdomen": "transversus abdominis",
    **MASTICATION_KEYS,
}
