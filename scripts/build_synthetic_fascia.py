"""Schematic regional deep-fascia sleeves (synthetic-v2). Quality over quantity."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

from mesh_primitives import cylinder_sleeve, loft_ribbon

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"

NOTE = (
    "Schéma pédagogique (synthetic-v2) : manchon fascial mince ancré sur les "
    "repères. Ce n’est pas une nappe cadavérique. Tractus ilio-tibiaux = BP3D."
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
        "source": "synthetic-v2",
        "sourceName": id_,
        "fmaId": "",
        "fileIds": [],
        "centroid": [round(float(x), 5) for x in mesh.vertices.mean(0)],
    }


def _sheet(a, b, c, d, thickness=0.0022) -> trimesh.Trimesh:
    """Loft two ribbons and concatenate into a thin posterior sheet."""
    path_a = np.linspace(0.0, 1.0, 10)[:, None] * (b - a) + a
    path_b = np.linspace(0.0, 1.0, 10)[:, None] * (d - c) + c
    mid = (path_a + path_b) / 2.0
    width = float(np.linalg.norm(path_a[5] - path_b[5])) + 0.01
    return loft_ribbon(mid, width=max(width, 0.04), thickness=thickness, binormal=np.array([0.0, 0.0, 1.0]))


def build() -> tuple[list[tuple[str, trimesh.Trimesh]], list[dict]]:
    p = load_lm()
    meshes: list[tuple[str, trimesh.Trimesh]] = []
    catalog: list[dict] = []

    def add(id_, name, latin, region, mesh):
        if mesh is None or mesh.vertices.size == 0:
            return
        meshes.append((id_, mesh))
        catalog.append(entry(id_, name, latin, region, mesh))

    for suf, side in (("d", "droit"), ("g", "gauche")):
        sx = -1.0 if suf == "d" else 1.0
        crest = p[f"crete-iliaque-{suf}"]
        gt = p[f"grand-trochanter-{suf}"]
        lat_k = p[f"tete-fibula-{suf}"]
        eias = p[f"eias-{suf}"]
        thigh_top = mix(crest, eias, 0.35)
        thigh_bot = mix(gt, lat_k, 0.15)
        add(
            f"fascia-lata-{suf}",
            f"Fascia lata {side}",
            "Fascia lata",
            "cuisse",
            cylinder_sleeve(
                off(thigh_top, x=sx * 0.02),
                off(thigh_bot, x=sx * 0.015),
                radius=0.055,
                thickness=0.0022,
            ),
        )
        mal = mix(p[f"maleole-laterale-{suf}"], p[f"maleole-mediale-{suf}"], 0.5)
        add(
            f"fascia-crural-{suf}",
            f"Fascia crural {side}",
            "Fascia cruris",
            "jambe",
            cylinder_sleeve(
                off(lat_k, y=0.02),
                off(mal, y=0.04),
                radius=0.038,
                thickness=0.002,
            ),
        )
        ole = p[f"olecrane-{suf}"]
        sty = mix(p[f"styloide-radial-{suf}"], p[f"styloide-ulnaire-{suf}"], 0.5)
        add(
            f"fascia-antebrachial-{suf}",
            f"Fascia antébrachial {side}",
            "Fascia antebrachii",
            "avant-bras",
            cylinder_sleeve(
                mix(ole, sty, 0.12),
                mix(ole, sty, 0.92),
                radius=0.028,
                thickness=0.0018,
            ),
        )

    # Thoracolumbar posterior sheet — one piece, not two sticks.
    add(
        "fascia-thoracolombaire",
        "Fascia thoraco-lombaire (nappe postérieure)",
        "Fascia thoracolumbalis",
        "tronc",
        _sheet(
            off(p["t12"], z=-0.032, x=-0.04),
            off(p["eips-d"], z=-0.018),
            off(p["t12"], z=-0.032, x=0.04),
            off(p["eips-g"], z=-0.018),
            thickness=0.0026,
        ),
    )
    return meshes, catalog
