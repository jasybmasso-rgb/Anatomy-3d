"""Landmark-anchored muscles missing from BodyParts3D 4.0.

Latissimus and rectus: wrap / strap sheets matching real attachments
(not stacked capsules). Mastication: temporalis, masseter, pterygoids.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

from mesh_primitives import bezier_cubic, grid_sheet, loft_ribbon, loft_tube

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"

SYNTH_NOTES = (
    "Educational landmark-anchored mesh — BodyParts3D 4.0 has no dedicated "
    "OBJ for this muscle. Attachments follow classical O/I; shape is a "
    "schematic solid, not a cadaver segmentation."
)


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


def _lat_wrap_path(origin: np.ndarray, insert: np.ndarray, sx: float, n: int = 24) -> np.ndarray:
    """C-shaped path: stay on the back, climb the flank, then tendon to the humerus.

    Linear mixes origin→insert would cut through the thorax; control points are
    forced onto the mid-axillary corridor.
    """
    back_x = sx * max(abs(float(origin[0])) + 0.055, 0.125)
    c1 = np.array([back_x, float(origin[1]) + 0.035, min(float(origin[2]), -0.028)])
    axilla_x = sx * 0.168
    c2 = np.array(
        [
            axilla_x,
            float(origin[1]) * 0.32 + float(insert[1]) * 0.68,
            0.012,
        ]
    )
    return bezier_cubic(origin, c1, c2, insert, n)


def _latissimus_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Broad thoracolumbar origin → axillary wrap → intertubercular groove."""
    suf = "d" if sx < 0 else "g"
    t7 = mix(p["t1"], p["t12"], 0.55) + np.array([sx * 0.016, 0.0, -0.062])
    t9 = mix(p["t1"], p["t12"], 0.70) + np.array([sx * 0.020, 0.0, -0.060])
    t12s = off(p["t12"], x=sx * 0.024, z=-0.056)
    l2 = mix(p["l1"], p["l5"], 0.35) + np.array([sx * 0.030, 0.0, -0.052])
    l5s = off(p["l5"], x=sx * 0.034, z=-0.050)
    sac = off(p["sacrum"], x=sx * 0.030, y=0.012, z=-0.042)
    eips = off(p[f"eips-{suf}"], z=-0.018)
    crest = p[f"crete-iliaque-{suf}"]
    crest_post = mix(eips, crest, 0.40) + np.array([0.0, 0.006, -0.028])
    crest_lat = off(crest, x=sx * 0.012, z=-0.018)
    scap = off(p[f"angle-inf-scapula-{suf}"], x=sx * 0.010, y=-0.006, z=-0.016)
    # Costal origins stay on the mid-axillary line (not the anterior chest).
    rib11 = np.array([sx * 0.125, 0.200, -0.008], dtype=np.float64)
    rib9 = np.array([sx * 0.132, 0.248, 0.000], dtype=np.float64)

    head = p[f"tete-humerus-{suf}"]
    # Floor of the intertubercular groove: distal / anterior / slightly lateral to the head.
    insert = head + np.array([sx * 0.012, -0.028, 0.022])

    origins = [
        t7,
        t9,
        t12s,
        l2,
        l5s,
        sac,
        eips,
        crest_post,
        crest_lat,
        rib11,
        rib9,
        scap,
    ]
    paths = [_lat_wrap_path(origin, insert, sx) for origin in origins]
    sheet = _sheet(paths, thickness=0.0068)
    fold = _lat_wrap_path(rib9, insert, sx)
    border = loft_tube(fold, np.linspace(0.0050, 0.0024, len(fold)), radial=8, caps=True)
    tendon = loft_tube(
        bezier_cubic(
            np.array([sx * 0.155, 0.38, 0.018]),
            np.array([sx * 0.162, 0.42, 0.028]),
            insert + np.array([sx * 0.006, -0.008, 0.006]),
            insert,
            12,
        ),
        np.linspace(0.0052, 0.0028, 12),
        radial=8,
        caps=True,
    )
    return _concat([sheet, border, tendon])


def _rectus_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Paramedian strap pubis → xiphoid / costal 5–7, with tendinous intersections."""
    pub = off(p["symphyse-pubienne"], x=sx * 0.016, y=0.014, z=0.048)
    xiph = off(p["xiphoide"], x=sx * 0.014, z=0.016)
    costal = off(p["xiphoide"], x=sx * 0.036, y=-0.018, z=0.008)

    n_along = 26
    n_across = 6
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        t = i / (n_along - 1)
        belly = 4.0 * t * (1.0 - t)
        # Upper third fans slightly toward the costal cartilage.
        top = mix(xiph, costal, 0.35 + 0.25 * t)
        center = mix(pub, top, t) + np.array([0.0, 0.0, 0.014 * belly])
        half = 0.013 + 0.007 * belly
        for j in range(n_across):
            s = j / (n_across - 1)
            grid[i, j] = center + np.array([sx * (0.008 + s * 2.0 * half), 0.0, 0.0])

    # Thinner at the three tendinous intersections (xiphoid, mid, umbilical).
    sheet = grid_sheet(grid, thickness=0.0105)
    parts = [sheet]
    for t_ins in (0.24, 0.48, 0.72):
        mid = mix(pub, mix(xiph, costal, 0.4), t_ins)
        a = mid + np.array([sx * 0.008, 0.0, 0.016])
        b = mid + np.array([sx * 0.042, 0.0, 0.016])
        # Recessed inscription: thinner, slightly more anterior so it reads as a tendon band.
        parts.append(loft_ribbon(np.linspace(a, b, 8), width=0.011, thickness=0.0024))
    return _concat(parts)


def _temporalis_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Fan on the temporal fossa → coronoid. Landmarks are bone centroids (too medial);
    positions are taken on the outer cranial table so the muscle sits on the skull side."""
    coronoid = np.array([sx * 0.062, 0.618, 0.052], dtype=np.float64)
    origins = [
        np.array([sx * 0.068, 0.748, -0.018], dtype=np.float64),
        np.array([sx * 0.074, 0.742, 0.012], dtype=np.float64),
        np.array([sx * 0.070, 0.728, 0.055], dtype=np.float64),
        np.array([sx * 0.076, 0.700, -0.004], dtype=np.float64),
        np.array([sx * 0.072, 0.682, 0.042], dtype=np.float64),
        np.array([sx * 0.068, 0.658, 0.028], dtype=np.float64),
    ]
    paths = []
    for origin in origins:
        c1 = mix(origin, coronoid, 0.32) + np.array([sx * 0.010, -0.004, 0.004])
        c2 = mix(origin, coronoid, 0.70) + np.array([sx * 0.004, -0.002, 0.002])
        paths.append(bezier_cubic(origin, c1, c2, coronoid, 18))
    return _sheet(paths, thickness=0.0072)


def _masseter_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    zyg_ant = np.array([sx * 0.068, 0.658, 0.082], dtype=np.float64)
    zyg_post = np.array([sx * 0.072, 0.650, 0.038], dtype=np.float64)
    angle = np.array([sx * 0.070, 0.548, 0.048], dtype=np.float64)
    ramus = np.array([sx * 0.068, 0.598, 0.055], dtype=np.float64)
    super_paths = []
    for t in (0.08, 0.34, 0.58, 0.86):
        o = mix(zyg_ant, zyg_post, t)
        dest = mix(angle, ramus, 0.15 + 0.35 * t)
        c1 = mix(o, dest, 0.42) + np.array([sx * 0.008, 0.0, 0.004])
        super_paths.append(bezier_cubic(o, c1, mix(o, dest, 0.78), dest, 14))
    deep_o = mix(zyg_ant, zyg_post, 0.72) + np.array([-sx * 0.004, 0.0, -0.006])
    deep = bezier_cubic(deep_o, mix(deep_o, ramus, 0.45), mix(deep_o, ramus, 0.75), ramus, 12)
    return _concat(
        [_sheet(super_paths, thickness=0.0090), loft_tube(deep, np.full(12, 0.0042), radial=8, caps=True)]
    )


def _pterygoid_medial_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    sph = np.array([sx * 0.028, 0.640, 0.055], dtype=np.float64)
    maxil = np.array([sx * 0.032, 0.618, 0.072], dtype=np.float64)
    angle = np.array([sx * 0.058, 0.554, 0.028], dtype=np.float64)
    paths = []
    for origin in (sph, mix(sph, maxil, 0.55), maxil):
        c1 = mix(origin, angle, 0.4) + np.array([sx * 0.010, -0.004, -0.006])
        paths.append(bezier_cubic(origin, c1, mix(origin, angle, 0.75), angle, 14))
    return _sheet(paths, thickness=0.0060)


def _pterygoid_lateral_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    sph = np.array([sx * 0.030, 0.658, 0.052], dtype=np.float64)
    sph_inf = np.array([sx * 0.028, 0.642, 0.058], dtype=np.float64)
    condyle = np.array([sx * 0.068, 0.652, 0.028], dtype=np.float64)
    paths = []
    for origin in (sph, sph_inf, mix(sph, sph_inf, 0.5)):
        c1 = mix(origin, condyle, 0.45) + np.array([sx * 0.008, 0.002, 0.002])
        paths.append(bezier_cubic(origin, c1, mix(origin, condyle, 0.78), condyle, 14))
    return _sheet(paths, thickness=0.0052)


def _bilateral(builder, p: dict[str, np.ndarray]) -> trimesh.Trimesh:
    return _concat([builder(p, -1.0), builder(p, 1.0)])


def build() -> dict[str, trimesh.Trimesh]:
    p = load_lm()
    return {
        "grand-dorsal": _bilateral(_latissimus_side, p),
        "droit-abdomen": _bilateral(_rectus_side, p),
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
