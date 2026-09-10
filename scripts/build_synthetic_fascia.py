"""Educational synthetic fascia / aponeurosis sheets anchored on landmarks.json."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

from mesh_primitives import ribbon

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"

NOTE = (
    "Approximation pédagogique : nappe synthétique ancrée sur les repères v1. "
    "Pas un scan. Source: synthetic."
)


def load_lm() -> dict[str, np.ndarray]:
    data = json.loads(LANDMARKS.read_text(encoding="utf-8"))
    return {item["id"]: np.array(item["position"], dtype=float) for item in data["landmarks"]}


def mix(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    return a * (1.0 - t) + b * t


def off(p: np.ndarray, x: float = 0, y: float = 0, z: float = 0) -> np.ndarray:
    return p + np.array([x, y, z], dtype=float)


def entry(id_: str, name: str, latin: str, region: str, mesh: trimesh.Trimesh) -> dict:
    return {
        "id": id_,
        "name": name,
        "nameLatin": latin,
        "region": region,
        "notes": NOTE,
        "source": "synthetic",
        "sourceName": id_,
        "fmaId": "",
        "fileIds": [],
        "centroid": [round(float(x), 5) for x in mesh.vertices.mean(0)],
    }


def build() -> tuple[list[trimesh.Trimesh], list[dict]]:
    p = load_lm()
    meshes: list[trimesh.Trimesh] = []
    catalog: list[dict] = []

    def add(id_, name, latin, region, mesh):
        if mesh is None or mesh.vertices.size == 0:
            return
        meshes.append(mesh)
        catalog.append(entry(id_, name, latin, region, mesh))

    # Plantar aponeurosis: calcaneus → forward plantar pad (no metatarsal landmarks).
    for suf, side in (("d", "droit"), ("g", "gauche")):
        cal = p[f"calcaneus-{suf}"]
        tal = p[f"talus-{suf}"]
        distal = off(mix(cal, tal, 1.35), z=0.045, y=-0.018)
        add(
            f"aponevrose-plantaire-{suf}",
            f"Aponévrose plantaire {side}",
            "Aponeurosis plantaris",
            "pied",
            ribbon(cal, distal, width=0.028, thickness=0.0024),
        )

    # Palmar aponeurosis: continue past the styloids along the forearm axis.
    for suf, side in (("d", "droit"), ("g", "gauche")):
        ole = p[f"olecrane-{suf}"]
        sty = mix(p[f"styloide-radial-{suf}"], p[f"styloide-ulnaire-{suf}"], 0.5)
        axis = sty - ole
        palm = sty + axis * 0.22
        add(
            f"aponevrose-palmaire-{suf}",
            f"Aponévrose palmaire {side}",
            "Aponeurosis palmaris",
            "main",
            ribbon(sty, palm, width=0.022, thickness=0.0022),
        )

    # Thoracolumbar fascia: T12/L1 → iliac crests / PSIS (posterior sheet).
    add(
        "fascia-thoracolombaire-d",
        "Fascia thoraco-lombaire droit",
        "Fascia thoracolumbalis dextrum",
        "tronc",
        ribbon(off(p["t12"], z=-0.03), off(p["eips-d"], z=-0.015), width=0.055, thickness=0.003),
    )
    add(
        "fascia-thoracolombaire-g",
        "Fascia thoraco-lombaire gauche",
        "Fascia thoracolumbalis sinistrum",
        "tronc",
        ribbon(off(p["t12"], z=-0.03), off(p["eips-g"], z=-0.015), width=0.055, thickness=0.003),
    )
    add(
        "fascia-thoracolombaire-lombaire",
        "Fascia thoraco-lombaire (nappe lombaire)",
        "Fascia thoracolumbalis (pars lumbalis)",
        "tronc",
        ribbon(off(p["l1"], z=-0.028), off(p["sacrum"], z=-0.02), width=0.07, thickness=0.003),
    )

    # Linea alba / rectus sheath midline — thin anterior band.
    add(
        "ligne-blanche",
        "Ligne blanche",
        "Linea alba",
        "tronc",
        ribbon(off(p["xiphoide"], z=0.02), off(p["symphyse-pubienne"], z=0.025), width=0.012, thickness=0.002),
    )

    return meshes, catalog
