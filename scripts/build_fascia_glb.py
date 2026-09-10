#!/usr/bin/env python3
"""Build fascia.glb from BodyParts3D deep-fascia meshes plus synthetic sheets.

Uses the same world transform as skeleton.glb (see skeleton.meta.json).
BodyParts3D / Anatomography (DBCLS) meshes: CC BY-SA 2.1 Japan.
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
from build_synthetic_fascia import build as build_synthetic

OUT_GLB = sk.ROOT / "public" / "models" / "fascia.glb"
OUT_META = sk.ROOT / "public" / "models" / "fascia.meta.json"
OUT_CATALOG = sk.ROOT / "src" / "data" / "fascia.json"
SKELETON_META = sk.ROOT / "public" / "models" / "skeleton.meta.json"

# Unique BP3D fascia meshes. Investing-fascia parents all collapse to the same
# FJ#### files (IT tract or wrist flexor retinaculum). Retinacula stay in
# ligaments.glb — do not duplicate them here. Exclude TFL (muscle), nasal
# septum, brain septa, skin and fat.
INCLUDE: dict[str, dict[str, str]] = {
    "right iliotibial tract": {
        "id": "tractus-ilio-tibial-d",
        "name": "Tractus ilio-tibial droit",
        "nameLatin": "Tractus iliotibialis dexter",
        "region": "cuisse",
        "notes": "Épaississement du fascia lata (seule nappe fasciale distincte dans BP3D 4.0).",
    },
    "left iliotibial tract": {
        "id": "tractus-ilio-tibial-g",
        "name": "Tractus ilio-tibial gauche",
        "nameLatin": "Tractus iliotibialis sinister",
        "region": "cuisse",
        "notes": "Épaississement du fascia lata (seule nappe fasciale distincte dans BP3D 4.0).",
    },
}

INCLUSION_RULES = (
    "Included from BodyParts3D: named iliotibial tract meshes (FJ1423 / FJ1423M). "
    "Investing-fascia / fascia-lata parents map to those same files and are not "
    "duplicated. Flexor retinacula of the wrist remain in ligaments.glb. "
    "Excluded: tensor fasciae latae (muscle), nasal septum, brain septa, skin, fat. "
    "BodyParts3D 4.0 has no dedicated thoracolumbar / crural / antebrachial fascia "
    "meshes. Those three regional sleeves plus one posterior thoracolumbar sheet "
    "are schematic (source=synthetic-v2). Palmar / plantar aponeuroses and linea "
    "alba sticks from v1 are omitted (quality > quantity)."
)

GAPS = [
    "fascia cervicale / nuchal",
    "rétinaculums de cheville (hors ligaments)",
    "clavipectoral / fascia pectoral",
    "septums intermusculaires",
    "aponévroses palmaire et plantaire (omises : géométrie v1 insuffisante)",
]


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

    items: list[tuple[str, trimesh.Trimesh]] = []
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
        items.append((info["id"], mesh))
        catalog.append(
            {
                **info,
                "source": "bodyparts3d",
                "sourceName": en_name,
                "fmaId": cid,
                "fileIds": element_map.get(cid, []),
                "centroid": [round(float(x), 5) for x in mesh.vertices.mean(0)],
            }
        )

    if missing:
        print("missing BP3D fascia parts:", missing, file=sys.stderr)
        return 1

    print("synthesizing regional fascia sleeves (v2)…", flush=True)
    synth_meshes, synth_catalog = build_synthetic()
    catalog.extend(synth_catalog)

    scene = trimesh.Scene()
    for part_id, mesh in items:
        mesh.visual.vertex_colors = [140, 170, 190, 170]
        _ = mesh.vertex_normals
        mesh.metadata["name"] = part_id
        scene.add_geometry(mesh, node_name=part_id, geom_name=part_id)
    for part_id, mesh in synth_meshes:
        mesh.visual.vertex_colors = [140, 170, 190, 110]
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
        "license": "CC BY-SA 2.1 Japan (BP3D meshes); synthetic-v2 sleeves are original educational approximations",
        "alignedTo": "public/models/skeleton.glb",
        "inclusionRules": INCLUSION_RULES,
        "gaps": GAPS,
    }
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    payload = {
        "version": 2,
        "defaultVisible": False,
        "inclusionRules": INCLUSION_RULES,
        "gaps": GAPS,
        "syntheticDisclaimer": (
            "Entries with source=synthetic-v2 are schematic regional deep-fascia "
            "sleeves / one thoracolumbar sheet. They are not cadaver segmentations."
        ),
        "count": len(catalog),
        "countBodyparts3d": n_bp3d,
        "countSynthetic": n_synth,
        "fascia": catalog,
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
