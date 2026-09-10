#!/usr/bin/env python3
"""Merge BodyParts3D ligament / deep connective meshes into ligaments.glb.

Uses the same world transform as skeleton.glb (see skeleton.meta.json).
Source: BodyParts3D / Anatomography (DBCLS), CC BY-SA 2.1 Japan.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from trimesh.exchange.gltf import export_glb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_skeleton_glb as sk
from build_synthetic_ligaments import build as build_synthetic

OUT_GLB = sk.ROOT / "public" / "models" / "ligaments.glb"
OUT_META = sk.ROOT / "public" / "models" / "ligaments.meta.json"
OUT_CATALOG = sk.ROOT / "src" / "data" / "ligaments.json"
SKELETON_META = sk.ROOT / "public" / "models" / "skeleton.meta.json"

# Exact English names from isa_parts_list_e.txt.
# BodyParts3D has no cruciate / collateral / iliofemoral / glenohumeral meshes;
# those are synthesized in build_synthetic_ligaments.py and merged below.
INCLUDE: dict[str, dict[str, str]] = {
    "right long plantar ligament": {
        "id": "plantaire-long-d",
        "name": "Ligament plantaire long droit",
        "nameLatin": "Ligamentum plantare longum dextrum",
        "region": "pied",
        "joint": "pied",
        "notes": "Ligament plantaire profond.",
    },
    "left long plantar ligament": {
        "id": "plantaire-long-g",
        "name": "Ligament plantaire long gauche",
        "nameLatin": "Ligamentum plantare longum sinistrum",
        "region": "pied",
        "joint": "pied",
        "notes": "Ligament plantaire profond.",
    },
    "right stylohyoid ligament": {
        "id": "stylo-hyoidien-d",
        "name": "Ligament stylo-hyoïdien droit",
        "nameLatin": "Ligamentum stylohyoideum dextrum",
        "region": "cou",
        "joint": "hyoïde",
        "notes": "Relie le processus styloïde à l’os hyoïde.",
    },
    "left stylohyoid ligament": {
        "id": "stylo-hyoidien-g",
        "name": "Ligament stylo-hyoïdien gauche",
        "nameLatin": "Ligamentum stylohyoideum sinistrum",
        "region": "cou",
        "joint": "hyoïde",
        "notes": "Relie le processus styloïde à l’os hyoïde.",
    },
    "right lateral thyrohyoid ligament": {
        "id": "thyro-hyoidien-lat-d",
        "name": "Ligament thyro-hyoïdien latéral droit",
        "nameLatin": "Ligamentum thyrohyoideum laterale dextrum",
        "region": "cou",
        "joint": "larynx",
        "notes": "Ligament extrinsèque du larynx.",
    },
    "left lateral thyrohyoid ligament": {
        "id": "thyro-hyoidien-lat-g",
        "name": "Ligament thyro-hyoïdien latéral gauche",
        "nameLatin": "Ligamentum thyrohyoideum laterale sinistrum",
        "region": "cou",
        "joint": "larynx",
        "notes": "Ligament extrinsèque du larynx.",
    },
    "median thyrohyoid ligament": {
        "id": "thyro-hyoidien-med",
        "name": "Ligament thyro-hyoïdien médian",
        "nameLatin": "Ligamentum thyrohyoideum medianum",
        "region": "cou",
        "joint": "larynx",
        "notes": "Ligament extrinsèque du larynx.",
    },
    "hyo-epiglottic ligament": {
        "id": "hyo-epiglottique",
        "name": "Ligament hyo-épiglottique",
        "nameLatin": "Ligamentum hyoepiglotticum",
        "region": "cou",
        "joint": "larynx",
        "notes": "Ligament intrinsèque / épiglotte.",
    },
    "thyro-epiglottic ligament": {
        "id": "thyro-epiglottique",
        "name": "Ligament thyro-épiglottique",
        "nameLatin": "Ligamentum thyroepiglotticum",
        "region": "cou",
        "joint": "larynx",
        "notes": "Ligament intrinsèque du larynx.",
    },
    "median cricothyroid ligament": {
        "id": "crico-thyroidien-med",
        "name": "Ligament crico-thyroïdien médian",
        "nameLatin": "Ligamentum cricothyroideum medianum",
        "region": "cou",
        "joint": "larynx",
        "notes": "Membrane crico-thyroïdienne (partie médiane).",
    },
    "right vocal ligament": {
        "id": "vocal-d",
        "name": "Ligament vocal droit",
        "nameLatin": "Ligamentum vocale dextrum",
        "region": "cou",
        "joint": "larynx",
        "notes": "Pli vocal — inclus comme ligament du larynx.",
    },
    "left vocal ligament": {
        "id": "vocal-g",
        "name": "Ligament vocal gauche",
        "nameLatin": "Ligamentum vocale sinistrum",
        "region": "cou",
        "joint": "larynx",
        "notes": "Pli vocal — inclus comme ligament du larynx.",
    },
    "interosseous membrane of right forearm": {
        "id": "membrane-interosseuse-avant-bras-d",
        "name": "Membrane interosseuse de l’avant-bras D",
        "nameLatin": "Membrana interossea antebrachii dextra",
        "region": "avant-bras",
        "joint": "syndesmose radio-ulnaire",
        "notes": "Syndesmose — tissu fibreux profond, inclus comme couche ligamentaire.",
    },
    "interosseous membrane of left forearm": {
        "id": "membrane-interosseuse-avant-bras-g",
        "name": "Membrane interosseuse de l’avant-bras G",
        "nameLatin": "Membrana interossea antebrachii sinistra",
        "region": "avant-bras",
        "joint": "syndesmose radio-ulnaire",
        "notes": "Syndesmose — tissu fibreux profond, inclus comme couche ligamentaire.",
    },
    "interosseous membrane of right leg": {
        "id": "membrane-interosseuse-jambe-d",
        "name": "Membrane interosseuse de la jambe D",
        "nameLatin": "Membrana interossea cruris dextra",
        "region": "jambe",
        "joint": "syndesmose tibio-fibulaire",
        "notes": "Syndesmose — tissu fibreux profond, inclus comme couche ligamentaire.",
    },
    "interosseous membrane of left leg": {
        "id": "membrane-interosseuse-jambe-g",
        "name": "Membrane interosseuse de la jambe G",
        "nameLatin": "Membrana interossea cruris sinistra",
        "region": "jambe",
        "joint": "syndesmose tibio-fibulaire",
        "notes": "Syndesmose — tissu fibreux profond, inclus comme couche ligamentaire.",
    },
    "flexor retinaculum of right wrist": {
        "id": "retinaculum-flechisseurs-d",
        "name": "Rétinaculum des fléchisseurs droit",
        "nameLatin": "Retinaculum musculorum flexorum dextrum",
        "region": "poignet",
        "joint": "poignet",
        "notes": "Rétinaculum (ligament transverse du carpe).",
    },
    "flexor retinaculum of left wrist": {
        "id": "retinaculum-flechisseurs-g",
        "name": "Rétinaculum des fléchisseurs gauche",
        "nameLatin": "Retinaculum musculorum flexorum sinistrum",
        "region": "poignet",
        "joint": "poignet",
        "notes": "Rétinaculum (ligament transverse du carpe).",
    },
}

INCLUSION_RULES = (
    "Included from BodyParts3D: named ligaments, interosseous membranes "
    "(syndesmoses) and flexor retinacula. "
    "Excluded: calcaneal tendons, extraocular check ligaments, lens zonules, "
    "trochleae, abstract parents. Crude capsule/stick synthetics (v1) and "
    "rectangular lofted ribbons are not exported. Missing major ligaments of "
    "knee, hip, shoulder, elbow and ankle are schematic tapered fascicle bundles "
    "(rounded cross-section, fan at attachments, thinner mid-substance; "
    "source=synthetic-v2), not cadaver meshes. Annular ligament of the radius "
    "is a torus. Spinal stick ligaments and menisci are omitted "
    "(quality > quantity)."
)


def main() -> int:
    if not SKELETON_META.exists():
        print("missing skeleton.meta.json — run scripts/build_skeleton_glb.py first", file=sys.stderr)
        return 1
    sk_meta = json.loads(SKELETON_META.read_text(encoding="utf-8"))
    matrix = np.array(sk_meta["worldMatrix"], dtype=float)
    if matrix.shape != (4, 4):
        print("invalid worldMatrix in skeleton.meta.json", file=sys.stderr)
        return 1

    sk.CACHE.mkdir(parents=True, exist_ok=True)
    parts_path = sk.CACHE / "isa_parts_list_e.txt"
    element_path = sk.CACHE / "isa_element_parts.txt"
    zip_path = sk.CACHE / "isa_BP3D_4.0_obj_99.zip"
    sk.download(sk.PARTS_URL, parts_path)
    sk.download(sk.ELEMENT_URL, element_path)
    sk.download(sk.ZIP_URL, zip_path, require_zip=True)

    parts = sk.load_tsv(parts_path)
    element_map = sk.load_element_map(element_path)
    name_to_row = {row[2].lower(): row for row in parts if len(row) >= 3}

    extract = sk.CACHE / "isa_obj"
    if not extract.exists() or not any(extract.rglob("*.obj")):
        print(f"extract {zip_path}", flush=True)
        import zipfile

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract)
    obj_map = sk.find_obj_map(extract)

    items: list[tuple[str, trimesh.Trimesh, dict]] = []
    catalog = []
    missing = 0
    for en_name, info in INCLUDE.items():
        row = name_to_row.get(en_name)
        if row is None:
            print("skip unknown name", en_name, file=sys.stderr)
            missing += 1
            continue
        cid = row[0]
        meshes = []
        for file_id in element_map.get(cid, []):
            path = obj_map.get(file_id) or obj_map.get(file_id.upper())
            if path is None:
                continue
            mesh = sk.load_mesh(path)
            if mesh is not None:
                meshes.append(mesh)
        if not meshes:
            print("skip no mesh", en_name, file=sys.stderr)
            missing += 1
            continue
        mesh = meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)
        mesh.apply_transform(matrix)
        rec = {
            **info,
            "source": "bodyparts3d",
            "sourceName": en_name,
            "fmaId": cid,
            "fileIds": element_map.get(cid, []),
            "centroid": [round(float(x), 5) for x in mesh.vertices.mean(0)],
        }
        items.append((info["id"], mesh, rec))
        catalog.append(rec)

    if len(items) < 4:
        print("too few ligaments; abort", file=sys.stderr)
        return 1

    print("synthesizing schematic major-joint ligaments (v2)…", flush=True)
    synth_meshes, synth_catalog = build_synthetic()
    catalog.extend(synth_catalog)

    scene = trimesh.Scene()
    for part_id, mesh, rec in items:
        mesh.visual.vertex_colors = [210, 176, 148, 200]
        _ = mesh.vertex_normals
        mesh.metadata["name"] = part_id
        scene.add_geometry(mesh, node_name=part_id, geom_name=part_id)
    for part_id, mesh in synth_meshes:
        mesh.visual.vertex_colors = [210, 176, 148, 140]
        _ = mesh.vertex_normals
        mesh.metadata["name"] = part_id
        scene.add_geometry(mesh, node_name=part_id, geom_name=part_id)

    OUT_GLB.parent.mkdir(parents=True, exist_ok=True)
    OUT_GLB.write_bytes(export_glb(scene, include_normals=True))
    size_mb = OUT_GLB.stat().st_size / (1024 * 1024)

    n_bp3d = sum(1 for p in catalog if p.get("source") == "bodyparts3d")
    n_synth = sum(1 for p in catalog if str(p.get("source", "")).startswith("synthetic"))
    meta = {
        "glbBytes": OUT_GLB.stat().st_size,
        "glbMiB": round(size_mb, 2),
        "partCount": len(catalog),
        "countBodyparts3d": n_bp3d,
        "countSynthetic": n_synth,
        "license": "CC BY-SA 2.1 Japan (BP3D meshes); synthetic-v2 fascicle bundles are original educational approximations",
        "alignedTo": "public/models/skeleton.glb",
        "inclusionRules": INCLUSION_RULES,
    }
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    payload = {
        "version": 4,
        "defaultVisible": False,
        "inclusionRules": INCLUSION_RULES,
        "syntheticDisclaimer": (
            "Entries with source=synthetic-v2 are schematic tapered fascicle "
            "bundles (rounded lofted strands) between named landmarks. They are "
            "not segmented from cadaver imaging and must not be treated as "
            "morphologically accurate. BodyParts3D connective meshes "
            "(interosseous membranes, retinacula, named ligaments) remain "
            "source=bodyparts3d."
        ),
        "count": len(catalog),
        "countBodyparts3d": n_bp3d,
        "countSynthetic": n_synth,
        "ligaments": catalog,
    }
    OUT_CATALOG.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT_GLB} ({size_mb:.2f} MiB), {len(catalog)} parts "
        f"({n_bp3d} BP3D + {n_synth} synthetic-v2)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
