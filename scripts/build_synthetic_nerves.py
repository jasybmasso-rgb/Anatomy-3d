"""Schematic major peripheral nerve trunks (synthetic-v2), landmark-anchored.

BodyParts3D 4.0 has almost no peripheral-nerve meshes (cranial/orbital only).
These tubes are pedagogical approximations, not cadaver segmentations.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

from anatomy_fr import region_from_point
from mesh_primitives import bezier_cubic, loft_tube

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"

NOTE = (
    "Schéma pédagogique (synthetic-v2) : tube lofté entre repères osseux. "
    "Ce n’est pas une segmentation cadavérique. BodyParts3D 4.0 n’expose pas "
    "les nerfs périphériques (sciatique, médian, plexus, etc.)."
)


def load_lm() -> dict[str, np.ndarray]:
    data = json.loads(LANDMARKS.read_text(encoding="utf-8"))
    return {item["id"]: np.array(item["position"], dtype=float) for item in data["landmarks"]}


def mirror(p: np.ndarray) -> np.ndarray:
    return np.array([-p[0], p[1], p[2]])


def mix(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    return a * (1.0 - t) + b * t


def off(p: np.ndarray, x: float = 0, y: float = 0, z: float = 0) -> np.ndarray:
    return p + np.array([x, y, z], dtype=float)


def _polyline(points: list[np.ndarray], samples: int = 7) -> np.ndarray:
    chunks: list[np.ndarray] = []
    for a, b in zip(points[:-1], points[1:]):
        mid = (a + b) / 2.0
        sag = np.array([0.0, 0.0, 0.008], dtype=float)
        curve = bezier_cubic(a, mix(a, mid, 0.45) + sag, mix(b, mid, 0.45) + sag, b, samples)
        chunks.append(curve[:-1])
    chunks.append(np.asarray(points[-1], dtype=float)[None, :])
    return np.vstack(chunks)


def nerve_tube(points: list[np.ndarray], radius: float = 0.007) -> trimesh.Trimesh:
    path = _polyline(points)
    radii = np.full(len(path), radius, dtype=float)
    mesh = loft_tube(path, radii, radial=8, caps=True)
    return mesh


def _entry(part_id: str, name: str, latin: str, mesh: trimesh.Trimesh, aliases: list[str]) -> dict:
    c = mesh.vertices.mean(0)
    extents = mesh.vertices.max(0) - mesh.vertices.min(0)
    radius = float(np.linalg.norm(extents) * 0.5)
    distance = float(min(1.35, max(0.55, radius * 2.2)))
    return {
        "id": part_id,
        "name": name,
        "nameLatin": latin,
        "aliases": aliases,
        "region": region_from_point(float(c[0]), float(c[1]), float(c[2])),
        "notes": NOTE,
        "source": "synthetic-v2",
        "sourceName": part_id,
        "fmaIds": [],
        "fileIds": [],
        "centroid": [round(float(x), 5) for x in c],
        "focus": {
            "position": [round(float(x), 5) for x in c],
            "distance": round(distance, 3),
        },
        "vertexCount": int(len(mesh.vertices)),
        "faceCount": int(len(mesh.faces)),
        "kind": "nerve",
    }


def build() -> tuple[list[tuple[str, trimesh.Trimesh]], list[dict]]:
    p = load_lm()
    meshes: list[tuple[str, trimesh.Trimesh]] = []
    catalog: list[dict] = []

    def add(part_id: str, name: str, latin: str, mesh: trimesh.Trimesh, aliases: list[str]):
        if mesh is None or mesh.vertices.size == 0:
            return
        meshes.append((part_id, mesh))
        catalog.append(_entry(part_id, name, latin, mesh, aliases))

    def S(key_d: str, suf: str) -> np.ndarray:
        if suf == "d":
            return p[key_d]
        alt = key_d[:-2] + "-g" if key_d.endswith("-d") else key_d
        if alt in p:
            return p[alt]
        return mirror(p[key_d])

    for suf, side, adj in (("d", "droit", "droit"), ("g", "gauche", "gauche")):
        sx = -1.0 if suf == "d" else 1.0
        c7 = p["c7"]
        t1 = p["t1"]
        neck = mix(c7, t1, 0.35)
        plexus = off(mix(neck, S("tete-humerus-d", suf), 0.42), x=sx * 0.01, z=0.02)
        hum = S("tete-humerus-d", suf)
        acrom = S("acromion-d", suf)
        med_ep = S("epicondyle-med-humerus-d", suf) if suf == "d" else mirror(p["epicondyle-med-humerus-d"])
        lat_ep = S("epicondyle-lat-humerus-d", suf) if suf == "d" else mirror(p["epicondyle-lat-humerus-d"])
        ole = S("olecrane-d", suf)
        sty_r = S("styloide-radial-d", suf)
        sty_u = S("styloide-ulnaire-d", suf)
        mid_arm = mix(hum, mix(med_ep, lat_ep, 0.5), 0.55)
        cubital = mix(med_ep, lat_ep, 0.45)

        add(
            f"plexus-brachial-{suf}",
            f"Plexus brachial {side}",
            "Plexus brachialis",
            nerve_tube(
                [off(neck, x=sx * 0.02, z=0.01), plexus, off(hum, x=sx * 0.02, y=-0.02, z=0.01)],
                0.011,
            ),
            ["brachial plexus", f"plexus brachial {adj}"],
        )
        add(
            f"nerf-axillaire-{suf}",
            f"Nerf axillaire {side}",
            "Nervus axillaris",
            nerve_tube([plexus, off(hum, y=-0.015, z=-0.01), off(acrom, y=-0.02, z=0.01)], 0.0065),
            ["axillary nerve", "circonflexe"],
        )
        add(
            f"nerf-musculo-cutane-{suf}",
            f"Nerf musculo-cutané {side}",
            "Nervus musculocutaneus",
            nerve_tube(
                [plexus, off(mid_arm, z=0.02), off(lat_ep, x=sx * 0.01, y=-0.04, z=0.02)],
                0.006,
            ),
            ["musculocutaneous nerve"],
        )
        add(
            f"nerf-median-{suf}",
            f"Nerf médian {side}",
            "Nervus medianus",
            nerve_tube(
                [
                    plexus,
                    off(mid_arm, x=sx * -0.01, z=0.015),
                    off(cubital, z=0.02),
                    mix(sty_r, sty_u, 0.45),
                ],
                0.0068,
            ),
            ["median nerve"],
        )
        add(
            f"nerf-ulnaire-{suf}",
            f"Nerf ulnaire {side}",
            "Nervus ulnaris",
            nerve_tube(
                [
                    plexus,
                    off(mid_arm, x=sx * -0.018, z=-0.01),
                    off(med_ep, z=-0.012),
                    off(sty_u, z=0.004),
                ],
                0.0065,
            ),
            ["ulnar nerve", "cubital"],
        )
        add(
            f"nerf-radial-{suf}",
            f"Nerf radial {side}",
            "Nervus radialis",
            nerve_tube(
                [
                    plexus,
                    off(mix(hum, ole, 0.45), z=-0.02),
                    off(lat_ep, z=-0.008),
                    off(sty_r, z=0.004),
                ],
                0.0066,
            ),
            ["radial nerve"],
        )

        l1 = p["l1"]
        l5 = p["l5"]
        eias = S("eias-d", suf)
        isch = S("tuberosite-ischiatique-d", suf)
        hip = S("tete-femorale-d", suf)
        gt = S("grand-trochanter-d", suf)
        cond_m = S("condyle-med-femur-d", suf) if suf == "d" else mirror(p["condyle-med-femur-d"])
        cond_l = S("condyle-lat-femur-d", suf) if suf == "d" else mirror(p["condyle-lat-femur-d"])
        knee_post = off(mix(cond_m, cond_l, 0.5), z=-0.028)
        pat = S("patella-d", suf)
        fib = S("tete-fibula-d", suf)
        mal_m = S("maleole-mediale-d", suf)
        mal_l = S("maleole-laterale-d", suf)
        pub = p["symphyse-pubienne"]

        add(
            f"plexus-lombaire-{suf}",
            f"Plexus lombaire {side}",
            "Plexus lumbalis",
            nerve_tube([off(l1, x=sx * 0.02, z=0.01), off(mix(l1, l5, 0.5), x=sx * 0.04), off(eias, z=0.02)], 0.009),
            ["lumbar plexus"],
        )
        add(
            f"nerf-femoral-{suf}",
            f"Nerf fémoral {side}",
            "Nervus femoralis",
            nerve_tube(
                [
                    off(eias, x=sx * 0.01, z=0.03),
                    off(mix(eias, pat, 0.45), z=0.03),
                    off(cond_m, z=0.02),
                ],
                0.0075,
            ),
            ["femoral nerve"],
        )
        add(
            f"nerf-obturateur-{suf}",
            f"Nerf obturateur {side}",
            "Nervus obturatorius",
            nerve_tube(
                [off(pub, x=sx * 0.03, z=0.01), off(mix(pub, hip, 0.6), x=sx * 0.02), off(mix(hip, cond_m, 0.4), x=sx * -0.01)],
                0.0058,
            ),
            ["obturator nerve"],
        )
        add(
            f"nerf-sciatique-{suf}",
            f"Nerf sciatique {side}",
            "Nervus ischiadicus",
            nerve_tube(
                [
                    off(p["sacrum"], x=sx * 0.03, z=-0.02),
                    off(isch, z=-0.02),
                    off(mix(isch, knee_post, 0.55), z=-0.03),
                    knee_post,
                ],
                0.011,
            ),
            ["sciatic nerve", "ischiatique"],
        )
        add(
            f"nerf-tibial-{suf}",
            f"Nerf tibial {side}",
            "Nervus tibialis",
            nerve_tube([knee_post, off(mix(knee_post, mal_m, 0.5), z=-0.02), off(mal_m, z=-0.01)], 0.0065),
            ["tibial nerve"],
        )
        add(
            f"nerf-fibulaire-{suf}",
            f"Nerf fibulaire commun {side}",
            "Nervus fibularis communis",
            nerve_tube([knee_post, off(fib, z=0.01), off(mal_l, z=0.01)], 0.006),
            ["common peroneal", "fibular nerve", "péronier"],
        )
        add(
            f"nerf-gluteal-inf-{suf}",
            f"Nerf glutéal inférieur {side}",
            "Nervus gluteus inferior",
            nerve_tube([off(p["sacrum"], x=sx * 0.025, z=-0.03), off(gt, z=-0.02)], 0.006),
            ["inferior gluteal nerve"],
        )

    # Midline phrenic (paired, close to midline)
    for suf, side, sx in (("d", "droit", -1.0), ("g", "gauche", 1.0)):
        add(
            f"nerf-phrenique-{suf}",
            f"Nerf phrénique {side}",
            "Nervus phrenicus",
            nerve_tube(
                [
                    off(p["c7"], x=sx * 0.018, z=0.03),
                    off(p["manubrium"], x=sx * 0.03, z=0.04),
                    off(p["xiphoide"], x=sx * 0.04, z=0.02),
                ],
                0.0055,
            ),
            ["phrenic nerve"],
        )

    return meshes, catalog
