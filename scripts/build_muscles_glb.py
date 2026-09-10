#!/usr/bin/env python3
"""Merge all BodyParts3D skeletal muscle meshes into muscles.glb.

Each app muscle id becomes a named node. Same worldMatrix as skeleton.glb.
Heads / parts are concatenated under one selectable id.
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
from bp3d_muscles import enumerate_muscle_groups
from build_synthetic_muscles import build as build_synthetic
from muscle_catalog import catalog_entry

OUT_GLB = sk.ROOT / "public" / "models" / "muscles.glb"
OUT_META = sk.ROOT / "public" / "models" / "muscles.meta.json"
OUT_CATALOG = sk.ROOT / "src" / "data" / "muscleMeshes.json"
MUSCLES_JSON = sk.ROOT / "src" / "data" / "muscles.json"
SKELETON_META = sk.ROOT / "public" / "models" / "skeleton.meta.json"

MAX_FACES = 9000
MAX_GLB_MIB = 42.0

INCLUSION_RULES = (
    "All BodyParts3D 4.0 skeletal muscle organs / heads / zones that have unique "
    "OBJ files, grouped by muscle (laterality merged; named heads concatenated). "
    "Excluded: extraocular, tongue, palate, pharynx, larynx, facial expression, "
    "abstract compartment parents. Latissimus dorsi and rectus abdominis have no "
    "BP3D 4.0 mesh and remain landmark-anchored synthetics. Iliacus + psoas major "
    "are merged as iliopsoas. Fiber axis = PCA of patient-right (x≤0) vertices."
)


def _load_named(name_to_row, element_map, obj_map, en_name: str) -> trimesh.Trimesh | None:
    row = name_to_row.get(en_name.lower())
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


def _simplify(mesh: trimesh.Trimesh, max_faces: int) -> trimesh.Trimesh:
    if len(mesh.faces) <= max_faces:
        return mesh
    try:
        out = mesh.simplify_quadric_decimation(face_count=max_faces)
        if out is not None and len(out.faces) > 0:
            return out
    except Exception as exc:  # noqa: BLE001
        print(f"    simplify skip ({exc})", flush=True)
    return mesh


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


def _fiber_axis(mesh: trimesh.Trimesh) -> list[float]:
    verts = np.asarray(mesh.vertices, dtype=np.float64)
    right = verts[verts[:, 0] <= 0.0]
    if len(right) < 30:
        right = verts
    centered = right - right.mean(0)
    try:
        _, _, vh = np.linalg.svd(centered, full_matrices=False)
        axis = vh[0]
    except np.linalg.LinAlgError:
        axis = np.array([0.0, 1.0, 0.0])
    if abs(axis[0]) > abs(axis[1]) and abs(axis[0]) > abs(axis[2]) and len(right) > 30:
        # Bilateral leftover: fall back to Y/Z of right half.
        axis = vh[1] if abs(vh[1][0]) < abs(vh[0][0]) else vh[2]
    if axis[1] < -0.15:
        axis = -axis
    n = np.linalg.norm(axis)
    if n < 1e-9:
        axis = np.array([0.0, 1.0, 0.0])
    else:
        axis = axis / n
    return [round(float(x), 5) for x in axis]


def _catalog_row(muscle_id, source, names, fma_ids, file_ids, mesh, notes=None):
    focus_pos, focus_dist = _right_focus(mesh)
    row = {
        "id": muscle_id,
        "source": source,
        "sourceNames": names,
        "fmaIds": fma_ids,
        "fileIds": sorted(set(file_ids)),
        "centroid": [round(float(x), 5) for x in mesh.vertices.mean(0)],
        "focus": {"position": focus_pos, "distance": focus_dist},
        "fiberAxis": _fiber_axis(mesh),
        "vertexCount": int(len(mesh.vertices)),
        "faceCount": int(len(mesh.faces)),
    }
    if notes:
        row["notes"] = notes
    return row


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
    inc_path = sk.CACHE / "isa_inclusion_relation_list.txt"
    element_path = sk.CACHE / "isa_element_parts.txt"
    zip_path = sk.CACHE / "isa_BP3D_4.0_obj_99.zip"
    sk.download(sk.PARTS_URL, parts_path)
    sk.download(sk.INC_URL, inc_path)
    sk.download(sk.ELEMENT_URL, element_path)
    sk.download(sk.ZIP_URL, zip_path, require_zip=True)

    parts = sk.load_tsv(parts_path)
    inclusion = sk.load_tsv(inc_path)
    element_map = sk.load_element_map(element_path)
    name_to_row = {row[2].lower(): row for row in parts if len(row) >= 3}

    extract = sk.CACHE / "isa_obj"
    if not extract.exists() or not any(extract.rglob("*.obj")):
        print(f"extract {zip_path}", flush=True)
        import zipfile

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract)
    obj_map = sk.find_obj_map(extract)

    groups = enumerate_muscle_groups(parts, inclusion, element_map)
    print(f"enumerated {len(groups)} skeletal muscle groups", flush=True)

    scene = trimesh.Scene()
    catalog = []
    muscles_out = []

    for group in groups:
        loaded: list[trimesh.Trimesh] = []
        for en_name in group.source_names:
            mesh = _load_named(name_to_row, element_map, obj_map, en_name)
            if mesh is None:
                print("skip missing part", group.id, en_name, file=sys.stderr)
                continue
            loaded.append(mesh)
        if not loaded:
            print("skip empty muscle", group.id, file=sys.stderr)
            continue
        mesh = loaded[0] if len(loaded) == 1 else trimesh.util.concatenate(loaded)
        mesh.apply_transform(matrix)
        mesh = _simplify(mesh, MAX_FACES)
        _ = mesh.vertex_normals
        mesh.visual.vertex_colors = [196, 72, 58, 230]
        mesh.metadata["name"] = group.id
        scene.add_geometry(mesh, node_name=group.id, geom_name=group.id)
        entry = _catalog_row(
            group.id, "bodyparts3d", group.source_names, group.concept_ids, group.file_ids, mesh
        )
        catalog.append(entry)
        text = catalog_entry(group.key, group.head_labels())
        muscle = {
            "id": group.id,
            **text,
            "focus": entry["focus"],
            "fiberAxis": entry["fiberAxis"],
            "meshSource": "bodyparts3d",
        }
        if muscle.get("heads") is None:
            muscle.pop("heads", None)
        if not muscle.get("secondaryActions"):
            muscle.pop("secondaryActions", None)
        muscles_out.append(muscle)
        print(
            f"  + {group.id:32s}  {len(mesh.faces):6d} faces  {len(group.source_names):2d} parts  BP3D",
            flush=True,
        )

    print("synthesizing missing muscles…", flush=True)
    synth_notes = (
        "Educational multi-lobe stand-in — BodyParts3D 4.0 has no mesh for this muscle."
    )
    synth_keys = {"grand-dorsal": "latissimus dorsi", "droit-abdomen": "rectus abdominis"}
    for muscle_id, mesh in build_synthetic().items():
        _ = mesh.vertex_normals
        mesh.visual.vertex_colors = [196, 72, 58, 230]
        mesh.metadata["name"] = muscle_id
        scene.add_geometry(mesh, node_name=muscle_id, geom_name=muscle_id)
        entry = _catalog_row(
            muscle_id, "synthetic", [muscle_id], [], [], mesh, notes=synth_notes
        )
        catalog.append(entry)
        key = synth_keys.get(muscle_id, muscle_id)
        text = catalog_entry(key, [])
        muscle = {
            "id": muscle_id,
            **text,
            "focus": entry["focus"],
            "fiberAxis": entry["fiberAxis"],
            "meshSource": "synthetic",
        }
        if muscle.get("heads") is None:
            muscle.pop("heads", None)
        if not muscle.get("secondaryActions"):
            muscle.pop("secondaryActions", None)
        muscles_out.append(muscle)
        print(f"  + {muscle_id:32s}  {len(mesh.faces):6d} faces  synthetic", flush=True)

    muscles_out.sort(key=lambda m: m["name"].lower())
    catalog.sort(key=lambda m: m["id"])

    OUT_GLB.parent.mkdir(parents=True, exist_ok=True)
    OUT_GLB.write_bytes(export_glb(scene, include_normals=True))
    size_mb = OUT_GLB.stat().st_size / (1024 * 1024)
    if size_mb > MAX_GLB_MIB:
        print(f"warning: GLB {size_mb:.2f} MiB exceeds {MAX_GLB_MIB}", file=sys.stderr)

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
        "maxFacesPerMuscle": MAX_FACES,
    }
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    OUT_CATALOG.write_text(
        json.dumps(
            {
                "version": 2,
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
    MUSCLES_JSON.write_text(json.dumps(muscles_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT_GLB} ({size_mb:.2f} MiB), {len(catalog)} muscles "
        f"({n_bp3d} BP3D + {n_synth} synthetic)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
