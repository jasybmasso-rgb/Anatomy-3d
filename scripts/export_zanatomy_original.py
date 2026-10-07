"""Export Z-Anatomy Startup.blend by system at authored resolution.

No decimation. Viewport modifiers that build the shape (mirror, solidify,
skin, subdivision at the authored level, booleans) are evaluated. The single
Decimate modifier and wireframe modifiers are left off. Curves (vessels,
peripheral nerves, ducts) become meshes at their bevel resolution.

Run:
  blender --background Startup.blend --python export_za_original.py
"""

import json
import os
import re
import sys
import time

import bmesh
import bpy
from mathutils import Vector

OUT = os.environ.get("ZANATOMY_OUT", "/tmp/za-export")
os.makedirs(OUT, exist_ok=True)

SKIP_SUFFIX = (".g", ".j", ".t", ".i")
MARKER = re.compile(r"\.[oe]\d*[lr]$", re.IGNORECASE)
CARTILAGE = ("cartilag", "meniscus", "intervertebral disc", "articular disc", "labrum")
LIGAMENT = ("ligament", "retinacul")
VESSEL_MESH = ("plexus", "vein", "vena", "arter", "aorta", "sinus")
SIZE_LIMIT = 95 * 1024 * 1024

COLORS = {
    "squelette": (0.86, 0.78, 0.66, 1.0),
    "cartilage": (0.70, 0.82, 0.88, 1.0),
    "muscles": (0.77, 0.28, 0.23, 1.0),
    "tendon": (0.96, 0.92, 0.84, 1.0),
    "ligaments": (0.91, 0.84, 0.68, 1.0),
    "nerfs": (0.93, 0.78, 0.22, 1.0),
    "vaisseaux": (0.72, 0.16, 0.18, 1.0),
    "veine": (0.22, 0.34, 0.72, 1.0),
    "organes": (0.78, 0.48, 0.50, 1.0),
}

LABELS = {
    "squelette": ("Squelette et cartilages", True),
    "muscles": ("Muscles", True),
    "ligaments": ("Ligaments", False),
    "nerfs": ("Nerfs", False),
    "vaisseaux": ("Vaisseaux", False),
    "organes": ("Organes", False),
}

MATS = {}
KEY_BOXES = {}
UNION = {}


def log(msg):
    print(msg, flush=True)


def has_word(name, words):
    n = name.lower()
    return any(w in n for w in words)


def mat_for(key):
    if key not in MATS:
        color = COLORS[key]
        mat = bpy.data.materials.new("ZA_" + key)
        mat.use_nodes = True
        mat.diffuse_color = color
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Roughness"].default_value = 0.55
            bsdf.inputs["Metallic"].default_value = 0.0
        MATS[key] = mat
    return MATS[key]


def paint(me, obj_name, system):
    vein = system == "vaisseaux" and has_word(obj_name, ("vein", "vena"))
    cartilage = system == "squelette" and has_word(obj_name, CARTILAGE)
    slots = list(me.materials)
    if not slots:
        me.materials.append(mat_for("cartilage" if cartilage else ("veine" if vein else system)))
        return
    for index, slot in enumerate(slots):
        src = slot.name.lower() if slot else ""
        if "tendon" in src:
            key = "tendon"
        elif vein:
            key = "veine"
        elif cartilage:
            key = "cartilage"
        else:
            key = system
        me.materials[index] = mat_for(key)


def tri_count(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def flip_normals(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()


def yup_box(me):
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    # glTF Y-up: X=X, Y=Z, Z=-Y
    return (min(xs), min(zs), -max(ys), max(xs), max(zs), -min(ys))


def union_box(a, b):
    if a is None:
        return b
    return (
        min(a[0], b[0]),
        min(a[1], b[1]),
        min(a[2], b[2]),
        max(a[3], b[3]),
        max(a[4], b[4]),
        max(a[5], b[5]),
    )


def remember(system, name, box):
    UNION[system] = union_box(UNION.get(system), box)
    lname = name.lower()
    keys = []
    if name.startswith("Deltoid muscle") or name.startswith("Scapula."):
        keys.append("epaule")
    if (
        "flexor digitorum superficialis" in lname
        or name.startswith("Radius.")
        or name.startswith("Scaphoid bone")
        or "abductor pollicis brevis" in lname
    ):
        keys.append("avant-bras")
    if name.startswith("Rectus abdominis muscle"):
        keys.append("abdomen")
    if (
        name in ("Frontal bone", "Mandible")
        or name.startswith("Orbicularis oculi")
        or "sternocleidomastoid" in lname
        or name.startswith("Hyoid")
    ):
        keys.append("face")
    if name.startswith("Patella"):
        keys.append("genou")
    if "tibial nerve" in lname or name.startswith("Femoral nerve"):
        keys.append("nerf-genou")
    for key in keys:
        KEY_BOXES[key] = union_box(KEY_BOXES.get(key), box)


def keep_object(obj):
    if obj.type not in ("MESH", "CURVE"):
        return False
    if obj.name.endswith(SKIP_SUFFIX):
        return False
    if MARKER.search(obj.name):
        return False
    if obj.type == "CURVE" and obj.data.bevel_depth <= 0 and obj.data.bevel_object is None:
        return False
    return True


def bake(obj, system):
    for mod in obj.modifiers:
        if mod.type in ("DECIMATE", "WIREFRAME"):
            mod.show_viewport = False
    src_name = obj.name
    obj.name = "__src__" + src_name
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    tmp = ev.to_mesh()
    me = tmp.copy()
    ev.to_mesh_clear()
    det = obj.matrix_world.determinant()
    me.transform(obj.matrix_world.copy())
    if det < 0:
        flip_normals(me)
    tris = tri_count(me)
    if tris < 12:
        bpy.data.meshes.remove(me)
        return None
    paint(me, src_name, system)
    me.name = src_name
    new_obj = bpy.data.objects.new(src_name, me)
    if new_obj.name != src_name:
        log(f"WARN name {src_name} -> {new_obj.name}")
    new_obj.matrix_world.identity()
    box = yup_box(me)
    center = Vector(((box[0] + box[3]) / 2, (box[1] + box[4]) / 2, (box[2] + box[5]) / 2))
    # centroid in blender Z-up for region splits: inverse of yup
    blender_c = Vector((center.x, -center.z, center.y))
    remember(system, src_name, box)
    return {"obj": new_obj, "name": src_name, "tris": tris, "center": blender_c, "box": box}


def collect():
    groups = {key: [] for key in LABELS}
    seen = set()

    def take(obj, system):
        if obj.as_pointer() in seen or not keep_object(obj):
            return
        seen.add(obj.as_pointer())
        groups[system].append(obj)

    skeletal = bpy.data.collections["1: Skeletal system"]
    joints = bpy.data.collections["3: Joints"]
    muscles = bpy.data.collections["4: Muscular system"]
    cardio = bpy.data.collections["5: Cardiovascular system"]
    lymph = bpy.data.collections["6: Lymphoid organs"]
    nerves = bpy.data.collections["7: Nervous system & Sense organs"]
    visceral = bpy.data.collections["8: Visceral systems"]

    for obj in skeletal.objects:
        take(obj, "squelette")
    for obj in joints.objects:
        if not keep_object(obj):
            continue
        take(obj, "squelette" if has_word(obj.name, CARTILAGE) else "ligaments")
    for obj in muscles.objects:
        if not keep_object(obj):
            continue
        take(obj, "ligaments" if has_word(obj.name, LIGAMENT) else "muscles")
    for obj in cardio.objects:
        if not keep_object(obj):
            continue
        if obj.type == "CURVE" or has_word(obj.name, VESSEL_MESH):
            take(obj, "vaisseaux")
        else:
            take(obj, "organes")
    for obj in nerves.objects:
        take(obj, "nerfs")
    for obj in list(lymph.objects) + list(visceral.objects):
        take(obj, "organes")
    return groups


def export_objects(records, path):
    scene = bpy.context.scene
    col = bpy.data.collections.new("ZA_EXPORT")
    scene.collection.children.link(col)
    for rec in records:
        col.objects.link(rec["obj"])
    bpy.ops.object.select_all(action="DESELECT")
    for rec in records:
        rec["obj"].select_set(True)
    bpy.context.view_layer.objects.active = records[0]["obj"]
    kwargs = dict(
        filepath=path,
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
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=16,
        export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12,
    )
    bpy.ops.export_scene.gltf(**kwargs)
    bpy.data.collections.remove(col)
    return os.path.getsize(path)


def free_records(records):
    for rec in records:
        me = rec["obj"].data
        bpy.data.objects.remove(rec["obj"], do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)


def region_of(center):
    x, _y, z = center.x, center.y, center.z
    if z >= 1.48:
        return "tete-cou"
    if abs(x) >= 0.22 and z >= 0.70:
        return "membre-sup"
    if z <= 0.82 and abs(x) >= 0.10:
        return "membre-inf"
    return "tronc"


def export_system(system, objects):
    log(f"BAKE {system} candidates={len(objects)}")
    t0 = time.time()
    records = []
    for index, obj in enumerate(objects):
        try:
            rec = bake(obj, system)
        except Exception as exc:  # noqa: BLE001 — keep going per the task
            log(f"SKIP {obj.name}: {exc}")
            continue
        if rec:
            records.append(rec)
        if index and index % 100 == 0:
            log(f"  {system} {index}/{len(objects)} kept={len(records)}")
    tris = sum(rec["tris"] for rec in records)
    log(f"BAKED {system} objects={len(records)} tris={tris} sec={time.time()-t0:.1f}")
    if not records:
        return {"id": system, "triangles": 0, "files": [], "objects": 0}

    files = []

    def write(subset, filename):
        path = os.path.join(OUT, filename)
        nbytes = export_objects(subset, path)
        part_tris = sum(rec["tris"] for rec in subset)
        log(f"WROTE {filename} bytes={nbytes} tris={part_tris} objects={len(subset)}")
        files.append(
            {
                "file": filename,
                "bytes": nbytes,
                "triangles": part_tris,
                "objects": len(subset),
            }
        )
        return nbytes

    filename = f"{system}.glb"
    nbytes = write(records, filename)
    if nbytes > SIZE_LIMIT:
        log(f"SPLIT {system} {nbytes} > {SIZE_LIMIT}")
        os.remove(os.path.join(OUT, filename))
        files.clear()
        buckets = {}
        for rec in records:
            buckets.setdefault(region_of(rec["center"]), []).append(rec)
        for region, subset in buckets.items():
            if not subset:
                continue
            write(subset, f"{system}-{region}.glb")
    free_records(records)
    return {
        "id": system,
        "triangles": sum(item["triangles"] for item in files),
        "objects": sum(item["objects"] for item in files),
        "files": files,
    }


def frame_from_box(box, direction, dist_scale):
    cx = (box[0] + box[3]) / 2
    cy = (box[1] + box[4]) / 2
    cz = (box[2] + box[5]) / 2
    size = max(box[3] - box[0], box[4] - box[1], box[5] - box[2], 0.08)
    dist = max(0.28, size * dist_scale)
    return {
        "eye": [
            round(cx + direction[0] * dist, 4),
            round(cy + direction[1] * dist, 4),
            round(cz + direction[2] * dist, 4),
        ],
        "target": [round(cx, 4), round(cy, 4), round(cz, 4)],
    }


def build_frames():
    frames = {}
    body = UNION.get("muscles") or UNION.get("squelette")
    if body:
        frames["corps-face"] = frame_from_box(body, (0.02, 0.04, 1.0), 1.35)
        frames["corps-dos"] = frame_from_box(body, (-0.02, 0.04, -1.0), 1.35)
    close = {
        "epaule": ((0.55, 0.15, 0.85), 1.6),
        "avant-bras": ((0.35, 0.05, 1.0), 1.5),
        "abdomen": ((0.15, 0.05, 1.0), 1.35),
        "face-cou": ((0.1, 0.05, 1.0), 1.45),
        "genou": ((0.45, 0.05, 0.9), 1.55),
    }
    # face key is the head box; the full-body front is also called face in French UI.
    # Keep anatomical close-up under face-cou.
    if "face" in KEY_BOXES:
        frames["face-cou"] = frame_from_box(KEY_BOXES["face"], *close["face-cou"])
    for key, spec in close.items():
        if key == "face-cou":
            continue
        if key in KEY_BOXES:
            frames[key] = frame_from_box(KEY_BOXES[key], *spec)
    if "epaule" in KEY_BOXES:
        frames["squelette"] = frame_from_box(KEY_BOXES["epaule"], (0.7, 0.2, 0.6), 1.35)
    elif "genou" in KEY_BOXES:
        frames["squelette"] = frame_from_box(KEY_BOXES["genou"], (0.5, 0.1, 0.85), 1.4)
    return frames


def main():
    groups = collect()
    for key, objs in groups.items():
        log(f"GROUP {key} {len(objs)}")
    systems = []
    for key in LABELS:
        systems.append(export_system(key, groups[key]))
    frames = build_frames()
    manifest_systems = []
    total_bytes = 0
    total_tris = 0
    for system in systems:
        label, default_on = LABELS[system["id"]]
        files = []
        for item in system["files"]:
            total_bytes += item["bytes"]
            files.append(
                {
                    "url": f"/models/zanatomy-original/{item['file']}",
                    "bytes": item["bytes"],
                    "triangles": item["triangles"],
                    "objects": item["objects"],
                }
            )
        total_tris += system["triangles"]
        manifest_systems.append(
            {
                "id": system["id"],
                "label": label,
                "defaultOn": default_on,
                "triangles": system["triangles"],
                "objects": system["objects"],
                "files": files,
            }
        )
    manifest = {
        "source": {
            "repo": "https://github.com/Z-Anatomy/Models-of-human-anatomy",
            "file": "Z-Anatomy/Startup.blend",
            "date": "2023-05-02",
            "license": "CC BY-SA 4.0",
            "authors": "Gauthier Kervyn, Marcin Zielinski",
            "upstream": "BodyParts3D, CC BY-SA 2.1 Japon",
        },
        "compression": {
            "method": "draco",
            "quantizePosition": 16,
            "quantizeNormal": 10,
            "quantizeTexcoord": 12,
            "decimated": False,
            "note": "Modificateurs de forme évalués (miroir, solidify, skin, subdivision au niveau d'affichage, booléens, biseau de courbes). Decimate et wireframe ignorés. Pas de décimation supplémentaire.",
        },
        "systems": manifest_systems,
        "totalTriangles": total_tris,
        "totalBytes": total_bytes,
        "frames": frames,
        "bounds": {key: list(box) for key, box in {**UNION, **KEY_BOXES}.items()},
    }
    path = os.path.join(OUT, "manifest.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    log(f"MANIFEST {path} tris={total_tris} bytes={total_bytes}")


if __name__ == "__main__":
    main()
