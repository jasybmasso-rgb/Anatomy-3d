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

    # Latissimus: iliac crest / PSIS / lumbar spine → intertubercular groove.
    lats: list[trimesh.Trimesh] = []
    for suf in ("d", "g"):
        hum = p[f"tubercule-majeur-{suf}"]
        origins = [
            p[f"crete-iliaque-{suf}"],
            p[f"eips-{suf}"],
            off(p["l5"], x=(-0.02 if suf == "d" else 0.02), z=-0.02),
            off(p["t12"], x=(-0.025 if suf == "d" else 0.025), z=-0.025),
            off(p["sacrum"], x=(-0.015 if suf == "d" else 0.015)),
        ]
        for origin in origins:
            lats.append(ribbon(origin, mix(origin, hum, 0.92), width=0.028, thickness=0.012))
            lats.append(band(mix(origin, hum, 0.15), mix(origin, hum, 0.85), 0.012))
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
