"""Schematic regional deep-fascia sheets (synthetic-v2). Quality over quantity.

Open wrap panels follow limb contours; no closed cylinder sleeves.
Antebrachial tubes and palmar/plantar sticks are omitted.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import trimesh

from mesh_primitives import grid_sheet, wrap_panel

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"

NOTE = (
    "Schéma pédagogique (synthetic-v2) : nappe fasciale mince (feuille ouverte "
    "qui épouse le contour du membre, bords irréguliers). Ce n’est pas une "
    "nappe cadavérique. Tractus ilio-tibiaux = BP3D."
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


def tlf_sheet(p: dict[str, np.ndarray]) -> trimesh.Trimesh:
    top = p["t12"]
    eips_d, eips_g = p["eips-d"], p["eips-g"]
    bot_y = 0.5 * (eips_d[1] + eips_g[1])
    bot_z = 0.5 * (eips_d[2] + eips_g[2]) - 0.02
    top_z = top[2] - 0.04
    rows, cols = 10, 9
    grid = []
    for i in range(rows):
        t = i / (rows - 1)
        y = top[1] * (1.0 - t) + bot_y * t
        z = top_z * (1.0 - t) + bot_z * t
        half = 0.048 + 0.032 * math.sin(t * math.pi)
        row = []
        for j in range(cols):
            s = j / (cols - 1)
            edge = min(s, 1.0 - s)
            flare = 0.88 + 0.12 * (1.0 - (1.0 - edge) ** 2)
            x = (-half + 2.0 * half * s) * flare
            # irregular posterior surface + scalloped lateral border
            zz = z - 0.007 * math.sin(s * math.pi) * (0.55 + 0.45 * math.sin(t * 3.4))
            zz -= 0.003 * (1.0 - edge) * abs(math.sin(t * 9.0 + s * 3.0))
            yy = y + 0.0035 * math.sin(s * 5.2 + t * 2.4)
            row.append([x, yy, zz])
        grid.append(row)
    return grid_sheet(grid, thickness=0.0019)


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
        lateral = np.array([sx, 0.0, 0.0], dtype=float)
        crest = p[f"crete-iliaque-{suf}"]
        gt = p[f"grand-trochanter-{suf}"]
        lat_k = p[f"tete-fibula-{suf}"]
        eias = p[f"eias-{suf}"]
        thigh_top = mix(crest, eias, 0.35)
        thigh_bot = mix(gt, lat_k, 0.12)
        add(
            f"fascia-lata-{suf}",
            f"Fascia lata {side}",
            "Fascia lata",
            "cuisse",
            wrap_panel(
                off(thigh_top, x=sx * 0.018),
                off(thigh_bot, x=sx * 0.012),
                radius_a=0.078,
                radius_b=0.056,
                theta0=-0.95,
                theta1=1.05,
                oval=(1.0, 0.82),
                length_samples=18,
                theta_samples=16,
                thickness=0.0016,
                lateral=lateral,
            ),
        )
        mal = mix(p[f"maleole-laterale-{suf}"], p[f"maleole-mediale-{suf}"], 0.5)
        add(
            f"fascia-crural-{suf}",
            f"Fascia crural {side}",
            "Fascia cruris",
            "jambe",
            wrap_panel(
                off(lat_k, y=0.018, x=sx * 0.008),
                off(mal, y=0.045, x=sx * 0.006),
                radius_a=0.046,
                radius_b=0.034,
                theta0=-0.55,
                theta1=1.28,
                oval=(1.0, 0.8),
                length_samples=16,
                theta_samples=15,
                thickness=0.0015,
                lateral=lateral,
            ),
        )

    add(
        "fascia-thoracolombaire",
        "Fascia thoraco-lombaire (nappe postérieure)",
        "Fascia thoracolumbalis",
        "tronc",
        tlf_sheet(p),
    )
    return meshes, catalog
