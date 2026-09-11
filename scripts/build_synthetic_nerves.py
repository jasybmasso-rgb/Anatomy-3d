"""Schematic major peripheral nerve trunks (synthetic-v2), landmark-anchored.

BodyParts3D 4.0 has almost no peripheral-nerve meshes (cranial/orbital only).
These tubes are pedagogical approximations, not cadaver segmentations.

Paths follow textbook courses (cubital tunnel, spiral groove, inguinal
ligament, greater sciatic foramen, fibular neck…) using named landmarks,
with derived elbow/knee points when a bbox landmark sits on the wrong bone.
Radii are trunk-scale (thinner than v1 sausages).
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
    "Schéma pédagogique (synthetic-v2) : tube lofté le long du trajet anatomique "
    "usuel, ancré sur des repères osseux. Ce n’est pas une segmentation "
    "cadavérique. BodyParts3D 4.0 n’expose pas les nerfs périphériques "
    "(sciatique, médian, plexus, etc.)."
)

# Atlas gold-yellow, distinct from bone ivory, gland tan, muscle red, vessels.
NERVE_RGB = (246, 214, 72, 255)


def load_lm() -> dict[str, np.ndarray]:
    data = json.loads(LANDMARKS.read_text(encoding="utf-8"))
    return {item["id"]: np.array(item["position"], dtype=float) for item in data["landmarks"]}


def mirror(p: np.ndarray) -> np.ndarray:
    return np.array([-p[0], p[1], p[2]])


def mix(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    return a * (1.0 - t) + b * t


def off(p: np.ndarray, x: float = 0, y: float = 0, z: float = 0) -> np.ndarray:
    return p + np.array([x, y, z], dtype=float)


def _polyline(points: list[np.ndarray], samples: int = 9) -> np.ndarray:
    chunks: list[np.ndarray] = []
    for a, b in zip(points[:-1], points[1:]):
        mid = (a + b) / 2.0
        chord = np.linalg.norm(b - a)
        sag = np.array([0.0, 0.0, 0.0025 if chord > 0.04 else 0.0012], dtype=float)
        curve = bezier_cubic(a, mix(a, mid, 0.38) + sag, mix(b, mid, 0.38) + sag, b, samples)
        chunks.append(curve[:-1])
    chunks.append(np.asarray(points[-1], dtype=float)[None, :])
    return np.vstack(chunks)


def nerve_tube(
    points: list[np.ndarray],
    radius: float,
    *,
    samples: int = 9,
    radial: int = 12,
    taper: float = 0.82,
) -> trimesh.Trimesh:
    path = _polyline(points, samples)
    t = np.linspace(1.08, taper, len(path))
    radii = np.clip(radius * t, radius * 0.62, radius * 1.15)
    mesh = loft_tube(path, radii, radial=radial, caps=True)
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


def _near_y(a: np.ndarray, b: np.ndarray, tol: float = 0.12) -> bool:
    return abs(float(a[1] - b[1])) <= tol


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
        clav = S("clavicule-d", suf)
        hum = S("tete-humerus-d", suf)
        acrom = S("acromion-d", suf)
        ole = S("olecrane-d", suf)
        sty_r = S("styloide-radial-d", suf)
        sty_u = S("styloide-ulnaire-d", suf)

        # Elbow: olecranon is reliable; medial epicondyle bbox is at the shoulder.
        lat_raw = S("epicondyle-lat-humerus-d", suf) if suf == "d" else mirror(p["epicondyle-lat-humerus-d"])
        lat_ep = lat_raw if _near_y(lat_raw, ole, 0.08) else off(ole, x=sx * 0.032, y=0.006, z=0.004)
        med_ep = off(ole, x=-sx * 0.028, y=0.01, z=-0.012)
        cubital = off(mix(med_ep, lat_ep, 0.48), y=-0.012, z=0.022)
        mid_arm = mix(hum, ole, 0.52)

        # C5–T1 roots → trunks behind the clavicle → axilla (brachial plexus).
        root = off(mix(c7, t1, 0.4), x=sx * 0.028, z=0.006)
        scalene = off(root, x=sx * 0.018, y=-0.012, z=0.01)
        retroclav = off(clav, x=sx * 0.02, y=-0.018, z=-0.012)
        axilla = off(hum, x=sx * 0.012, y=-0.028, z=0.006)

        add(
            f"plexus-brachial-{suf}",
            f"Plexus brachial {side}",
            "Plexus brachialis",
            nerve_tube([root, scalene, retroclav, axilla], 0.0048),
            ["brachial plexus", f"plexus brachial {adj}"],
        )
        add(
            f"nerf-axillaire-{suf}",
            f"Nerf axillaire {side}",
            "Nervus axillaris",
            nerve_tube(
                [
                    axilla,
                    off(hum, x=sx * 0.008, y=-0.02, z=-0.016),
                    off(acrom, x=sx * 0.006, y=-0.018, z=0.004),
                ],
                0.0026,
            ),
            ["axillary nerve", "circonflexe"],
        )
        add(
            f"nerf-musculo-cutane-{suf}",
            f"Nerf musculo-cutané {side}",
            "Nervus musculocutaneus",
            nerve_tube(
                [
                    axilla,
                    off(mid_arm, x=sx * 0.006, z=0.018),
                    off(lat_ep, x=sx * 0.008, y=-0.03, z=0.02),
                ],
                0.0024,
            ),
            ["musculocutaneous nerve"],
        )
        # Median: medial arm with brachial a. → cubital fossa (medial to biceps) → carpal tunnel.
        carpal = mix(sty_r, sty_u, 0.48)
        add(
            f"nerf-median-{suf}",
            f"Nerf médian {side}",
            "Nervus medianus",
            nerve_tube(
                [
                    axilla,
                    off(mix(hum, ole, 0.38), x=-sx * 0.01, z=0.012),
                    cubital,
                    off(mix(cubital, carpal, 0.55), z=0.012),
                    off(carpal, z=0.01),
                ],
                0.0027,
            ),
            ["median nerve"],
        )
        # Ulnar: medial cord → cubital tunnel (behind medial epicondyle) → Guyon.
        add(
            f"nerf-ulnaire-{suf}",
            f"Nerf ulnaire {side}",
            "Nervus ulnaris",
            nerve_tube(
                [
                    axilla,
                    off(mix(hum, ole, 0.4), x=-sx * 0.016, z=-0.006),
                    off(med_ep, z=-0.014),
                    off(mix(med_ep, sty_u, 0.55), x=-sx * 0.006, z=0.004),
                    off(sty_u, z=0.008),
                ],
                0.0026,
            ),
            ["ulnar nerve", "cubital"],
        )
        # Radial: posterior cord → spiral groove → anterior to lateral epicondyle → radius.
        add(
            f"nerf-radial-{suf}",
            f"Nerf radial {side}",
            "Nervus radialis",
            nerve_tube(
                [
                    axilla,
                    off(mix(hum, ole, 0.28), z=-0.022),
                    off(mix(hum, ole, 0.58), x=sx * 0.012, z=-0.018),
                    off(lat_ep, y=-0.008, z=0.006),
                    off(sty_r, z=0.006),
                ],
                0.0026,
            ),
            ["radial nerve"],
        )

        l1 = p["l1"]
        l5 = p["l5"]
        eias = S("eias-d", suf)
        eips = S("eips-d", suf)
        isch = S("tuberosite-ischiatique-d", suf)
        hip = S("tete-femorale-d", suf)
        gt = S("grand-trochanter-d", suf)
        pat = S("patella-d", suf)
        fib = S("tete-fibula-d", suf)
        mal_m = S("maleole-mediale-d", suf)
        mal_l = S("maleole-laterale-d", suf)
        pub = p["symphyse-pubienne"]
        pub_t = p["tubercule-pubien"]
        sacrum = p["sacrum"]

        cond_m_raw = S("condyle-med-femur-d", suf) if suf == "d" else mirror(p["condyle-med-femur-d"])
        cond_m = cond_m_raw if _near_y(cond_m_raw, pat, 0.12) else off(pat, x=-sx * 0.024, z=-0.012)
        knee_post = off(mix(cond_m, off(pat, x=sx * 0.028, z=-0.02), 0.5), z=-0.034)

        # Lumbar plexus: psoas gutter L1–L4 toward inguinal ligament.
        psoas = off(mix(l1, l5, 0.45), x=sx * 0.032, z=0.012)
        inguinal = mix(eias, pub_t, 0.55)
        add(
            f"plexus-lombaire-{suf}",
            f"Plexus lombaire {side}",
            "Plexus lumbalis",
            nerve_tube(
                [
                    off(l1, x=sx * 0.018, z=0.008),
                    psoas,
                    off(inguinal, y=0.02, z=0.01),
                ],
                0.0042,
            ),
            ["lumbar plexus"],
        )
        # Femoral: under inguinal ligament (mid ASIS–pubic tubercle) → anterior thigh.
        add(
            f"nerf-femoral-{suf}",
            f"Nerf fémoral {side}",
            "Nervus femoralis",
            nerve_tube(
                [
                    off(inguinal, z=0.016),
                    off(mix(inguinal, pat, 0.42), z=0.028),
                    off(cond_m, z=0.018),
                ],
                0.003,
            ),
            ["femoral nerve"],
        )
        add(
            f"nerf-obturateur-{suf}",
            f"Nerf obturateur {side}",
            "Nervus obturatorius",
            nerve_tube(
                [
                    off(pub, x=sx * 0.022, z=0.008),
                    off(mix(pub, hip, 0.55), x=sx * 0.016, z=0.004),
                    off(mix(hip, cond_m, 0.38), x=-sx * 0.008, z=0.006),
                ],
                0.0022,
            ),
            ["obturator nerve"],
        )
        # Sciatic: greater sciatic foramen (EIPS/sacrum) → posterior ischium → popliteal split.
        sciatic_exit = off(mix(sacrum, eips, 0.55), x=sx * 0.018, y=-0.02, z=-0.028)
        add(
            f"nerf-sciatique-{suf}",
            f"Nerf sciatique {side}",
            "Nervus ischiadicus",
            nerve_tube(
                [
                    sciatic_exit,
                    off(isch, x=sx * 0.01, z=-0.032),
                    off(mix(isch, knee_post, 0.55), z=-0.036),
                    knee_post,
                ],
                0.0048,
                taper=0.78,
            ),
            ["sciatic nerve", "ischiatique"],
        )
        add(
            f"nerf-tibial-{suf}",
            f"Nerf tibial {side}",
            "Nervus tibialis",
            nerve_tube(
                [
                    knee_post,
                    off(mix(knee_post, mal_m, 0.5), z=-0.022),
                    off(mal_m, z=-0.012),
                ],
                0.0028,
            ),
            ["tibial nerve"],
        )
        # Common fibular: popliteal fossa → winds around fibular neck → lateral leg.
        add(
            f"nerf-fibulaire-{suf}",
            f"Nerf fibulaire commun {side}",
            "Nervus fibularis communis",
            nerve_tube(
                [
                    knee_post,
                    off(fib, x=sx * 0.006, y=0.006, z=-0.008),
                    off(fib, x=sx * 0.008, y=-0.01, z=0.01),
                    off(mal_l, z=0.008),
                ],
                0.0024,
            ),
            ["common peroneal", "fibular nerve", "péronier"],
        )
        add(
            f"nerf-gluteal-inf-{suf}",
            f"Nerf glutéal inférieur {side}",
            "Nervus gluteus inferior",
            nerve_tube(
                [
                    off(sciatic_exit, z=-0.006),
                    off(gt, x=sx * 0.004, z=-0.018),
                ],
                0.0022,
            ),
            ["inferior gluteal nerve"],
        )

    for suf, side, sx in (("d", "droit", -1.0), ("g", "gauche", 1.0)):
        rib1 = S("cote1-d", suf)
        add(
            f"nerf-phrenique-{suf}",
            f"Nerf phrénique {side}",
            "Nervus phrenicus",
            nerve_tube(
                [
                    off(p["c7"], x=sx * 0.016, z=0.028),
                    off(rib1, x=sx * 0.01, z=0.02),
                    off(p["manubrium"], x=sx * 0.028, z=0.018),
                    off(p["xiphoide"], x=sx * 0.036, y=-0.02, z=0.008),
                ],
                0.002,
            ),
            ["phrenic nerve"],
        )

    return meshes, catalog
