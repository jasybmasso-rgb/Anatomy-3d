#!/usr/bin/env python3
"""Merge BodyParts3D muscle meshes (plus two synthetic stand-ins) into muscles.glb.

Each app muscle id becomes a named node. Same worldMatrix as skeleton.glb.
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
from build_synthetic_muscles import build as build_synthetic

OUT_GLB = sk.ROOT / "public" / "models" / "muscles.glb"
OUT_META = sk.ROOT / "public" / "models" / "muscles.meta.json"
OUT_CATALOG = sk.ROOT / "src" / "data" / "muscleMeshes.json"
MUSCLES_JSON = sk.ROOT / "src" / "data" / "muscles.json"
SKELETON_META = sk.ROOT / "public" / "models" / "skeleton.meta.json"

# Leaf English names from isa_parts_list_e.txt. Parents ("deltoid") have no unique mesh.
MUSCLE_PARTS: dict[str, list[str]] = {
    "biceps-brachial": [
        "short head of right biceps brachii",
        "short head of left biceps brachii",
        "long head of right biceps brachii",
        "long head of left biceps brachii",
    ],
    "triceps-brachial": [
        "long head of right triceps brachii",
        "long head of left triceps brachii",
        "medial head of right triceps brachii",
        "medial head of left triceps brachii",
        "lateral head of right triceps brachii",
        "lateral head of left triceps brachii",
    ],
    "deltoide": [
        "clavicular part of right deltoid",
        "clavicular part of left deltoid",
        "acromial part of right deltoid",
        "acromial part of left deltoid",
        "spinal part of right deltoid",
        "spinal part of left deltoid",
    ],
    "grand-pectoral": [
        "clavicular part of right pectoralis major",
        "clavicular part of left pectoralis major",
        "sternocostal part of right pectoralis major",
        "sternocostal part of left pectoralis major",
        "abdominal part of right pectoralis major",
        "abdominal part of left pectoralis major",
    ],
    "trapeze": [
        "ascending part of right trapezius",
        "ascending part of left trapezius",
        "transverse part of right trapezius",
        "transverse part of left trapezius",
        "descending part of right trapezius",
        "descending part of left trapezius",
    ],
    "sterno-cleido-mastoidien": [
        "right sternocleidomastoid",
        "left sternocleidomastoid",
    ],
    "biceps-femoral": [
        "long head of right biceps femoris",
        "long head of left biceps femoris",
        "short head of right biceps femoris",
        "short head of left biceps femoris",
    ],
    "semi-tendineux": [
        "right semitendinosus",
        "left semitendinosus",
    ],
    "semi-membraneux": [
        "right semimembranosus",
        "left semimembranosus",
    ],
    "droit-femoral": [
        "right rectus femoris",
        "left rectus femoris",
    ],
    "vaste-lateral": [
        "right vastus lateralis",
        "left vastus lateralis",
    ],
    "vaste-medial": [
        "right vastus medialis",
        "left vastus medialis",
    ],
    "vaste-intermediaire": [
        "right vastus intermedius",
        "left vastus intermedius",
    ],
    "grand-fessier": [
        "right gluteus maximus",
        "left gluteus maximus",
    ],
    "iliopsoas": [
        "right iliacus",
        "left iliacus",
        "right psoas major",
        "left psoas major",
    ],
    "gastrocnemien": [
        "medial head of right gastrocnemius",
        "medial head of left gastrocnemius",
        "lateral head of right gastrocnemius",
        "lateral head of left gastrocnemius",
    ],
    "soleaire": [
        "right soleus",
        "left soleus",
    ],
    "tibial-anterieur": [
        "right tibialis anterior",
        "left tibialis anterior",
    ],
    "oblique-externe": [
        "right external oblique",
        "left external oblique",
    ],
    "supra-epineux": [
        "right supraspinatus",
        "left supraspinatus",
    ],
}

# Confirmed absent from BodyParts3D 4.0 ISA parts list.
SYNTHETIC_IDS = ("grand-dorsal", "droit-abdomen")

INCLUSION_RULES = (
    "App muscles mapped to BodyParts3D IS-A leaf meshes (heads / parts), "
    "concatenated per muscle id, aligned with skeleton.meta.json worldMatrix. "
    "Latissimus dorsi and rectus abdominis have no BP3D 4.0 mesh and are "
    "synthesized from landmarks (multi-lobe bands). Tensor fasciae latae and "
    "other muscles not in muscles.json are omitted."
)


def _load_named(name_to_row, element_map, obj_map, en_name: str) -> trimesh.Trimesh | None:
    row = name_to_row.get(en_name)
    if row is None:
        return None
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
        return None
    return meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)


def _right_focus(mesh: trimesh.Trimesh) -> tuple[list[float], float]:
    verts = mesh.vertices
    right = verts[verts[:, 0] <= 0.0]
    if len(right) < 20:
        right = verts
    centroid = right.mean(0)
    extents = right.max(0) - right.min(0)
    radius = float(np.linalg.norm(extents) * 0.5)
    distance = float(min(1.35, max(0.62, radius * 2.35)))
    return [round(float(x), 5) for x in centroid], round(distance, 3)


def main() -> int:
    if not SKELETON_META.exists():
        print("missing skeleton.meta.json — run scripts/build_skeleton_glb.py first", file=sys.stderr)
        return 1
    sk_meta = json.loads(SKELETON_META.read_text(encoding="utf-8"))
    matrix = np.array(sk_meta["worldMatrix"], dtype=float)
    if matrix.shape != (4, 4):
        print("invalid worldMatrix in skeleton.meta.json", file=sys.stderr)
        return 1

    muscles_data = json.loads(MUSCLES_JSON.read_text(encoding="utf-8"))
    app_ids = [m["id"] for m in muscles_data]
    expected = set(MUSCLE_PARTS) | set(SYNTHETIC_IDS)
    if set(app_ids) != expected:
        print("muscle id mismatch", set(app_ids).symmetric_difference(expected), file=sys.stderr)
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

    scene = trimesh.Scene()
    catalog = []
    by_id: dict[str, trimesh.Trimesh] = {}

    for muscle_id, names in MUSCLE_PARTS.items():
        loaded: list[trimesh.Trimesh] = []
        fma_ids: list[str] = []
        file_ids: list[str] = []
        for en_name in names:
            mesh = _load_named(name_to_row, element_map, obj_map, en_name)
            if mesh is None:
                print("missing part", muscle_id, en_name, file=sys.stderr)
                return 1
            row = name_to_row[en_name]
            fma_ids.append(row[0])
            file_ids.extend(element_map.get(row[0], []))
            loaded.append(mesh)
        mesh = loaded[0] if len(loaded) == 1 else trimesh.util.concatenate(loaded)
        mesh.apply_transform(matrix)
        _ = mesh.vertex_normals
        mesh.visual.vertex_colors = [196, 72, 58, 230]
        mesh.metadata["name"] = muscle_id
        scene.add_geometry(mesh, node_name=muscle_id, geom_name=muscle_id)
        by_id[muscle_id] = mesh
        centroid = [round(float(x), 5) for x in mesh.vertices.mean(0)]
        focus_pos, focus_dist = _right_focus(mesh)
        catalog.append(
            {
                "id": muscle_id,
                "source": "bodyparts3d",
                "sourceNames": names,
                "fmaIds": fma_ids,
                "fileIds": sorted(set(file_ids)),
                "centroid": centroid,
                "focus": {"position": focus_pos, "distance": focus_dist},
                "vertexCount": int(len(mesh.vertices)),
                "faceCount": int(len(mesh.faces)),
            }
        )
        print(f"  + {muscle_id:28s}  {len(mesh.faces):7d} faces  BP3D", flush=True)

    print("synthesizing missing muscles…", flush=True)
    for muscle_id, mesh in build_synthetic().items():
        _ = mesh.vertex_normals
        mesh.visual.vertex_colors = [196, 72, 58, 230]
        mesh.metadata["name"] = muscle_id
        scene.add_geometry(mesh, node_name=muscle_id, geom_name=muscle_id)
        by_id[muscle_id] = mesh
        focus_pos, focus_dist = _right_focus(mesh)
        catalog.append(
            {
                "id": muscle_id,
                "source": "synthetic",
                "sourceNames": [muscle_id],
                "fmaIds": [],
                "fileIds": [],
                "centroid": [round(float(x), 5) for x in mesh.vertices.mean(0)],
                "focus": {"position": focus_pos, "distance": focus_dist},
                "vertexCount": int(len(mesh.vertices)),
                "faceCount": int(len(mesh.faces)),
                "notes": (
                    "Educational multi-lobe stand-in — BodyParts3D 4.0 has no mesh "
                    "for this muscle."
                ),
            }
        )
        print(f"  + {muscle_id:28s}  {len(mesh.faces):7d} faces  synthetic", flush=True)

    OUT_GLB.parent.mkdir(parents=True, exist_ok=True)
    OUT_GLB.write_bytes(export_glb(scene, include_normals=True))
    size_mb = OUT_GLB.stat().st_size / (1024 * 1024)

    n_bp3d = sum(1 for p in catalog if p["source"] == "bodyparts3d")
    n_synth = sum(1 for p in catalog if p["source"] == "synthetic")
    meta = {
        "glbBytes": OUT_GLB.stat().st_size,
        "glbMiB": round(size_mb, 2),
        "partCount": len(catalog),
        "countBodyparts3d": n_bp3d,
        "countSynthetic": n_synth,
        "license": "CC BY-SA 2.1 Japan (BP3D meshes); synthetic stand-ins are original educational approximations",
        "alignedTo": "public/models/skeleton.glb",
        "inclusionRules": INCLUSION_RULES,
    }
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    OUT_CATALOG.write_text(
        json.dumps(
            {
                "version": 1,
                "inclusionRules": INCLUSION_RULES,
                "count": len(catalog),
                "countBodyparts3d": n_bp3d,
                "countSynthetic": n_synth,
                "muscles": catalog,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    catalog_by_id = {entry["id"]: entry for entry in catalog}
    for muscle in muscles_data:
        entry = catalog_by_id[muscle["id"]]
        muscle["meshSource"] = entry["source"]
        muscle["focus"] = {
            "position": entry["focus"]["position"],
            "distance": entry["focus"]["distance"],
        }

    MUSCLES_JSON.write_text(json.dumps(muscles_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT_GLB} ({size_mb:.2f} MiB), {len(catalog)} muscles ({n_bp3d} BP3D + {n_synth} synthetic)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
