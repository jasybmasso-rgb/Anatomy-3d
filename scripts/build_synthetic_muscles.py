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


def _latissimus_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Broad thoracolumbar origin → axillary wrap → intertubercular groove."""
    suf = "d" if sx < 0 else "g"
    t7 = mix(p["t1"], p["t12"], 0.55) + np.array([sx * 0.014, 0.0, -0.058])
    t9 = mix(p["t1"], p["t12"], 0.70) + np.array([sx * 0.018, 0.0, -0.056])
    t12s = off(p["t12"], x=sx * 0.022, z=-0.052)
    l2 = mix(p["l1"], p["l5"], 0.35) + np.array([sx * 0.028, 0.0, -0.048])
    l5s = off(p["l5"], x=sx * 0.032, z=-0.046)
    sac = off(p["sacrum"], x=sx * 0.028, y=0.012, z=-0.038)
    eips = off(p[f"eips-{suf}"], z=-0.014)
    crest = p[f"crete-iliaque-{suf}"]
    crest_post = mix(eips, crest, 0.40) + np.array([0.0, 0.006, -0.022])
    crest_lat = off(crest, x=sx * 0.010, z=-0.012)
    scap = off(p[f"angle-inf-scapula-{suf}"], x=sx * 0.006, y=-0.008, z=-0.010)
    # Lower ribs, mid-axillary (no dedicated landmarks).
    rib11 = np.array([sx * 0.112, 0.205, 0.008], dtype=np.float64)
    rib9 = np.array([sx * 0.118, 0.255, 0.022], dtype=np.float64)

    head = p[f"tete-humerus-{suf}"]
    # Floor of the intertubercular groove: distal / anterior / slightly lateral to the head.
    insert = head + np.array([sx * 0.014, -0.030, 0.026])

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

    paths: list[np.ndarray] = []
    for i, origin in enumerate(origins):
        climb = 0.045 + 0.012 * (i / max(len(origins) - 1, 1))
        c1 = origin + np.array([sx * (0.048 + 0.01 * (i % 3)), climb, -0.008])
        c1[0] = sx * max(abs(float(c1[0])), 0.088)
        c2 = mix(origin, insert, 0.64) + np.array([sx * 0.028, 0.012, 0.038])
        c2[0] = sx * max(abs(float(c2[0])), 0.125)
        paths.append(bezier_cubic(origin, c1, c2, insert, 24))

    sheet = _sheet(paths, thickness=0.0072)
    # Posterior axillary fold: thicker converging border.
    fold = paths[10]
    radii = np.linspace(0.0048, 0.0022, len(fold))
    border = loft_tube(fold, radii, radial=8, caps=True)
    tendon = loft_tube(
        bezier_cubic(
            mix(rib9, insert, 0.55),
            mix(rib9, insert, 0.72) + np.array([sx * 0.01, 0.004, 0.012]),
            mix(rib9, insert, 0.88) + np.array([sx * 0.004, -0.002, 0.008]),
            insert,
            12,
        ),
        np.linspace(0.0055, 0.0030, 12),
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
    for t_ins, width in ((0.26, 0.008), (0.50, 0.008), (0.74, 0.007)):
        a = mix(pub, mix(xiph, costal, 0.4), t_ins) + np.array([sx * 0.010, 0.0, 0.010])
        b = mix(pub, mix(xiph, costal, 0.4), t_ins) + np.array([sx * 0.038, 0.0, 0.010])
        parts.append(loft_ribbon(np.linspace(a, b, 8), width=width, thickness=0.0036))
    return _concat(parts)


def _temporalis_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    suf = "d" if sx < 0 else "g"
    par = p[f"os-parietal-{suf}"]
    temp = p[f"os-temporal-{suf}"]
    front = p["os-frontal"]
    coronoid = np.array([sx * 0.046, 0.626, 0.056], dtype=np.float64)
    origins = [
        off(par, x=sx * 0.016, y=0.016, z=-0.010),
        off(par, x=sx * 0.026, y=0.006, z=0.014),
        off(front, x=sx * 0.050, y=0.022, z=-0.012),
        off(temp, x=sx * 0.016, y=0.058, z=0.006),
        off(temp, x=sx * 0.020, y=0.032, z=0.018),
    ]
    paths = []
    for origin in origins:
        c1 = mix(origin, coronoid, 0.35) + np.array([sx * 0.008, -0.006, 0.006])
        c2 = mix(origin, coronoid, 0.72) + np.array([sx * 0.004, -0.004, 0.004])
        paths.append(bezier_cubic(origin, c1, c2, coronoid, 18))
    return _sheet(paths, thickness=0.0058)


def _masseter_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    suf = "d" if sx < 0 else "g"
    zyg_ant = off(p[f"maxillaire-{suf}"], x=sx * 0.040, y=0.030, z=-0.004)
    zyg_post = off(p[f"os-temporal-{suf}"], x=sx * 0.016, y=0.014, z=0.026)
    angle = np.array([sx * 0.054, 0.570, 0.052], dtype=np.float64)
    ramus = np.array([sx * 0.050, 0.598, 0.050], dtype=np.float64)
    # Superficial (zygomatic arch → mandibular angle) + deep (arch → ramus).
    super_paths = []
    for t, dest in ((0.15, angle), (0.5, mix(angle, ramus, 0.35)), (0.85, mix(angle, ramus, 0.15))):
        o = mix(zyg_ant, zyg_post, t)
        c1 = mix(o, dest, 0.4) + np.array([sx * 0.006, 0.0, 0.006])
        super_paths.append(bezier_cubic(o, c1, mix(o, dest, 0.75), dest, 14))
    deep_o = mix(zyg_ant, zyg_post, 0.7) + np.array([-sx * 0.006, 0.0, -0.006])
    deep = bezier_cubic(deep_o, mix(deep_o, ramus, 0.45), mix(deep_o, ramus, 0.75), ramus, 12)
    return _concat([_sheet(super_paths, thickness=0.0075), loft_tube(deep, np.full(12, 0.0036), radial=8, caps=True)])


def _pterygoid_medial_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    sph = off(p["os-sphenoid"], x=sx * 0.018, y=-0.006, z=0.008)
    maxil = off(p[f"maxillaire-{'d' if sx < 0 else 'g'}"], x=sx * 0.008, y=0.004, z=-0.016)
    angle = np.array([sx * 0.030, 0.568, 0.048], dtype=np.float64)
    paths = []
    for origin in (sph, mix(sph, maxil, 0.55), maxil):
        c1 = mix(origin, angle, 0.4) + np.array([sx * 0.006, -0.004, -0.004])
        paths.append(bezier_cubic(origin, c1, mix(origin, angle, 0.75), angle, 14))
    return _sheet(paths, thickness=0.0054)


def _pterygoid_lateral_side(p: dict[str, np.ndarray], sx: float) -> trimesh.Trimesh:
    """Mostly horizontal: lateral pterygoid plate → TMJ / condyle."""
    sph = off(p["os-sphenoid"], x=sx * 0.024, y=0.012, z=0.016)
    sph_inf = off(p["os-sphenoid"], x=sx * 0.022, y=-0.004, z=0.020)
    condyle = off(p[f"os-temporal-{'d' if sx < 0 else 'g'}"], x=sx * 0.008, y=0.006, z=0.006)
    paths = []
    for origin in (sph, sph_inf):
        c1 = mix(origin, condyle, 0.45) + np.array([sx * 0.008, 0.002, 0.004])
        paths.append(bezier_cubic(origin, c1, mix(origin, condyle, 0.78), condyle, 12))
    return _sheet(paths, thickness=0.0046)


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
