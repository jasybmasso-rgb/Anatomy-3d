#!/usr/bin/env python3
"""Filter BodyParts3D bone + cartilage OBJs, merge to a web GLB, emit landmarks.json.

Cartilage (costal, intervertebral discs, laryngeal, nasal) is a second scene
node in skeleton.glb — always visible with bone, not a Couches category.
Landmarks are derived from bone meshes only. Same worldMatrix for both.

Source: BodyParts3D / Anatomography (DBCLS), CC BY-SA 2.1 Japan.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.request
import zipfile
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import trimesh
from trimesh.exchange.gltf import export_glb

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path("/tmp/bp3d")
OUT_GLB = ROOT / "public" / "models" / "skeleton.glb"
OUT_META = ROOT / "public" / "models" / "skeleton.meta.json"
OUT_LANDMARKS = ROOT / "src" / "data" / "landmarks.json"
LANDMARK_SRC = Path(__file__).resolve().parent / "landmark_sources.json"

PARTS_URL = "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_parts_list_e.txt"
INC_URL = "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_inclusion_relation_list.txt"
ELEMENT_URL = "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_element_parts.txt"
ZIP_URL = "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip"

BONE_ROOT = "FMA5018"
TARGET_HEIGHT = 1.70
PELVIS_NAMES = ("right hip bone", "left hip bone", "hip bone", "sacrum")
# Sternum pieces are not IS-A descendants of bone organ in the BP3D tree.
EXTRA_PART_NAMES = ("manubrium", "body of sternum", "xiphoid process")
MAX_GLB_MIB = 48.0

EXCLUDE_SUBSTR = (
    "marrow",
    "periosteum",
    "cartilage",
    "ligament",
    "artery",
    "vein",
    "nerve",
    "muscle",
    "tendon",
    "fascia",
    "skin",
    "tooth",
    "teeth",
    "enamel",
    "dentin",
    "pulp",
    "organ system",
    "set of",
    "zone of",
)

COSTAL_LEAF_RE = re.compile(
    r"^(left|right) (first|second|third|fourth|fifth|sixth|seventh) costal cartilage$"
)
IVD_RE = re.compile(r"^intervertebral disk of ")
CARTILAGE_EXACT = {
    "thyroid cartilage",
    "cricoid cartilage",
    "epiglottis",
    "right arytenoid cartilage",
    "left arytenoid cartilage",
    "right corniculate cartilage",
    "left corniculate cartilage",
    "right cuneiform cartilage",
    "left cuneiform cartilage",
    "septal nasal cartilage",
    "right major alar cartilage",
    "left major alar cartilage",
    "right lateral nasal cartilage",
    "left lateral nasal cartilage",
}

ABSTRACT_NAMES = {
    "bone organ",
    "long bone",
    "short bone",
    "flat bone",
    "irregular bone",
    "pneumatized bone",
    "sesamoid bone",
    "accessory bone",
    "bone of free limb",
    "bone of free upper limb",
    "bone of free lower limb",
    "true rib",
    "false rib",
    "typical rib",
    "atypical rib",
    "floating rib",
    "rib",
    "vertebra",
    "cervical vertebra",
    "thoracic vertebra",
    "lumbar vertebra",
    "hip bone",
    "clavicle",
    "scapula",
    "humerus",
    "radius",
    "ulna",
    "femur",
    "tibia",
    "fibula",
    "patella",
    "calcaneus",
    "talus",
    "metacarpal bone",
    "phalanx of finger",
}


def zip_ok(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1_000_000:
        return False
    try:
        with zipfile.ZipFile(path) as zf:
            return zf.testzip() is None
    except zipfile.BadZipFile:
        return False


def download(url: str, dest: Path, *, require_zip: bool = False) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        if not require_zip or zip_ok(dest):
            return
        dest.unlink()
    print(f"download {url} -> {dest}", flush=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(dest)
    if require_zip and not zip_ok(dest):
        raise RuntimeError(f"invalid zip after download: {dest}")


def load_tsv(path: Path) -> list[list[str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) >= 3:
            rows.append(cols)
    return rows


def bone_concept_ids(parts: list[list[str]], inc: list[list[str]]) -> dict[str, tuple[str, str]]:
    id_to_name = {r[0]: r[2] for r in parts}
    id_to_bp = {r[0]: r[1] for r in parts}
    children: dict[str, list[str]] = defaultdict(list)
    for row in inc:
        if len(row) >= 4:
            children[row[0]].append(row[2])

    seen: set[str] = set()
    q = deque([BONE_ROOT])
    while q:
        n = q.popleft()
        if n in seen:
            continue
        seen.add(n)
        q.extend(children.get(n, []))

    # Leaves only: skip unpaired parents ("femur") when left/right children exist.
    leaves = {cid for cid in seen if not any(child in seen for child in children.get(cid, []))}

    out: dict[str, tuple[str, str]] = {}
    for cid in leaves:
        name = id_to_name.get(cid, "")
        low = name.lower()
        if not name or low in ABSTRACT_NAMES:
            continue
        if any(x in low for x in EXCLUDE_SUBSTR):
            continue
        out[cid] = (id_to_bp.get(cid, ""), name)

    extras = {n.lower() for n in EXTRA_PART_NAMES}
    for cid, name in id_to_name.items():
        if name.lower() in extras:
            out[cid] = (id_to_bp.get(cid, ""), name)
    return out


def is_cartilage_part(name: str) -> bool:
    low = name.lower().strip()
    return bool(COSTAL_LEAF_RE.match(low) or IVD_RE.match(low) or low in CARTILAGE_EXACT)


def cartilage_file_records(
    parts: list[list[str]],
    element_map: dict[str, list[str]],
) -> list[dict]:
    """Unique BP3D cartilage meshes (costal, IV discs, laryngeal, nasal).

    Parents such as 'costal cartilage' / 'articular disk of symphysis' share
    child FJ files and are skipped. No articular hyaline or menisci exist in
    BodyParts3D 4.0.
    """
    seen_files: set[str] = set()
    records: list[dict] = []
    for row in parts:
        if len(row) < 3:
            continue
        cid, name = row[0], row[2]
        if not is_cartilage_part(name):
            continue
        for file_id in element_map.get(cid, []):
            if file_id in seen_files:
                continue
            seen_files.add(file_id)
            records.append({"fmaId": cid, "name": name, "fileId": file_id})
    # Parent "intervertebral disk" holds one leftover FJ not named "disk of …".
    for row in parts:
        if len(row) < 3 or row[2].lower() != "intervertebral disk":
            continue
        cid = row[0]
        for file_id in element_map.get(cid, []):
            if file_id in seen_files:
                continue
            seen_files.add(file_id)
            records.append({"fmaId": cid, "name": "intervertebral disk", "fileId": file_id})
    return records


def find_obj_map(extract_dir: Path) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for path in extract_dir.rglob("*.obj"):
        stem = path.stem
        mapping[stem] = path
        mapping[stem.upper()] = path
    return mapping


def load_element_map(path: Path) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = defaultdict(list)
    for row in load_tsv(path):
        if len(row) >= 3 and row[2] not in mapping[row[0]]:
            mapping[row[0]].append(row[2])
    return mapping


def load_mesh(path: Path) -> trimesh.Trimesh | None:
    loaded = trimesh.load(path, force="mesh", skip_materials=True)
    if isinstance(loaded, trimesh.Scene):
        geoms = [g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not geoms:
            return None
        loaded = trimesh.util.concatenate(geoms)
    if not isinstance(loaded, trimesh.Trimesh) or loaded.vertices.size == 0:
        return None
    return loaded


def pick_up_axis(bounds: np.ndarray) -> int:
    extents = bounds[1] - bounds[0]
    return int(np.argmax(extents))


def normalize_meshes(
    items: list[tuple[str, str, trimesh.Trimesh]],
) -> tuple[list[tuple[str, str, trimesh.Trimesh]], dict]:
    all_v = np.vstack([m.vertices for _, _, m in items])
    bounds = np.vstack([all_v.min(0), all_v.max(0)])
    up = pick_up_axis(bounds)

    # Rotate so up becomes +Y
    rot = np.eye(4)
    if up == 0:
        rot[:3, :3] = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1])[:3, :3]
    elif up == 2:
        rot[:3, :3] = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])[:3, :3]

    world = rot.copy()
    for _, _, mesh in items:
        mesh.apply_transform(rot)

    all_v = np.vstack([m.vertices for _, _, m in items])
    # millimetres → metres if the figure is huge
    span = float(all_v.max(0)[1] - all_v.min(0)[1])
    scale = 1.0
    if span > 10:
        scale = 0.001
        smm = np.eye(4)
        smm[:3, :3] *= scale
        world = smm @ world
        for _, _, mesh in items:
            mesh.apply_scale(scale)
        all_v = np.vstack([m.vertices for _, _, m in items])
        span = float(all_v.max(0)[1] - all_v.min(0)[1])

    height_scale = 1.0
    if span > 1e-6:
        height_scale = TARGET_HEIGHT / span
        sh = np.eye(4)
        sh[:3, :3] *= height_scale
        world = sh @ world
        for _, _, mesh in items:
            mesh.apply_scale(height_scale)
        all_v = np.vstack([m.vertices for _, _, m in items])

    # Pelvis origin: centroid of hip bones + sacrum
    pelvis_v = []
    for _cid, name, mesh in items:
        if name.lower() in PELVIS_NAMES:
            pelvis_v.append(mesh.vertices)
    if not pelvis_v:
        pelvis_v = [all_v]
    pelvis_c = np.vstack(pelvis_v).mean(0)
    shift = np.eye(4)
    shift[:3, 3] = -pelvis_c
    world = shift @ world
    for _, _, mesh in items:
        mesh.apply_transform(shift)

    # Face +Z: skull / maxilla should be anterior (larger Z than sacrum)
    def named_centroid(substr: str) -> np.ndarray | None:
        vs = [m.vertices for _, n, m in items if substr in n.lower()]
        if not vs:
            return None
        return np.vstack(vs).mean(0)

    face = named_centroid("frontal bone")
    if face is None:
        face = named_centroid("maxilla")
    back = named_centroid("sacrum")
    yaw = 0.0
    if face is not None and back is not None:
        delta = face - back
        # Want anterior along +Z
        yaw = float(np.arctan2(delta[0], delta[2]))
        yaw_m = trimesh.transformations.rotation_matrix(-yaw, [0, 1, 0])
        world = yaw_m @ world
        for _, _, mesh in items:
            mesh.apply_transform(yaw_m)

    # Patient's right → −X (matches existing stylized muscle coordinates).
    flipped_x = False
    right = named_centroid("right femur")
    if right is not None and right[0] > 0:
        flip = np.diag([-1.0, 1.0, 1.0, 1.0])
        world = flip @ world
        for _, _, mesh in items:
            mesh.apply_transform(flip)
        flipped_x = True

    all_v = np.vstack([m.vertices for _, _, m in items])
    meta = {
        "targetHeightM": TARGET_HEIGHT,
        "detectedUpAxis": int(up),
        "mmToM": scale == 0.001,
        "yawRad": yaw,
        "flippedX": flipped_x,
        "heightScale": height_scale,
        "worldMatrix": world.round(8).tolist(),
        "bounds": {
            "min": all_v.min(0).round(5).tolist(),
            "max": all_v.max(0).round(5).tolist(),
        },
        "vertexCount": int(sum(len(m.vertices) for _, _, m in items)),
        "faceCount": int(sum(len(m.faces) for _, _, m in items)),
        "boneCount": len(items),
    }
    return items, meta


def bone_point(mesh: trimesh.Trimesh, mode: str) -> np.ndarray:
    v = mesh.vertices
    if mode == "centroid":
        return v.mean(0)
    if mode == "bbox_max_y" or mode == "superior":
        return v[np.argmax(v[:, 1])]
    if mode == "bbox_min_y" or mode == "inferior":
        return v[np.argmin(v[:, 1])]
    if mode == "bbox_max_z" or mode == "anterior":
        return v[np.argmax(v[:, 2])]
    if mode == "bbox_min_z" or mode == "posterior":
        return v[np.argmin(v[:, 2])]
    if mode == "bbox_max_x":
        return v[np.argmax(v[:, 0])]
    if mode == "bbox_min_x":
        return v[np.argmin(v[:, 0])]
    if mode == "lateral":
        return v[np.argmax(np.abs(v[:, 0]))]
    if mode == "medial":
        return v[np.argmin(np.abs(v[:, 0]))]
    if mode == "superior_anterior":
        subset = v[v[:, 1] >= np.percentile(v[:, 1], 60)]
        return subset[np.argmax(subset[:, 2])]
    if mode == "superior_posterior":
        subset = v[v[:, 1] >= np.percentile(v[:, 1], 60)]
        return subset[np.argmin(subset[:, 2])]
    if mode == "mid_anterior":
        lo, hi = np.percentile(v[:, 1], [35, 70])
        subset = v[(v[:, 1] >= lo) & (v[:, 1] <= hi)]
        return subset[np.argmax(subset[:, 2])]
    if mode == "anterior_inferior_medial":
        subset = v[(v[:, 1] <= np.percentile(v[:, 1], 45)) & (v[:, 2] >= np.percentile(v[:, 2], 55))]
        if len(subset) == 0:
            return v.mean(0)
        return subset[np.argmin(np.abs(subset[:, 0]))]
    return v.mean(0)


def resolve_mesh(
    match_names: list[str],
    by_name: dict[str, trimesh.Trimesh],
) -> trimesh.Trimesh | None:
    lowered = {k.lower(): v for k, v in by_name.items()}
    for raw in match_names:
        key = raw.lower()
        if key in lowered:
            return lowered[key]
        candidates = [
            (name, mesh)
            for name, mesh in lowered.items()
            if name == key or name.endswith(" " + key) or name.endswith(key) or key in name
        ]
        if candidates:
            candidates.sort(key=lambda item: (0 if item[0] == key else 1, len(item[0])))
            return candidates[0][1]
    return None


def build_landmarks(
    items: list[tuple[str, str, trimesh.Trimesh]],
) -> list[dict]:
    spec = json.loads(LANDMARK_SRC.read_text(encoding="utf-8"))
    by_name = {name: mesh for _cid, name, mesh in items}
    cid_by_name = {name: cid for cid, name, _mesh in items}
    out = []
    for entry in spec["landmarks"]:
        matches = entry["match"]
        mode = entry["mode"]
        if mode == "mid_centroids":
            meshes = [resolve_mesh([n], by_name) for n in matches]
            meshes = [m for m in meshes if m is not None]
            if len(meshes) < 1:
                print("skip landmark", entry["id"], file=sys.stderr)
                continue
            pos = np.mean([m.vertices.mean(0) for m in meshes], axis=0)
            source = ", ".join(matches)
        elif mode == "anterior_inferior_medial" and len(matches) > 1:
            meshes = [resolve_mesh([n], by_name) for n in matches]
            meshes = [m for m in meshes if m is not None]
            if not meshes:
                print("skip landmark", entry["id"], file=sys.stderr)
                continue
            pos = np.mean([bone_point(m, mode) for m in meshes], axis=0)
            source = ", ".join(matches)
        else:
            mesh = resolve_mesh(matches, by_name)
            if mesh is None:
                print("skip landmark", entry["id"], matches, file=sys.stderr)
                continue
            pos = bone_point(mesh, mode)
            source = next((n for n in matches if n.lower() in {k.lower() for k in by_name}), matches[0])
        fma = cid_by_name.get(source, "")
        out.append(
            {
                "id": entry["id"],
                "name": entry["name"],
                "nameLatin": entry["nameLatin"],
                "region": entry["region"],
                "position": [round(float(x), 5) for x in pos],
                "source": {
                    "fmaId": fma,
                    "partName": source,
                    "mode": mode,
                    "precision": "approximate-centroid-or-bbox",
                },
            }
        )
    return out


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    parts_path = CACHE / "isa_parts_list_e.txt"
    inc_path = CACHE / "isa_inclusion_relation_list.txt"
    element_path = CACHE / "isa_element_parts.txt"
    zip_path = CACHE / "isa_BP3D_4.0_obj_99.zip"
    download(PARTS_URL, parts_path)
    download(INC_URL, inc_path)
    download(ELEMENT_URL, element_path)
    download(ZIP_URL, zip_path, require_zip=True)

    parts = load_tsv(parts_path)
    inc = load_tsv(inc_path)
    element_map = load_element_map(element_path)
    bones = bone_concept_ids(parts, inc)
    print(f"candidate bone concepts: {len(bones)}", flush=True)

    extract = CACHE / "isa_obj"
    if not extract.exists() or not any(extract.rglob("*.obj")):
        print(f"extract {zip_path}", flush=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract)

    obj_map = find_obj_map(extract)
    print(f"obj files: {len(obj_map) // 2}", flush=True)

    items: list[tuple[str, str, trimesh.Trimesh]] = []
    missing = 0
    for cid, (_bp, name) in bones.items():
        file_ids = element_map.get(cid, [])
        meshes: list[trimesh.Trimesh] = []
        for file_id in file_ids:
            path = obj_map.get(file_id) or obj_map.get(file_id.upper())
            if path is None:
                continue
            mesh = load_mesh(path)
            if mesh is not None:
                meshes.append(mesh)
        if not meshes:
            missing += 1
            continue
        if len(meshes) == 1:
            items.append((cid, name, meshes[0]))
        else:
            items.append((cid, name, trimesh.util.concatenate(meshes)))
    print(f"loaded bone meshes: {len(items)} (missing {missing})", flush=True)
    if len(items) < 30:
        print("too few bones; abort", file=sys.stderr)
        return 1

    cart_recs = cartilage_file_records(parts, element_map)
    cartilage_meshes: list[trimesh.Trimesh] = []
    cart_missing = 0
    for rec in cart_recs:
        path = obj_map.get(rec["fileId"]) or obj_map.get(rec["fileId"].upper())
        if path is None:
            cart_missing += 1
            continue
        mesh = load_mesh(path)
        if mesh is None:
            cart_missing += 1
            continue
        cartilage_meshes.append(mesh)
    print(
        f"loaded cartilage meshes: {len(cartilage_meshes)} "
        f"({len(cart_recs)} unique files, missing {cart_missing})",
        flush=True,
    )

    items, meta = normalize_meshes(items)
    world = np.array(meta["worldMatrix"], dtype=float)
    for mesh in cartilage_meshes:
        mesh.apply_transform(world)

    bones_combined = trimesh.util.concatenate([m for _c, _n, m in items])
    bones_combined.visual.vertex_colors = [232, 220, 200, 255]
    _ = bones_combined.vertex_normals

    cartilage_combined = None
    if cartilage_meshes:
        cartilage_combined = trimesh.util.concatenate(cartilage_meshes)
        cartilage_combined.visual.vertex_colors = [185, 212, 228, 190]
        _ = cartilage_combined.vertex_normals

    scene = trimesh.Scene()
    scene.add_geometry(bones_combined, node_name="bones", geom_name="bones")
    if cartilage_combined is not None:
        scene.add_geometry(cartilage_combined, node_name="cartilage", geom_name="cartilage")

    OUT_GLB.parent.mkdir(parents=True, exist_ok=True)
    OUT_GLB.write_bytes(export_glb(scene, include_normals=True))
    size_mb = OUT_GLB.stat().st_size / (1024 * 1024)
    if size_mb > MAX_GLB_MIB:
        target_faces = max(80_000, int(len(bones_combined.faces) * MAX_GLB_MIB / size_mb))
        print(f"decimate bones {len(bones_combined.faces)} faces -> ~{target_faces} ({size_mb:.1f} MiB)", flush=True)
        try:
            simplified = bones_combined.simplify_quadric_decimation(face_count=target_faces)
            if isinstance(simplified, trimesh.Trimesh) and len(simplified.faces) > 1000:
                bones_combined = simplified
                bones_combined.visual.vertex_colors = [232, 220, 200, 255]
                _ = bones_combined.vertex_normals
                scene = trimesh.Scene()
                scene.add_geometry(bones_combined, node_name="bones", geom_name="bones")
                if cartilage_combined is not None:
                    scene.add_geometry(cartilage_combined, node_name="cartilage", geom_name="cartilage")
                OUT_GLB.write_bytes(export_glb(scene, include_normals=True))
                meta["decimatedFaces"] = int(len(bones_combined.faces))
        except Exception as exc:  # noqa: BLE001
            print(f"decimation skipped: {exc}", flush=True)
    size_mb = OUT_GLB.stat().st_size / (1024 * 1024)
    meta["glbBytes"] = OUT_GLB.stat().st_size
    meta["glbMiB"] = round(size_mb, 2)
    meta["cartilageCount"] = len(cartilage_meshes)
    meta["cartilageConcepts"] = sorted({r["name"] for r in cart_recs})
    meta["cartilageFiles"] = [r["fileId"] for r in cart_recs]
    meta["sourceZip"] = ZIP_URL
    meta["license"] = "CC BY-SA 2.1 Japan"
    meta["attribution"] = (
        "BodyParts3D, Copyright© 2008 The Database Center for Life Science "
        "licensed by CC Attribution-Share Alike 2.1 Japan"
    )
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    landmarks = build_landmarks(items)
    payload = {
        "version": 1,
        "space": {
            "up": "Y",
            "units": "meters",
            "figureHeight": TARGET_HEIGHT,
            "origin": "near pelvis (hip bones + sacrum centroid)",
            "facing": "+Z",
        },
        "precision": (
            "v1 landmarks are approximate centroids or bounding-box extrema of "
            "BodyParts3D bone meshes, after the same transform as skeleton.glb. "
            "Pending manual refinement for origin/insertion binding."
        ),
        "count": len(landmarks),
        "landmarks": landmarks,
    }
    OUT_LANDMARKS.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT_GLB} ({size_mb:.2f} MiB), {len(landmarks)} landmarks, "
        f"{len(cartilage_meshes)} cartilage meshes",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
