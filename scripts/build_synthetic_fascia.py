"""Schematic regional deep-fascia sheets (synthetic-v3). Quality over quantity.

Sheets snap to the skeleton / muscle envelope (anatomy-chart wrap), not
free-floating cylinders. Tractus ilio-tibiaux remain BodyParts3D.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from body_surface import (  # noqa: E402
    BACK_MUSCLES,
    LEG_MUSCLES,
    THIGH_MUSCLES,
    BodyCloud,
    fix_landmarks,
    load_lm,
    mix,
    off,
    posterior_back_grid,
    posterior_midline,
    wrap_limb_grid,
)
from mesh_primitives import fascicle_bundle, grid_sheet  # noqa: E402

NOTE = (
    "Schéma pédagogique (synthetic-v3) : nappe fasciale mince calée sur "
    "l’enveloppe osseuse et musculaire (comme une planche d’atlas), bords "
    "libres irréguliers. Ce n’est pas une nappe cadavérique. "
    "Tractus ilio-tibiaux = BodyParts3D 4.0."
)


def entry(id_: str, name: str, latin: str, region: str, mesh: trimesh.Trimesh) -> dict:
    return {
        "id": id_,
        "name": name,
        "nameLatin": latin,
        "region": region,
        "notes": NOTE,
        "source": "synthetic-v3",
        "sourceName": id_,
        "fmaId": "",
        "fileIds": [],
        "centroid": [round(float(x), 5) for x in mesh.vertices.mean(0)],
    }


def _mirror_x(grid: np.ndarray) -> np.ndarray:
    out = grid.copy()
    out[:, :, 0] *= -1.0
    return out[:, ::-1, :]


def tlf_sheet(p: dict[str, np.ndarray]) -> trimesh.Trimesh:
    """Posterior layer of the thoracolumbar fascia: spinous T12–S1 → iliac crest."""
    cloud = BodyCloud(BACK_MUSCLES, sx=None)
    mask = (
        (cloud.pts[:, 1] > 0.02)
        & (cloud.pts[:, 1] < 0.26)
        & (cloud.pts[:, 2] < 0.03)
        & (np.abs(cloud.pts[:, 0]) < 0.16)
    )
    if int(mask.sum()) >= 40:
        cloud.pts = cloud.pts[mask]
        from scipy.spatial import cKDTree

        cloud.tree = cKDTree(cloud.pts)
    t12, l5, sac = p["t12"], p["l5"], p["sacrum"]
    crest = 0.5 * (p["crete-iliaque-d"] + p["crete-iliaque-g"])
    ys = np.linspace(float(t12[1]) + 0.012, float(mix(l5, sac, 0.55)[1]), 14)
    # Diamond: narrow at T12, wide over the lumbar belt, seats on the iliac crest.
    t = np.linspace(0.0, 1.0, len(ys))
    half = 0.042 + 0.078 * np.sin(np.clip(t, 0, 1) * np.pi) ** 0.85
    half[-1] = max(float(np.abs(p["crete-iliaque-d"][0])) * 0.72, 0.07)
    half[0] = 0.038
    right = posterior_back_grid(cloud, ys, half, n_across=12, standoff=0.0026)
    # Pull the lateral column onto the iliac crest at the bottom rows.
    for i in range(len(ys) - 3, len(ys)):
        s = (i - (len(ys) - 4)) / 3.0
        crest_pt = mix(p["eips-d"], p["crete-iliaque-d"], 0.55 + 0.35 * s)
        right[i, -1] = mix(right[i, -1], off(crest_pt, z=-0.008), 0.65)
        right[i, -2] = mix(right[i, -2], off(crest_pt, x=0.01, z=-0.006), 0.4)
    left = _mirror_x(right)
    grid = np.concatenate([left[:, :-1, :], right], axis=1)
    # Scallop the lateral free edge so it doesn’t read as a hard box.
    cols = grid.shape[1]
    for i in range(grid.shape[0]):
        for j in range(cols):
            edge = min(j, cols - 1 - j) / max(cols / 2.0, 1)
            jitter = 0.0022 * (1.0 - edge) * np.sin(i * 1.7 + j * 0.6)
            grid[i, j, 1] += jitter
            grid[i, j, 2] -= 0.0012 * (1.0 - edge) * abs(np.sin(i * 0.9))
    return grid_sheet(grid, thickness=0.0018)


def nuchal_sheet(p: dict[str, np.ndarray]) -> trimesh.Trimesh:
    """Midline sagittal sheet: nuchal line / inion → C7 spinous (ligamentum nuchae)."""
    inion = p["inion"]
    c7 = posterior_midline(float(p["c7"][1]), ywin=0.016)
    n_along, n_across = 16, 7
    grid = np.zeros((n_along, n_across, 3), dtype=np.float64)
    for i in range(n_along):
        t = i / (n_along - 1)
        y = float(inion[1] * (1.0 - t) + c7[1] * t)
        spin = posterior_midline(y, ywin=0.012)
        # Free posterior border: inion → C7, staying behind the spinous line.
        free_z = float(inion[2] * (1.0 - t) + c7[2] * t)
        # Mid-neck the sheet is deepest (fills the nuchal fossa).
        free_z = min(free_z, float(spin[2]) - 0.018 * np.sin(t * np.pi))
        if t < 0.08:
            free_z = float(inion[2])
        if t > 0.94:
            free_z = float(c7[2]) - 0.002
        ant_z = float(spin[2]) + 0.0012
        for j in range(n_across):
            s = j / (n_across - 1)
            z = ant_z * (1.0 - s) + free_z * s
            # 2–3 mm laterality so it is a sheet, not a paper-thin plane.
            x = 0.0014 * np.sin(s * np.pi) * (0.4 + 0.6 * np.sin(t * np.pi))
            yy = y + 0.001 * np.sin(s * 4.0 + t * 2.0)
            grid[i, j] = np.array([x, yy, z], dtype=np.float64)
    return grid_sheet(grid, thickness=0.0024)


def build() -> tuple[list[tuple[str, trimesh.Trimesh]], list[dict]]:
    p = fix_landmarks(load_lm())
    meshes: list[tuple[str, trimesh.Trimesh]] = []
    catalog: list[dict] = []

    def add(id_, name, latin, region, mesh):
        if mesh is None or mesh.vertices.size == 0:
            return
        meshes.append((id_, mesh))
        catalog.append(entry(id_, name, latin, region, mesh))

    thigh_cloud_d = BodyCloud(THIGH_MUSCLES, sx=-1.0)
    thigh_cloud_g = BodyCloud(THIGH_MUSCLES, sx=1.0)
    leg_cloud_d = BodyCloud(LEG_MUSCLES, sx=-1.0)
    leg_cloud_g = BodyCloud(LEG_MUSCLES, sx=1.0)

    for suf, side, sx, thigh_cloud, leg_cloud in (
        ("d", "droit", -1.0, thigh_cloud_d, leg_cloud_d),
        ("g", "gauche", 1.0, thigh_cloud_g, leg_cloud_g),
    ):
        crest = p[f"crete-iliaque-{suf}"]
        eias = p[f"eias-{suf}"]
        gt = p[f"grand-trochanter-{suf}"]
        fib = p[f"tete-fibula-{suf}"]
        lat_k = p["condyle-lat-femur-d"] if suf == "d" else np.array(
            [-p["condyle-lat-femur-d"][0], p["condyle-lat-femur-d"][1], p["condyle-lat-femur-d"][2]]
        )
        prox = mix(gt, mix(crest, eias, 0.35), 0.45)
        dist = mix(lat_k, fib, 0.22)
        thigh_cloud.clip_to_capsule(prox, dist, radius=0.088, y_pad=0.04)
        grid = wrap_limb_grid(
            thigh_cloud,
            prox,
            dist,
            sx,
            theta0=-0.55,
            theta1=1.62,
            n_len=20,
            n_th=16,
            standoff=0.0024,
        )
        add(
            f"fascia-lata-{suf}",
            f"Fascia lata {side}",
            "Fascia lata",
            "cuisse",
            grid_sheet(grid, thickness=0.0015),
        )

        mal = mix(p[f"maleole-laterale-{suf}"], p[f"maleole-mediale-{suf}"], 0.5)
        prox_leg = off(mix(fib, lat_k, 0.35), y=-0.012)
        dist_leg = off(mal, y=0.038)
        leg_cloud.clip_to_capsule(prox_leg, dist_leg, radius=0.085, y_pad=0.04)
        grid_leg = wrap_limb_grid(
            leg_cloud,
            prox_leg,
            dist_leg,
            sx,
            theta0=-0.70,
            theta1=1.85,
            n_len=18,
            n_th=15,
            standoff=0.0022,
        )
        add(
            f"fascia-crural-{suf}",
            f"Fascia crural {side}",
            "Fascia cruris",
            "jambe",
            grid_sheet(grid_leg, thickness=0.0014),
        )

    add(
        "fascia-thoracolombaire",
        "Fascia thoraco-lombaire (nappe postérieure)",
        "Fascia thoracolumbalis",
        "tronc",
        tlf_sheet(p),
    )
    add(
        "fascia-nuchal",
        "Ligament nuchal (nappe sagittale)",
        "Ligamentum nuchae",
        "cou",
        nuchal_sheet(p),
    )

    for suf, side in (("d", "droit"), ("g", "gauche")):
        sx = -1.0 if suf == "d" else 1.0
        isch = p[f"tuberosite-ischiatique-{suf}"]
        sac = off(p["sacrum"], x=sx * 0.016, y=0.012, z=-0.018)
        add(
            f"sacro-tubereux-{suf}",
            f"Ligament sacro-tubéreux {side}",
            "Ligamentum sacrotuberale",
            "bassin",
            fascicle_bundle(
                isch,
                sac,
                sag=np.array([sx * 0.004, 0.012, -0.018]),
                n_fibers=7,
                radius_end=0.0011,
                radius_mid=0.0015,
                spread_end=0.010,
                spread_mid=0.0016,
                samples=22,
                radial=7,
                rings=2,
            ),
        )
    return meshes, catalog
