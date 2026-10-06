"""Blender Decimate (collapse) of models/original.glb at 25%, 10% and 5%.

Run:
  blender --background --python decimate_blender.py

The collapse modifier has no border lock. These meshes are closed, so this is
the plain collapse the Blender UI would apply. UVs do not exist on the source.
"""

import json
import os

import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "models", "original.glb")
MODELS = os.path.join(ROOT, "models")
METRICS = os.path.join(ROOT, "metrics.json")
RATIOS = [("decimate-25", 0.25), ("decimate-10", 0.10), ("decimate-05", 0.05)]


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_source():
    bpy.ops.import_scene.gltf(filepath=SRC)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise SystemExit("no meshes in original.glb")
    return meshes


def tri_count(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def export_ratio(ratio, out_path):
    clear_scene()
    sources = import_source()
    before = 0
    after = 0
    per = {}
    for obj in sources:
        before += tri_count(obj)
        mod = obj.modifiers.new("Decimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        if hasattr(mod, "use_collapse_triangulate"):
            mod.use_collapse_triangulate = True
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        tris = tri_count(obj)
        after += tris
        per[obj.name] = tris
    bpy.ops.object.select_all(action="SELECT")
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
    )
    return {
        "trianglesBefore": before,
        "triangles": after,
        "percentOfOriginal": round(100.0 * after / before, 2),
        "perMesh": per,
        "glbBytes": os.path.getsize(out_path),
    }


def main():
    results = []
    for name, ratio in RATIOS:
        out = os.path.join(MODELS, f"{name}.glb")
        stats = export_ratio(ratio, out)
        stats.update(
            {
                "id": name,
                "method": "Blender Decimate collapse",
                "requestedRatio": ratio,
                "glb": f"models/{name}.glb",
            }
        )
        print(f"{name} tris={stats['triangles']} ({stats['percentOfOriginal']}%) bytes={stats['glbBytes']}")
        results.append(stats)

    payload = {}
    if os.path.exists(METRICS):
        with open(METRICS, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    payload["decimate"] = results
    with open(METRICS, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


if __name__ == "__main__":
    main()
