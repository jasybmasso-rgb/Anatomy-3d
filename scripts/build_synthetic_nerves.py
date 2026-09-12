"""Schematic major peripheral nerves (synthetic-v3), landmark-anchored.

BodyParts3D 4.0 has almost no peripheral-nerve meshes (cranial/orbital only).
These tubes are pedagogical approximations, not cadaver segmentations.

v3+: tighter foraminal exits, thinner trunks, textbook courses past key
muscles (sciatic infrapiriform, radial spiral groove, ulnar cubital tunnel,
femoral under the inguinal ligament).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anatomy_fr import region_from_point  # noqa: E402
from body_surface import (  # noqa: E402
    fix_landmarks,
    foramen,
    load_lm,
    mix,
    off,
    piriformis_underside,
    spinal_levels,
)
from mesh_primitives import bezier_cubic, loft_tube  # noqa: E402

NOTE = (
    "Schéma pédagogique (synthetic-v3) : tube lofté le long du trajet "
    "anatomique usuel, avec racines / sorties foraminales visibles. Ancré sur "
    "des repères osseux et, pour le sciatique, le corridor infrapiriforme. "
    "Ce n’est pas une segmentation cadavérique. BodyParts3D 4.0 n’expose pas "
    "les nerfs périphériques (sciatique, médian, plexus, etc.)."
)

NERVE_RGB = (246, 214, 72, 255)


def mirror(p: np.ndarray) -> np.ndarray:
    return np.array([-p[0], p[1], p[2]])


def _polyline(points: list[np.ndarray], samples: int = 10) -> np.ndarray:
    chunks: list[np.ndarray] = []
    for a, b in zip(points[:-1], points[1:]):
        mid = (a + b) / 2.0
        chord = float(np.linalg.norm(b - a))
        sag = np.array([0.0, 0.0, 0.0018 if chord > 0.04 else 0.0008], dtype=float)
        curve = bezier_cubic(a, mix(a, mid, 0.38) + sag, mix(b, mid, 0.38) + sag, b, samples)
        chunks.append(curve[:-1])
    chunks.append(np.asarray(points[-1], dtype=float)[None, :])
    return np.vstack(chunks)


def nerve_tube(
    points: list[np.ndarray],
    radius: float,
    *,
    samples: int = 10,
    radial: int = 10,
    taper: float = 0.84,
) -> trimesh.Trimesh:
    path = _polyline(points, samples)
    t = np.linspace(1.0, taper, len(path))
    radii = np.clip(radius * t, radius * 0.55, radius * 1.06)
    return loft_tube(path, radii, radial=radial, caps=True)


def merge_tubes(parts: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    mesh = trimesh.util.concatenate([p for p in parts if p is not None and p.vertices.size])
    mesh.merge_vertices()
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
        "source": "synthetic-v3+",
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


def roots_to(levels: list[np.ndarray], dest: np.ndarray, radius: float) -> list[trimesh.Trimesh]:
    tubes = []
    for src in levels:
        tubes.append(nerve_tube([src, mix(src, dest, 0.55), dest], radius, samples=8, radial=8, taper=0.9))
    return tubes


def build() -> tuple[list[tuple[str, trimesh.Trimesh]], list[dict]]:
    p = fix_landmarks(load_lm())
    lv = spinal_levels(p)
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

    for suf, side in (("d", "droit"), ("g", "gauche")):
        sx = -1.0 if suf == "d" else 1.0
        clav = S("clavicule-d", suf)
        hum = S("tete-humerus-d", suf)
        acrom = S("acromion-d", suf)
        ole = S("olecrane-d", suf)
        sty_r = S("styloide-radial-d", suf)
        sty_u = S("styloide-ulnaire-d", suf)

        lat_raw = S("epicondyle-lat-humerus-d", suf) if suf == "d" else mirror(p["epicondyle-lat-humerus-d"])
        lat_ep = lat_raw if _near_y(lat_raw, ole, 0.08) else off(ole, x=sx * 0.032, y=0.006, z=0.004)
        med_raw = p["epicondyle-med-humerus-d"] if suf == "d" else mirror(p["epicondyle-med-humerus-d"])
        med_ep = med_raw if _near_y(med_raw, ole, 0.08) else off(ole, x=-sx * 0.028, y=0.01, z=-0.012)
        cubital = off(mix(med_ep, lat_ep, 0.48), y=-0.012, z=0.018)
        mid_arm = mix(hum, ole, 0.52)

        c5 = foramen(lv["C5"], sx, "cervical")
        c6 = foramen(lv["C6"], sx, "cervical")
        c7f = foramen(lv["C7"], sx, "cervical")
        c8 = foramen(mix(lv["C7"], lv["T1"], 0.55), sx, "cervical")
        t1f = foramen(lv["T1"], sx, "thoracic")
        scalene = off(mix(c7f, t1f, 0.4), x=sx * 0.016, y=-0.008, z=0.008)
        retroclav = off(clav, x=sx * 0.018, y=-0.016, z=-0.010)
        axilla = off(hum, x=sx * 0.010, y=-0.026, z=0.004)

        add(
            f"plexus-brachial-{suf}",
            f"Plexus brachial {side}",
            "Plexus brachialis",
            merge_tubes(
                roots_to([c5, c6, c7f, c8, t1f], scalene, 0.00110)
                + [nerve_tube([scalene, retroclav, axilla], 0.0027, taper=0.88)]
            ),
            ["brachial plexus", f"plexus brachial {side}", "C5", "C6", "C7", "C8", "T1"],
        )
        add(
            f"nerf-axillaire-{suf}",
            f"Nerf axillaire {side}",
            "Nervus axillaris",
            nerve_tube(
                [
                    axilla,
                    off(hum, x=sx * 0.006, y=-0.018, z=-0.014),
                    off(acrom, x=sx * 0.004, y=-0.016, z=0.002),
                ],
                0.00155,
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
                    off(mid_arm, x=sx * 0.005, z=0.016),
                    off(lat_ep, x=sx * 0.006, y=-0.028, z=0.016),
                ],
                0.00145,
            ),
            ["musculocutaneous nerve"],
        )
        carpal = mix(sty_r, sty_u, 0.48)
        add(
            f"nerf-median-{suf}",
            f"Nerf médian {side}",
            "Nervus medianus",
            nerve_tube(
                [
                    axilla,
                    off(mix(hum, ole, 0.38), x=-sx * 0.006, z=0.012),
                    cubital,
                    off(mix(cubital, carpal, 0.55), z=0.012),
                    off(carpal, z=0.009),
                ],
                0.00160,
            ),
            ["median nerve"],
        )
        add(
            f"nerf-ulnaire-{suf}",
            f"Nerf ulnaire {side}",
            "Nervus ulnaris",
            nerve_tube(
                [
                    axilla,
                    off(mix(hum, ole, 0.4), x=-sx * 0.016, z=-0.008),
                    off(med_ep, y=0.004, z=-0.016),
                    off(med_ep, y=-0.008, z=-0.010),
                    off(mix(med_ep, sty_u, 0.55), x=-sx * 0.005, z=0.003),
                    off(sty_u, z=0.006),
                ],
                0.00150,
            ),
            ["ulnar nerve", "cubital"],
        )
        add(
            f"nerf-radial-{suf}",
            f"Nerf radial {side}",
            "Nervus radialis",
            nerve_tube(
                [
                    axilla,
                    off(mix(hum, ole, 0.22), z=-0.026),
                    off(mix(hum, ole, 0.48), x=sx * 0.012, z=-0.022),
                    off(mix(hum, ole, 0.68), x=sx * 0.010, z=-0.008),
                    off(lat_ep, y=-0.006, z=0.005),
                    off(sty_r, z=0.005),
                ],
                0.00150,
            ),
            ["radial nerve"],
        )

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
        knee_post = off(mix(cond_m, off(pat, x=sx * 0.028, z=-0.02), 0.5), z=-0.032)

        l2 = foramen(lv["L2"], sx, "lumbar")
        l3 = foramen(lv["L3"], sx, "lumbar")
        l4 = foramen(lv["L4"], sx, "lumbar")
        l5f = foramen(lv["L5"], sx, "lumbar")
        s1 = foramen(lv["S1"], sx, "sacral")
        s2 = foramen(lv["S2"], sx, "sacral")
        s3 = foramen(lv["S3"], sx, "sacral")
        psoas = off(mix(lv["L2"], lv["L4"], 0.5), x=sx * 0.030, z=0.010)
        inguinal = mix(eias, pub_t, 0.55)

        add(
            f"plexus-lombaire-{suf}",
            f"Plexus lombaire {side}",
            "Plexus lumbalis",
            merge_tubes(
                roots_to([l2, l3, l4], psoas, 0.00105)
                + [nerve_tube([psoas, off(inguinal, y=0.018, z=0.008)], 0.0022, taper=0.86)]
            ),
            ["lumbar plexus", "L1", "L2", "L3", "L4"],
        )
        add(
            f"nerf-femoral-{suf}",
            f"Nerf fémoral {side}",
            "Nervus femoralis",
            merge_tubes(
                roots_to([l2, l3, l4], off(inguinal, y=-0.002, z=0.012), 0.00100)
                + [
                    nerve_tube(
                        [
                            off(inguinal, y=-0.002, z=0.012),
                            off(mix(inguinal, pat, 0.42), z=0.022),
                            off(cond_m, z=0.016),
                        ],
                        0.00175,
                    )
                ]
            ),
            ["femoral nerve"],
        )
        add(
            f"nerf-obturateur-{suf}",
            f"Nerf obturateur {side}",
            "Nervus obturatorius",
            merge_tubes(
                roots_to([l2, l3, l4], off(pub, x=sx * 0.020, z=0.006), 0.00095)
                + [
                    nerve_tube(
                        [
                            off(pub, x=sx * 0.020, z=0.006),
                            off(mix(pub, hip, 0.55), x=sx * 0.014, z=0.002),
                            off(mix(hip, cond_m, 0.38), x=-sx * 0.006, z=0.004),
                        ],
                        0.00140,
                    )
                ]
            ),
            ["obturator nerve"],
        )

        # Sciatic: L4–S3 roots → greater sciatic foramen INFERIOR to piriformis
        # → between ischium and GT (closer to ischium) → posterior thigh → popliteal split.
        under_pir = piriformis_underside(sx)
        # Posterior greater-sciatic notch, then INFERIOR to piriformis (not through the belly).
        behind = off(mix(sacrum, eips, 0.22), x=sx * 0.032, y=-0.006, z=-0.042)
        gsf = off(mix(sacrum, eips, 0.38), x=sx * 0.026, y=-0.048, z=-0.034)
        deep_glute = off(mix(isch, gt, 0.28), z=-0.034, y=-0.006)
        mid_thigh = off(mix(isch, knee_post, 0.48), z=-0.032, x=sx * 0.006)
        sacral_plexus = off(mix(s1, s2, 0.5), x=sx * 0.016, y=-0.004, z=-0.012)
        add(
            f"nerf-sciatique-{suf}",
            f"Nerf sciatique {side}",
            "Nervus ischiadicus",
            merge_tubes(
                roots_to([l4, l5f, s1, s2, s3], sacral_plexus, 0.00110)
                + [
                    nerve_tube(
                        [sacral_plexus, behind, gsf, under_pir, deep_glute, mid_thigh, knee_post],
                        0.00245,
                        samples=14,
                        taper=0.78,
                    )
                ]
            ),
            ["sciatic nerve", "ischiatique", "L4", "L5", "S1", "S2", "S3", "piriforme"],
        )
        add(
            f"nerf-tibial-{suf}",
            f"Nerf tibial {side}",
            "Nervus tibialis",
            nerve_tube(
                [
                    knee_post,
                    off(mix(knee_post, mal_m, 0.5), z=-0.020),
                    off(mal_m, z=-0.010),
                ],
                0.00160,
            ),
            ["tibial nerve"],
        )
        add(
            f"nerf-fibulaire-{suf}",
            f"Nerf fibulaire commun {side}",
            "Nervus fibularis communis",
            nerve_tube(
                [
                    knee_post,
                    off(fib, x=sx * 0.005, y=0.004, z=-0.008),
                    off(fib, x=sx * 0.007, y=-0.010, z=0.008),
                    off(mal_l, z=0.006),
                ],
                0.00145,
            ),
            ["common peroneal", "fibular nerve", "péronier"],
        )
        add(
            f"nerf-gluteal-inf-{suf}",
            f"Nerf glutéal inférieur {side}",
            "Nervus gluteus inferior",
            nerve_tube(
                [
                    under_pir,
                    off(gt, x=sx * 0.004, z=-0.016),
                ],
                0.00130,
            ),
            ["inferior gluteal nerve"],
        )

    for suf, side, sx in (("d", "droit", -1.0), ("g", "gauche", 1.0)):
        rib1 = S("cote1-d", suf)
        c3 = foramen(lv["C3"], sx, "cervical")
        c4 = foramen(lv["C4"], sx, "cervical")
        add(
            f"nerf-phrenique-{suf}",
            f"Nerf phrénique {side}",
            "Nervus phrenicus",
            merge_tubes(
                roots_to([c3, c4], off(p["c7"], x=sx * 0.014, z=0.024), 0.00090)
                + [
                    nerve_tube(
                        [
                            off(p["c7"], x=sx * 0.014, z=0.024),
                            off(rib1, x=sx * 0.008, z=0.016),
                            off(p["manubrium"], x=sx * 0.024, z=0.016),
                            off(p["xiphoide"], x=sx * 0.032, y=-0.018, z=0.006),
                        ],
                        0.00120,
                    )
                ]
            ),
            ["phrenic nerve"],
        )

    return meshes, catalog
