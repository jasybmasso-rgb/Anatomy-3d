"""Landmark-anchored stand-ins for muscles missing from BodyParts3D 4.0."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

from mesh_primitives import band, ribbon

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"


def load_lm() -> dict[str, np.ndarray]:
    data = json.loads(LANDMARKS.read_text(encoding="utf-8"))
    return {item["id"]: np.array(item["position"], dtype=float) for item in data["landmarks"]}


def mix(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    return a * (1.0 - t) + b * t


def off(p: np.ndarray, x: float = 0, y: float = 0, z: float = 0) -> np.ndarray:
    return p + np.array([x, y, z], dtype=float)


def _concat(parts: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    return trimesh.util.concatenate(parts)


def build() -> dict[str, trimesh.Trimesh]:
    p = load_lm()
    out: dict[str, trimesh.Trimesh] = {}

    # Latissimus: posterior-lateral wrap, iliac crest / spine → flank → humerus.
    lats: list[trimesh.Trimesh] = []
    for suf in ("d", "g"):
        sx = -1.0 if suf == "d" else 1.0
        hum = p[f"tubercule-majeur-{suf}"]
        gt = p[f"grand-trochanter-{suf}"]
        crest = p[f"crete-iliaque-{suf}"]
        eips = p[f"eips-{suf}"]
        flank = off(mix(crest, gt, 0.28), x=sx * 0.03, z=-0.06)
        axilla = off(mix(flank, hum, 0.58), z=-0.035, y=0.03)
        origins = [
            off(eips, z=-0.03),
            off(crest, z=-0.035),
            off(p["l5"], x=sx * 0.03, z=-0.045),
            off(p["t12"], x=sx * 0.045, z=-0.05),
            off(p["sacrum"], x=sx * 0.02, z=-0.03),
        ]
        for origin in origins:
            lats.append(ribbon(origin, flank, width=0.048, thickness=0.007))
            lats.append(ribbon(flank, axilla, width=0.036, thickness=0.007))
            lats.append(ribbon(axilla, hum, width=0.02, thickness=0.006))
    out["grand-dorsal"] = _concat(lats)

    # Rectus abdominis: two paramedian straps, xiphoid → pubis, with three intersections.
    abs_parts: list[trimesh.Trimesh] = []
    top = off(p["xiphoide"], z=0.035)
    mid = off(p["corps-sternum"], z=0.04, y=-0.04)
    pub = off(p["symphyse-pubienne"], z=0.03)
    for x in (-0.028, 0.028):
        a = off(top, x=x)
        b = off(mid, x=x)
        c = mix(off(mid, x=x), off(pub, x=x * 0.6), 0.45)
        d = off(pub, x=x * 0.45)
        abs_parts.append(ribbon(a, b, width=0.032, thickness=0.01))
        abs_parts.append(ribbon(b, c, width=0.03, thickness=0.01))
        abs_parts.append(ribbon(c, d, width=0.026, thickness=0.009))
        abs_parts.append(band(a, d, 0.011))
    out["droit-abdomen"] = _concat(abs_parts)
    return out
