"""Extract the abdominal wall from the Z-Anatomy Startup.blend.

Run:
  blender --background /path/to/Startup.blend --python extract_original.py

Writes models/original.glb and merges triangle stats into metrics.json.
Does not modify the source blend.
"""

import json
import os
import re
import sys

import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS = os.path.join(ROOT, "models")
METRICS_PATH = os.path.join(ROOT, "metrics.json")
os.makedirs(MODELS, exist_ok=True)

# Stable id, source object name in Z-Anatomy (May 2023 template).
TARGETS = [
    ("rectus_l", "Rectus abdominis muscle.l"),
    ("rectus_r", "Rectus abdominis muscle.r"),
    ("external_l", "External abdominal oblique muscle.l"),
    ("external_r", "External abdominal oblique muscle.r"),
    ("internal_l", "Internal abdominal oblique muscle.l"),
    ("internal_r", "Internal abdominal oblique muscle.r"),
    ("transversus_l", "Transversus abdominis muscle.l"),
    ("transversus_r", "Transversus abdominis muscle.r"),
]

MUSCLE_COLORS = {
    "rectus": (0.72, 0.27, 0.26, 1.0),
    "external": (0.80, 0.42, 0.30, 1.0),
    "internal": (0.66, 0.32, 0.40, 1.0),
    "transversus": (0.52, 0.26, 0.34, 1.0),
}

MARKER = re.compile(r"\.[oe]\d*[lr]$", re.IGNORECASE)


def lighter(color, mix=0.62):
    return tuple(color[i] * (1.0 - mix) + mix for i in range(3)) + (1.0,)


def tri_count(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def border_stats(me):
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    border_edges = [e for e in bm.edges if e.is_boundary]
    verts = set()
    for e in border_edges:
        verts.add(e.verts[0].index)
        verts.add(e.verts[1].index)
    bm.free()
    return len(border_edges), len(verts)


def material_counts(me):
    counts = {}
    for poly in me.polygons:
        counts[poly.material_index] = counts.get(poly.material_index, 0) + 1
    return counts


def make_principled(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = color
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.52
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat


def full_muscle_census():
    """Triangle count of skeletal-muscle bodies (both sides), excluding origin/insertion markers."""
    total = 0
    objects = 0
    largest = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        cols = [c.name for c in obj.users_collection]
        if not any("uscle" in c or "uscular" in c for c in cols):
            continue
        if MARKER.search(obj.name):
            continue
        if obj.name.endswith((".g", ".j", ".t")):
            continue
        tris = tri_count(obj.data)
        if tris < 20:
            continue
        total += tris
        objects += 1
        largest.append((tris, obj.name))
    largest.sort(reverse=True)
    return {
        "muscle_body_objects": objects,
        "muscle_body_triangles": total,
        "largest": [{"name": n, "triangles": t} for t, n in largest[:12]],
    }


def main():
    if os.environ.get("SKIP_CENSUS") == "1" and os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r", encoding="utf-8") as fh:
            census = json.load(fh).get("census")
        print("CENSUS cached", census["muscle_body_triangles"] if census else None)
    else:
        census = full_muscle_census()
        print("CENSUS", json.dumps({k: census[k] for k in ("muscle_body_objects", "muscle_body_triangles")}))

    mats = {}
    for prefix, color in MUSCLE_COLORS.items():
        mats[prefix] = (
            make_principled(f"{prefix}_muscle", color),
            make_principled(f"{prefix}_tendon", lighter(color)),
        )

    created = []
    per_muscle = []
    for sid, src_name in TARGETS:
        src = bpy.data.objects.get(src_name)
        if src is None or src.type != "MESH":
            raise SystemExit(f"Missing mesh: {src_name}")
        prefix = sid.rsplit("_", 1)[0]
        me = src.data.copy()
        me.name = sid
        det = src.matrix_world.determinant()
        me.transform(src.matrix_world.copy())
        # Replace material slots in place. Popping them makes Blender
        # collapse every polygon onto slot 0 and the tendon region disappears.
        while len(me.materials) < 2:
            me.materials.append(None)
        me.materials[0] = mats[prefix][0]
        me.materials[1] = mats[prefix][1]
        while len(me.materials) > 2:
            me.materials.pop(index=len(me.materials) - 1)
        obj = bpy.data.objects.new(sid, me)
        bpy.context.scene.collection.objects.link(obj)
        obj.matrix_world.identity()
        created.append(obj)
        tris = tri_count(me)
        b_edges, b_verts = border_stats(me)
        center = sum((Vector(v) for v in obj.bound_box), Vector()) / 8.0
        world_center = obj.matrix_world @ center
        per_muscle.append(
            {
                "id": sid,
                "sourceName": src_name,
                "triangles": tris,
                "vertices": len(me.vertices),
                "materialPolygons": material_counts(me),
                "boundaryEdges": b_edges,
                "boundaryVertices": b_verts,
                "boundaryVertexFraction": round(b_verts / max(1, len(me.vertices)), 4),
                "sharedMeshUsers": src.data.users,
                "worldDeterminant": round(det, 4),
                "centroid": [round(world_center.x, 4), round(world_center.y, 4), round(world_center.z, 4)],
            }
        )
        print(
            f"EXTRACT {sid} tris={tris} verts={len(me.vertices)} "
            f"borderVerts={b_verts} ({b_verts / len(me.vertices):.1%}) det={det:.3f} "
            f"centroid=({world_center.x:.3f},{world_center.y:.3f},{world_center.z:.3f})"
        )

    # Left/right must land on opposite X after the mirrored parent matrix is applied.
    by_id = {row["id"]: row for row in per_muscle}
    for prefix in MUSCLE_COLORS:
        cl = by_id[f"{prefix}_l"]["centroid"][0]
        cr = by_id[f"{prefix}_r"]["centroid"][0]
        if cl * cr >= 0:
            raise SystemExit(f"{prefix} L/R centroids did not separate on X ({cl}, {cr})")

    # Drop the rest of the atlas so the work file and the export stay small.
    keep = {obj.name for obj in created}
    for obj in list(bpy.data.objects):
        if obj.name not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    for _ in range(4):
        try:
            bpy.data.orphans_purge(do_recursive=True)
        except Exception as exc:  # pragma: no cover
            print("purge skipped", exc)
            break

    bpy.ops.object.select_all(action="DESELECT")
    for obj in created:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = created[0]

    out_path = os.path.join(MODELS, "original.glb")
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_normals=True,
        export_texcoords=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_extras=False,
        export_skins=False,
        export_morph=False,
    )

    total = sum(row["triangles"] for row in per_muscle)
    grouped = {}
    for row in per_muscle:
        prefix = row["id"].rsplit("_", 1)[0]
        grouped.setdefault(prefix, 0)
        grouped[prefix] += row["triangles"]

    payload = {}
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    payload["source"] = {
        "repo": "https://github.com/Z-Anatomy/Models-of-human-anatomy",
        "file": "Z-Anatomy/Startup.blend",
        "blendBytes": 306838281,
        "zipUrl": "https://github.com/Z-Anatomy/Models-of-human-anatomy/raw/refs/heads/master/Z-Anatomy.zip",
        "license": "CC BY-SA 4.0",
        "upstream": "BodyParts3D CC BY-SA 2.1 Japan",
        "note": "Rectus sheath collection exists but contains no mesh. Aponeuroses are the Tendon material on each muscle, not separate objects. Linea alba (338 tris) was left out of the decimation set.",
    }
    payload["census"] = census
    payload["original"] = {
        "triangles": total,
        "byMuscle": grouped,
        "objects": per_muscle,
        "glb": "models/original.glb",
        "glbBytes": os.path.getsize(out_path),
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("WROTE", out_path, os.path.getsize(out_path))
    print("TOTAL_TRIS", total)


if __name__ == "__main__":
    main()
