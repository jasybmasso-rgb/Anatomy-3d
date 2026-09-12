"""Skeleton / muscle surface queries for schematic sheets and landmark fixes.

Used only at mesh-build time. Positions are in the same world frame as
public/models/skeleton.glb (metres, origin near the pelvic mid-plane).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"
SKELETON_GLB = ROOT / "public" / "models" / "skeleton.glb"
MUSCLES_GLB = ROOT / "public" / "models" / "muscles.glb"

_BONE_VERTS: np.ndarray | None = None
_MUSCLE_SCENE = None


def load_lm() -> dict[str, np.ndarray]:
    data = json.loads(LANDMARKS.read_text(encoding="utf-8"))
    return {item["id"]: np.array(item["position"], dtype=float) for item in data["landmarks"]}


def mix(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    return a * (1.0 - t) + b * t


def off(p: np.ndarray, x: float = 0, y: float = 0, z: float = 0) -> np.ndarray:
    return p + np.array([x, y, z], dtype=float)


def bone_verts() -> np.ndarray:
    global _BONE_VERTS
    if _BONE_VERTS is None:
        scene = trimesh.load(SKELETON_GLB, force="scene")
        geom = scene.geometry.get("bones") or next(iter(scene.geometry.values()))
        _BONE_VERTS = np.asarray(geom.vertices, dtype=np.float64)
    return _BONE_VERTS


def _muscle_scene():
    global _MUSCLE_SCENE
    if _MUSCLE_SCENE is None:
        _MUSCLE_SCENE = trimesh.load(MUSCLES_GLB, force="scene")
    return _MUSCLE_SCENE


def muscle_verts(ids: list[str], sx: float | None = None) -> np.ndarray:
    scene = _muscle_scene()
    chunks: list[np.ndarray] = []
    for name in ids:
        geom = scene.geometry.get(name)
        if geom is None:
            continue
        v = np.asarray(geom.vertices, dtype=np.float64)
        if sx is not None:
            v = v[v[:, 0] * sx >= -0.004]
        if len(v):
            chunks.append(v)
    return np.vstack(chunks) if chunks else np.zeros((0, 3), dtype=np.float64)


def nearest_bone(point: np.ndarray, sx: float | None = None, ywin: float | None = None) -> np.ndarray:
    v = bone_verts()
    if sx is not None:
        v = v[v[:, 0] * sx >= -0.002]
    if ywin is not None:
        band = v[np.abs(v[:, 1] - point[1]) < ywin]
        if len(band) >= 8:
            v = band
    d = np.linalg.norm(v - point[None, :], axis=1)
    return v[int(d.argmin())].copy()


def posterior_midline(y: float, ywin: float = 0.012) -> np.ndarray:
    """Most posterior midline bone vertex near this height (spinous / nuchal)."""
    v = bone_verts()
    mask = (np.abs(v[:, 1] - y) < ywin) & (np.abs(v[:, 0]) < 0.028)
    pts = v[mask]
    if len(pts) < 4:
        mask = (np.abs(v[:, 1] - y) < ywin * 2.2) & (np.abs(v[:, 0]) < 0.04)
        pts = v[mask]
    if len(pts) == 0:
        return np.array([0.0, y, -0.02], dtype=np.float64)
    return pts[pts[:, 2].argmin()].copy()


def fix_landmarks(p: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Correct bbox-extremum landmarks that land on the wrong bony prominence."""
    out = {k: np.asarray(v, dtype=float).copy() for k, v in p.items()}
    v = bone_verts()

    def _pick(mask: np.ndarray, fallback: np.ndarray) -> np.ndarray:
        pts = v[mask]
        return pts[int(np.linalg.norm(pts - fallback[None, :], axis=1).argmin())].copy() if len(pts) else fallback

    # Lateral femoral condyle was bbox_min_x of the whole femur (= greater trochanter).
    guess = np.array([-0.110, -0.469, 0.029], dtype=float)
    out["condyle-lat-femur-d"] = _pick(
        (v[:, 1] > -0.495) & (v[:, 1] < -0.445) & (v[:, 0] < -0.08) & (v[:, 0] > -0.14) & (v[:, 2] > 0.0) & (v[:, 2] < 0.055),
        guess,
    )
    # Medial humeral epicondyle was bbox_max_x near the humeral head.
    ole = out["olecrane-d"]
    med_guess = ole + np.array([0.022, 0.008, -0.006])
    out["epicondyle-med-humerus-d"] = _pick(
        (np.abs(v[:, 1] - ole[1]) < 0.028) & (v[:, 0] < -0.15) & (v[:, 0] > -0.22) & (v[:, 2] > -0.02) & (v[:, 2] < 0.05),
        med_guess,
    )
    return out


def spinal_levels(p: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Approximate vertebral centroids, interpolating missing named levels."""
    c1, c2, c7 = p["c1"], p["c2"], p["c7"]
    t1, t12 = p["t1"], p["t12"]
    l1, l5, sac = p["l1"], p["l5"], p["sacrum"]
    levels: dict[str, np.ndarray] = {
        "C1": c1,
        "C2": c2,
        "C7": c7,
        "T1": t1,
        "T12": t12,
        "L1": l1,
        "L5": l5,
        "S2": sac,
    }
    for i in range(3, 7):
        levels[f"C{i}"] = mix(c2, c7, (i - 2) / 5.0)
    for i in range(2, 12):
        levels[f"T{i}"] = mix(t1, t12, (i - 1) / 11.0)
    for i in range(2, 5):
        levels[f"L{i}"] = mix(l1, l5, (i - 1) / 4.0)
    levels["S1"] = mix(l5, sac, 0.42)
    levels["S3"] = mix(sac, sac + np.array([0.0, -0.028, -0.012]), 0.55)
    return levels


def foramen(level: np.ndarray, sx: float, region: str) -> np.ndarray:
    """Pedagogical intervertebral / sacral foramen just off the vertebral body."""
    if region == "cervical":
        # Pedicle / IVF: slightly caudal and posterior to the body centroid.
        return off(level, x=sx * 0.022, y=-0.005, z=-0.002)
    if region == "thoracic":
        return off(level, x=sx * 0.024, y=-0.004, z=-0.006)
    if region == "lumbar":
        return off(level, x=sx * 0.034, y=-0.007, z=-0.016)
    # Anterior sacral foramen, then the trunk heads toward the greater sciatic notch.
    return off(level, x=sx * 0.028, y=-0.010, z=0.002)


def piriformis_underside(sx: float) -> np.ndarray:
    """Point on the inferior / deep border of piriformis (infrapiriform exit)."""
    scene = _muscle_scene()
    mesh = scene.geometry.get("piriforme")
    if mesh is None:
        return np.array([sx * 0.055, -0.03, -0.022], dtype=float)
    v = np.asarray(mesh.vertices, dtype=np.float64)
    side = v[v[:, 0] * sx > 0.018]
    if len(side) < 12:
        return np.array([sx * 0.055, -0.03, -0.022], dtype=float)
    xabs = np.abs(side[:, 0])
    # Medial–mid belly sits over the greater sciatic foramen, not the GT.
    gsf = side[(xabs > 0.028) & (xabs < 0.085)]
    if len(gsf) < 8:
        gsf = side
    ycut = float(np.percentile(gsf[:, 1], 18))
    band = gsf[gsf[:, 1] <= ycut]
    if len(band) < 4:
        band = gsf
    zcut = float(np.percentile(band[:, 2], 22))
    deep = band[band[:, 2] <= zcut]
    p = deep.mean(0) if len(deep) else band.mean(0)
    # Force the corridor inferior and posterior to the muscle (infrapiriform).
    p[1] = min(float(p[1]), float(side[:, 1].min()) - 0.012)
    p[2] = min(float(p[2]), -0.032)
    return p + np.array([sx * 0.008, 0.0, -0.006], dtype=float)


class BodyCloud:
    """Point cloud of bone ± regional muscles for outer-envelope queries."""

    def __init__(self, muscle_ids: list[str] | None = None, sx: float | None = None):
        chunks = [bone_verts()]
        if muscle_ids:
            mv = muscle_verts(muscle_ids, sx=sx)
            if len(mv):
                chunks.append(mv)
        pts = np.vstack(chunks)
        if sx is not None:
            pts = pts[pts[:, 0] * sx >= -0.006]
        self.pts = pts
        self.tree = cKDTree(pts)

    def clip_to_capsule(self, a: np.ndarray, b: np.ndarray, radius: float, y_pad: float = 0.04) -> "BodyCloud":
        """Drop points that are not near the limb segment (avoids grabbing the hanging arm)."""
        a = np.asarray(a, dtype=np.float64)
        b = np.asarray(b, dtype=np.float64)
        ab = b - a
        length = float(np.linalg.norm(ab))
        if length < 1e-6 or len(self.pts) == 0:
            return self
        direction = ab / length
        rel = self.pts - a[None, :]
        t = np.clip(rel @ direction, -y_pad, length + y_pad)
        closest = a[None, :] + t[:, None] * direction[None, :]
        dist = np.linalg.norm(self.pts - closest, axis=1)
        y0, y1 = min(float(a[1]), float(b[1])) - y_pad, max(float(a[1]), float(b[1])) + y_pad
        mask = (dist < radius) & (self.pts[:, 1] >= y0) & (self.pts[:, 1] <= y1)
        if int(mask.sum()) >= 24:
            self.pts = self.pts[mask]
            self.tree = cKDTree(self.pts)
        return self

    def posterior_z(self, x: float, y: float, xwin: float = 0.016, ywin: float = 0.016) -> float | None:
        mask = (np.abs(self.pts[:, 0] - x) < xwin) & (np.abs(self.pts[:, 1] - y) < ywin) & (self.pts[:, 2] < 0.02)
        band = self.pts[mask]
        if len(band) < 4:
            _, idx = self.tree.query([x, y, 0.0], k=min(24, len(self.pts)))
            band = self.pts[np.atleast_1d(idx)]
            band = band[(np.abs(band[:, 0] - x) < xwin * 2.5) & (np.abs(band[:, 1] - y) < ywin * 2.5)]
        if len(band) == 0:
            return None
        return float(np.percentile(band[:, 2], 10))

    def envelope_point(
        self,
        center: np.ndarray,
        lat: np.ndarray,
        ant: np.ndarray,
        theta: float,
        ywin: float = 0.018,
        dtheta: float = 0.38,
        standoff: float = 0.003,
    ) -> np.ndarray:
        y = float(center[1])
        band = self.pts[np.abs(self.pts[:, 1] - y) < ywin]
        if len(band) < 8:
            _, idx = self.tree.query(center, k=min(48, len(self.pts)))
            band = self.pts[np.atleast_1d(idx)]
        rel = band - center[None, :]
        rlat = rel @ lat
        rant = rel @ ant
        ang = np.arctan2(rant, rlat)
        rad = np.hypot(rlat, rant)
        delta = np.abs((ang - theta + np.pi) % (2.0 * np.pi) - np.pi)
        sel = (delta < dtheta) & (rad > 0.008)
        if np.any(sel):
            r = float(np.percentile(rad[sel], 90))
        elif len(rad):
            r = float(rad[int(delta.argmin())])
        else:
            r = 0.05
        direction = math_cos(theta) * lat + math_sin(theta) * ant
        return center + direction * (r + standoff)


def math_cos(t: float) -> float:
    return float(np.cos(t))


def math_sin(t: float) -> float:
    return float(np.sin(t))


THIGH_MUSCLES = [
    "vaste-lateral",
    "vaste-intermediaire",
    "vaste-medial",
    "droit-femoral",
    "biceps-femoral",
    "tenseur-du-fascia-lata",
    "sartorius",
    "semi-tendineux",
    "semi-membraneux",
]

LEG_MUSCLES = [
    "gastrocnemien",
    "soleaire",
    "tibial-anterieur",
    "long-fibulaire",
    "court-fibulaire",
]

BACK_MUSCLES = [
    "grand-dorsal",
    "iliocostal-lombaire",
    "iliocostal-thoracique",
    "longissimus-du-thorax",
]


def wrap_limb_grid(
    cloud: BodyCloud,
    proximal: np.ndarray,
    distal: np.ndarray,
    sx: float,
    *,
    theta0: float,
    theta1: float,
    n_len: int = 20,
    n_th: int = 16,
    standoff: float = 0.0028,
    y_pad: tuple[float, float] = (0.0, 0.0),
) -> np.ndarray:
    """Open wrap sheet on the outer envelope of a limb (anatomy-chart sleeve)."""
    axis = distal - proximal
    length = float(np.linalg.norm(axis))
    z_axis = axis / max(length, 1e-9)
    lat = np.array([sx, 0.0, 0.0], dtype=float)
    lat = lat - z_axis * np.dot(lat, z_axis)
    lat /= max(np.linalg.norm(lat), 1e-9)
    ant = np.cross(z_axis, lat)
    ant /= max(np.linalg.norm(ant), 1e-9)

    grid = np.zeros((n_len, n_th, 3), dtype=np.float64)
    for i in range(n_len):
        t = i / (n_len - 1)
        y = float(proximal[1] * (1.0 - t) + distal[1] * t) + y_pad[0] * (1.0 - t) + y_pad[1] * t
        center = mix(proximal, distal, t)
        center[1] = y
        # pinch the angular span slightly at the ends
        pinch = 0.08 * (1.0 - 4.0 * t * (1.0 - t))
        ta, tb = theta0 + pinch, theta1 - pinch
        for j in range(n_th):
            s = j / (n_th - 1)
            th = ta * (1.0 - s) + tb * s
            grid[i, j] = cloud.envelope_point(center, lat, ant, th, standoff=standoff)
    return grid


def posterior_back_grid(
    cloud: BodyCloud,
    ys: np.ndarray,
    half_widths: np.ndarray,
    *,
    n_across: int = 11,
    standoff: float = 0.0024,
) -> np.ndarray:
    """Midline → flank sheet snapped to the posterior body envelope."""
    grid = np.zeros((len(ys), n_across, 3), dtype=np.float64)
    for i, (y, half) in enumerate(zip(ys, half_widths)):
        spin = posterior_midline(float(y), ywin=0.014)
        for j in range(n_across):
            s = j / (n_across - 1)
            # slight diamond: more lateral in the mid-lumbar belt
            x = float(half) * (s**0.92)
            z = cloud.posterior_z(x if x > 0.004 else 0.0, float(y))
            if z is None:
                z = float(spin[2])
            # standoff further posterior so the sheet sits on muscle, not inside bone
            grid[i, j] = np.array([x, float(y), z - standoff], dtype=np.float64)
        # pin column 0 to the spinous line
        grid[i, 0] = np.array([0.0, float(y), float(spin[2]) - standoff * 0.4], dtype=np.float64)
    return grid
