"""Schematic major-joint ligaments: multi-fiber lofted ribbons (synthetic-v2).

Not cadaver meshes. Landmark-anchored, labeled source=synthetic-v2.
Spine sticks and menisci are omitted on purpose (quality > quantity).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

from mesh_primitives import fiber_bundle, torus_ring

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"

NOTE = (
    "Schéma pédagogique (synthetic-v2) : faisceau de rubans loftés entre repères "
    "osseux vérifiés. Ce n’est pas une segmentation cadavérique."
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


def entry(id_: str, name: str, latin: str, region: str, joint: str, mesh: trimesh.Trimesh) -> dict:
    return {
        "id": id_,
        "name": name,
        "nameLatin": latin,
        "region": region,
        "joint": joint,
        "notes": NOTE,
        "source": "synthetic-v2",
        "sourceName": id_,
        "fmaId": "",
        "fileIds": [],
        "centroid": [round(float(x), 5) for x in mesh.vertices.mean(0)],
    }


def build() -> tuple[list[tuple[str, trimesh.Trimesh]], list[dict]]:
    p = load_lm()
    meshes: list[tuple[str, trimesh.Trimesh]] = []
    catalog: list[dict] = []

    def add(id_, name, latin, region, joint, mesh):
        if mesh is None or mesh.vertices.size == 0:
            return
        meshes.append((id_, mesh))
        catalog.append(entry(id_, name, latin, region, joint, mesh))

    def bundle(id_, name, latin, region, joint, a, b, **kw):
        add(id_, name, latin, region, joint, fiber_bundle(a, b, **kw))

    def S(key: str, suf: str) -> np.ndarray:
        if key in p:
            return p[key]
        if suf == "g" and key.endswith("-g"):
            right = key[:-2] + "-d"
            if right in p:
                return mirror(p[right])
        raise KeyError(key)

    for suf, side in (("d", "droit"), ("g", "gauche")):
        sx = -1.0 if suf == "d" else 1.0
        lat_f = S("condyle-lat-femur-d", suf) if suf == "d" else mirror(p["condyle-lat-femur-d"])
        med_f = S("condyle-med-femur-d", suf) if suf == "d" else mirror(p["condyle-med-femur-d"])
        pat = p[f"patella-{suf}"]
        tub = p[f"tuberosite-tibiale-{suf}"]
        fib = p[f"tete-fibula-{suf}"]
        tibia_ant = mix(tub, pat, 0.22)
        tibia_post = off(mix(tub, pat, 0.38), z=-0.038)
        acl_from = off(mix(lat_f, med_f, 0.32), z=-0.004)
        pcl_from = off(mix(med_f, lat_f, 0.28), z=-0.012)

        bundle(
            f"lca-{suf}", f"LCA {side}", "Ligamentum cruciatum anterius", "genou", "genou",
            acl_from, off(tibia_ant, x=sx * 0.004, z=0.006),
            sag=[0, -0.008, -0.012], width=0.011, thickness=0.0028, n_fibers=5, spread=0.0045,
        )
        bundle(
            f"lcp-{suf}", f"LCP {side}", "Ligamentum cruciatum posterius", "genou", "genou",
            pcl_from, tibia_post,
            sag=[0, -0.006, 0.01], width=0.012, thickness=0.003, n_fibers=5, spread=0.005,
        )
        bundle(
            f"llim-{suf}", f"LLI {side}", "Ligamentum collaterale tibiale", "genou", "genou",
            med_f, off(tub, x=sx * -0.018, y=0.015),
            sag=[sx * -0.006, 0.0, 0.004], width=0.014, thickness=0.0032, n_fibers=6, spread=0.006,
        )
        bundle(
            f"lle-{suf}", f"LLE {side}", "Ligamentum collaterale fibulare", "genou", "genou",
            lat_f, fib,
            sag=[sx * 0.008, 0.0, 0.0], width=0.009, thickness=0.0026, n_fibers=4, spread=0.0035,
        )
        bundle(
            f"patellaire-{suf}", f"Ligament patellaire {side}", "Ligamentum patellae", "genou", "genou",
            pat, tub,
            sag=[0, 0, 0.006], width=0.018, thickness=0.0034, n_fibers=5, spread=0.007,
        )

        eias = p[f"eias-{suf}"]
        eiia = p[f"eiia-{suf}"]
        isch = p[f"tuberosite-ischiatique-{suf}"]
        head = p[f"tete-femorale-{suf}"]
        gt = p[f"grand-trochanter-{suf}"]
        pub = p["tubercule-pubien"]
        cox = p[f"os-coxal-{suf}"]
        # Iliofemoral Y (Bertin): two bands from AIIS region.
        bundle(
            f"ilio-femoral-sup-{suf}", f"Ilio-fémoral supérieur {side}",
            "Ligamentum iliofemorale (pars transversa)", "hanche", "hanche",
            mix(eias, eiia, 0.25), mix(head, gt, 0.55),
            sag=[0, 0.01, 0.008], width=0.016, thickness=0.0034, n_fibers=6, spread=0.007,
        )
        bundle(
            f"ilio-femoral-inf-{suf}", f"Ilio-fémoral inférieur {side}",
            "Ligamentum iliofemorale (pars descendens)", "hanche", "hanche",
            mix(eias, eiia, 0.45), off(mix(head, gt, 0.35), y=-0.02),
            sag=[0, -0.012, 0.006], width=0.014, thickness=0.0032, n_fibers=5, spread=0.006,
        )
        bundle(
            f"pubo-femoral-{suf}", f"Pubo-fémoral {side}", "Ligamentum pubofemorale", "hanche", "hanche",
            mix(pub, cox, 0.42), off(head, y=-0.025, z=0.01),
            sag=[0, -0.01, 0.008], width=0.011, thickness=0.0028, n_fibers=4, spread=0.005,
        )
        bundle(
            f"ischio-femoral-{suf}", f"Ischio-fémoral {side}", "Ligamentum ischiofemorale", "hanche", "hanche",
            isch, off(gt, z=-0.025),
            sag=[0, 0.008, -0.012], width=0.012, thickness=0.003, n_fibers=5, spread=0.0055,
        )

        acr = p[f"acromion-{suf}"]
        scap = p[f"scapula-{suf}"]
        clav_acr = p[f"extremite-acromiale-clavicule-{suf}"]
        clav_st = p[f"extremite-sternale-clavicule-{suf}"]
        hum = p[f"tete-humerus-{suf}"]
        cor = off(mix(mix(scap, acr, 0.45), clav_acr, 0.25), z=0.022, y=-0.008)
        glen = mix(scap, acr, 0.62)
        bundle(
            f"gleno-hum-{suf}", f"Complexe gléno-huméral {side}",
            "Ligamenta glenohumeralia", "épaule", "épaule",
            glen, hum,
            sag=[0, -0.006, 0.004], width=0.016, thickness=0.0026, n_fibers=7, spread=0.009,
        )
        bundle(
            f"coraco-humeral-{suf}", f"Coraco-huméral {side}",
            "Ligamentum coracohumerale", "épaule", "épaule",
            cor, off(hum, y=0.012),
            sag=[0, 0.008, 0.004], width=0.01, thickness=0.0026, n_fibers=4, spread=0.004,
        )
        bundle(
            f"coraco-acromial-{suf}", f"Coraco-acromial {side}",
            "Ligamentum coracoacromiale", "épaule", "épaule",
            cor, acr,
            sag=[0, 0.006, 0.01], width=0.012, thickness=0.0028, n_fibers=4, spread=0.005,
        )
        bundle(
            f"acromio-clav-{suf}", f"Acromio-claviculaire {side}",
            "Ligamentum acromioclaviculare", "épaule", "épaule",
            clav_acr, acr,
            sag=[0, 0.004, 0.003], width=0.01, thickness=0.0028, n_fibers=4, spread=0.004,
        )
        bundle(
            f"coraco-clav-{suf}", f"Coraco-claviculaire {side}",
            "Ligamenta trapezoidum et conoideum", "épaule", "épaule",
            mix(clav_acr, clav_st, 0.2), cor,
            sag=[0, -0.006, 0.0], width=0.011, thickness=0.0026, n_fibers=5, spread=0.005,
        )

        ole = p[f"olecrane-{suf}"]
        sty_u = p[f"styloide-ulnaire-{suf}"]
        sty_r = p[f"styloide-radial-{suf}"]
        epi_m = p["epicondyle-med-humerus-d"] if suf == "d" else mirror(p["epicondyle-med-humerus-d"])
        epi_l = p["epicondyle-lat-humerus-d"] if suf == "d" else mirror(p["epicondyle-lat-humerus-d"])
        ulna_prox = mix(ole, sty_u, 0.11)
        rad_head = mix(ole, sty_r, 0.13)
        bundle(
            f"lliu-{suf}", f"LCU {side}", "Ligamentum collaterale ulnare", "coude", "coude",
            epi_m, ulna_prox,
            sag=[sx * -0.004, -0.004, 0.003], width=0.01, thickness=0.0026, n_fibers=5, spread=0.0045,
        )
        bundle(
            f"llir-{suf}", f"LCR {side}", "Ligamentum collaterale radiale", "coude", "coude",
            epi_l, mix(rad_head, ole, 0.25),
            sag=[sx * 0.004, -0.003, 0.002], width=0.008, thickness=0.0024, n_fibers=4, spread=0.0035,
        )
        axis = sty_r - ole
        add(
            f"annulaire-radius-{suf}",
            f"Annulaire du radius {side}",
            "Ligamentum anulare radii",
            "coude",
            "coude",
            torus_ring(rad_head, axis, major=0.013, minor=0.0026, major_sec=28, minor_sec=8),
        )

        mal_l = p[f"maleole-laterale-{suf}"]
        mal_m = p[f"maleole-mediale-{suf}"]
        tal = p[f"talus-{suf}"]
        cal = p[f"calcaneus-{suf}"]
        bundle(
            f"lfta-{suf}", f"LTFA {side}", "Ligamentum talofibulare anterius", "cheville", "cheville",
            mal_l, off(tal, z=0.018, y=0.004),
            sag=[0, -0.004, 0.006], width=0.008, thickness=0.0022, n_fibers=4, spread=0.0032,
        )
        bundle(
            f"lfcal-{suf}", f"LCF {side}", "Ligamentum calcaneofibulare", "cheville", "cheville",
            mal_l, cal,
            sag=[sx * 0.006, -0.006, 0.0], width=0.008, thickness=0.0022, n_fibers=4, spread=0.003,
        )
        bundle(
            f"lftp-{suf}", f"LTFP {side}", "Ligamentum talofibulare posterius", "cheville", "cheville",
            mal_l, off(tal, z=-0.016),
            sag=[0, -0.003, -0.005], width=0.008, thickness=0.0022, n_fibers=4, spread=0.003,
        )
        bundle(
            f"deltoide-{suf}", f"Ligament deltoïde {side}", "Ligamentum deltoideum", "cheville", "cheville",
            mal_m, mix(off(tal, z=0.012), cal, 0.35),
            sag=[sx * -0.004, -0.005, 0.004], width=0.013, thickness=0.0028, n_fibers=6, spread=0.006,
        )

    return meshes, catalog
