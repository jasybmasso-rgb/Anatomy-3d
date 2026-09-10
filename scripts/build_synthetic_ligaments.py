"""Educational synthetic ligaments anchored on landmarks.json."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

from mesh_primitives import band, disc

ROOT = Path(__file__).resolve().parents[1]
LANDMARKS = ROOT / "src" / "data" / "landmarks.json"

NOTE = (
    "Approximation pédagogique : bande synthétique ancrée sur les repères v1 "
    "(centroïdes / extrema). Pas un scan. Source: synthetic."
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

    def add(id_, name, latin, region, joint, mesh, radius=None):
        if mesh is None or mesh.vertices.size == 0:
            return
        meshes.append(mesh)
        catalog.append(entry(id_, name, latin, region, joint, mesh))

    def capsule(id_, name, latin, region, joint, a, b, r):
        add(id_, name, latin, region, joint, band(a, b, r * 1.75))

    # --- Knee ---
    for side, suf, flip in (("droit", "d", False), ("gauche", "g", True)):
        def S(key: str) -> np.ndarray:
            if key in p:
                return p[key] if not flip or key.endswith("-g") or key.endswith(f"-{suf}") else p[key]
            # left condyles / epicondyles: mirror right
            right_key = key.replace("-g", "-d") if key.endswith("-g") else key
            if flip and right_key in p:
                return mirror(p[right_key])
            return p[key]

        lat_f = S("condyle-lat-femur-d") if suf == "d" else mirror(p["condyle-lat-femur-d"])
        med_f = S("condyle-med-femur-d") if suf == "d" else mirror(p["condyle-med-femur-d"])
        pat = p[f"patella-{suf}"]
        tub = p[f"tuberosite-tibiale-{suf}"]
        fib = p[f"tete-fibula-{suf}"]
        tibia_ant = mix(tub, pat, 0.25)
        tibia_post = off(mix(tub, pat, 0.4), z=-0.035)
        acl_from = mix(lat_f, med_f, 0.35)
        pcl_from = mix(med_f, lat_f, 0.35)

        capsule(f"lca-{suf}", f"LCA {side}", "Ligamentum cruciatum anterius", "genou", "genou",
                off(acl_from, z=0.01), off(tibia_ant, z=0.01), 0.004)
        capsule(f"lcp-{suf}", f"LCP {side}", "Ligamentum cruciatum posterius", "genou", "genou",
                off(pcl_from, z=-0.01), tibia_post, 0.004)
        capsule(f"llim-{suf}", f"LLI {side}", "Ligamentum collaterale tibiale", "genou", "genou",
                med_f, off(tub, x=(-0.02 if suf == "d" else 0.02), y=0.02), 0.005)
        capsule(f"lle-{suf}", f"LLE {side}", "Ligamentum collaterale fibulare", "genou", "genou",
                lat_f, fib, 0.0045)
        capsule(f"patellaire-{suf}", f"Ligament patellaire {side}", "Ligamentum patellae", "genou", "genou",
                pat, tub, 0.006)
        men_c = mix(mix(lat_f, med_f, 0.5), tub, 0.35)
        add(f"menisque-med-{suf}", f"Ménisque médial {side}", "Meniscus medialis", "genou", "genou",
            disc(off(men_c, x=(-0.012 if suf == "d" else 0.012)), [0, 1, 0.15], 0.02, 0.005))
        add(f"menisque-lat-{suf}", f"Ménisque latéral {side}", "Meniscus lateralis", "genou", "genou",
            disc(off(men_c, x=(0.012 if suf == "d" else -0.012)), [0, 1, 0.15], 0.018, 0.005))

    # --- Hip ---
    for suf, side in (("d", "droit"), ("g", "gauche")):
        eias = p[f"eias-{suf}"]
        eiia = p[f"eiia-{suf}"]
        isch = p[f"tuberosite-ischiatique-{suf}"]
        head = p[f"tete-femorale-{suf}"]
        gt = p[f"grand-trochanter-{suf}"]
        pub = p["tubercule-pubien"]
        cox = p[f"os-coxal-{suf}"]
        capsule(f"ilio-femoral-{suf}", f"Ligament ilio-fémoral {side}", "Ligamentum iliofemorale",
                "hanche", "hanche", mix(eias, eiia, 0.35), mix(head, gt, 0.45), 0.007)
        capsule(f"pubo-femoral-{suf}", f"Ligament pubo-fémoral {side}", "Ligamentum pubofemorale",
                "hanche", "hanche", mix(pub, cox, 0.4), off(head, y=-0.02), 0.0055)
        capsule(f"ischio-femoral-{suf}", f"Ligament ischio-fémoral {side}", "Ligamentum ischiofemorale",
                "hanche", "hanche", isch, off(gt, z=-0.02), 0.0055)
        capsule(f"tete-femur-{suf}", f"Ligament de la tête fémorale {side}", "Ligamentum capitis femoris",
                "hanche", "hanche", mix(cox, pub, 0.25), head, 0.0035)

    # --- Shoulder ---
    for suf, side in (("d", "droit"), ("g", "gauche")):
        acr = p[f"acromion-{suf}"]
        scap = p[f"scapula-{suf}"]
        clav_acr = p[f"extremite-acromiale-clavicule-{suf}"]
        clav_st = p[f"extremite-sternale-clavicule-{suf}"]
        hum = p[f"tete-humerus-{suf}"]
        cor = mix(mix(scap, acr, 0.45), clav_acr, 0.25)
        cor = off(cor, z=0.025, y=-0.01)
        capsule(f"gleno-hum-sup-{suf}", f"Ligament gléno-huméral supérieur {side}",
                "Ligamentum glenohumerale superius", "épaule", "épaule",
                mix(scap, acr, 0.55), off(hum, y=0.012), 0.0035)
        capsule(f"gleno-hum-moy-{suf}", f"Ligament gléno-huméral moyen {side}",
                "Ligamentum glenohumerale medium", "épaule", "épaule",
                scap, hum, 0.0035)
        capsule(f"gleno-hum-inf-{suf}", f"Ligament gléno-huméral inférieur {side}",
                "Ligamentum glenohumerale inferius", "épaule", "épaule",
                off(scap, y=-0.02), off(hum, y=-0.012), 0.0035)
        capsule(f"coraco-humeral-{suf}", f"Ligament coraco-huméral {side}",
                "Ligamentum coracohumerale", "épaule", "épaule", cor, off(hum, y=0.01), 0.004)
        capsule(f"coraco-acromial-{suf}", f"Ligament coraco-acromial {side}",
                "Ligamentum coracoacromiale", "épaule", "épaule", cor, acr, 0.004)
        capsule(f"acromio-clav-{suf}", f"Ligament acromio-claviculaire {side}",
                "Ligamentum acromioclaviculare", "épaule", "épaule", clav_acr, acr, 0.004)
        capsule(f"trapezoide-{suf}", f"Ligament trapézoïde {side}",
                "Ligamentum trapezoideum", "épaule", "épaule", mix(clav_acr, clav_st, 0.15), cor, 0.0035)
        capsule(f"conoide-{suf}", f"Ligament conoïde {side}",
                "Ligamentum conoideum", "épaule", "épaule", mix(clav_acr, clav_st, 0.28), cor, 0.0035)

    # --- Elbow ---
    for suf, side in (("d", "droit"), ("g", "gauche")):
        ole = p[f"olecrane-{suf}"]
        sty_u = p[f"styloide-ulnaire-{suf}"]
        sty_r = p[f"styloide-radial-{suf}"]
        if suf == "d":
            epi_m = p["epicondyle-med-humerus-d"]
            epi_l = p["epicondyle-lat-humerus-d"]
        else:
            epi_m = mirror(p["epicondyle-med-humerus-d"])
            epi_l = mirror(p["epicondyle-lat-humerus-d"])
        ulna_prox = mix(ole, sty_u, 0.12)
        rad_head = mix(ole, sty_r, 0.14)
        capsule(f"lliu-{suf}", f"LCU {side}", "Ligamentum collaterale ulnare",
                "coude", "coude", epi_m, ulna_prox, 0.004)
        capsule(f"llir-{suf}", f"LCR {side}", "Ligamentum collaterale radiale",
                "coude", "coude", epi_l, rad_head, 0.0038)
        add(f"annulaire-radius-{suf}", f"Ligament annulaire du radius {side}",
            "Ligamentum anulare radii", "coude", "coude",
            disc(rad_head, sty_r - ole, 0.012, 0.004))

    # --- Ankle ---
    for suf, side in (("d", "droit"), ("g", "gauche")):
        mal_l = p[f"maleole-laterale-{suf}"]
        mal_m = p[f"maleole-mediale-{suf}"]
        tal = p[f"talus-{suf}"]
        cal = p[f"calcaneus-{suf}"]
        capsule(f"lfta-{suf}", f"LTFA {side}", "Ligamentum talofibulare anterius",
                "cheville", "cheville", mal_l, off(tal, z=0.02), 0.0032)
        capsule(f"lfcal-{suf}", f"LCF {side}", "Ligamentum calcaneofibulare",
                "cheville", "cheville", mal_l, cal, 0.0032)
        capsule(f"lftp-{suf}", f"LTFP {side}", "Ligamentum talofibulare posterius",
                "cheville", "cheville", mal_l, off(tal, z=-0.015), 0.0032)
        capsule(f"deltoide-ant-{suf}", f"Deltoïde antérieur {side}", "Pars tibionavicularis lig. deltoidei",
                "cheville", "cheville", mal_m, off(tal, z=0.018), 0.0034)
        capsule(f"deltoide-cal-{suf}", f"Deltoïde calcanéen {side}", "Pars tibiocalcanea lig. deltoidei",
                "cheville", "cheville", mal_m, cal, 0.0034)

    # --- Spine ---
    chain = [p["c2"], p["c7"], p["t1"], p["t12"], p["l1"], p["l5"], p["sacrum"]]
    for i in range(len(chain) - 1):
        a, b = chain[i], chain[i + 1]
        capsule(f"all-{i}", f"Ligament longitudinal antérieur ({i + 1})",
                "Ligamentum longitudinale anterius", "rachis", "rachis",
                off(a, z=0.018), off(b, z=0.018), 0.003)
        capsule(f"pll-{i}", f"Ligament longitudinal postérieur ({i + 1})",
                "Ligamentum longitudinale posterius", "rachis", "rachis",
                off(a, z=-0.012), off(b, z=-0.012), 0.0026)
        capsule(f"flavum-{i}", f"Ligament jaune ({i + 1})",
                "Ligamentum flavum", "rachis", "rachis",
                off(a, z=-0.02), off(b, z=-0.02), 0.0024)
        capsule(f"interepineux-{i}", f"Ligament inter-épineux ({i + 1})",
                "Ligamentum interspinale", "rachis", "rachis",
                off(a, z=-0.028), off(b, z=-0.028), 0.0022)
    capsule("supraepineux", "Ligament supra-épineux", "Ligamentum supraspinale",
            "rachis", "rachis", off(p["c7"], z=-0.03), off(p["l5"], z=-0.03), 0.003)

    return meshes, catalog
