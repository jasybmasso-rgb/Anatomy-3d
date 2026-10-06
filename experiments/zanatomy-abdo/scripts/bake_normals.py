"""Bake tangent-space normal maps from the full mesh onto meshopt LODs.

  blender --background --python bake_normals.py -- --size 2048

Optional:
  --level meshopt-10
  --only external_l
  --size 256
"""

import array
import os
import struct
import sys
import time
import zlib

import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS = os.path.join(ROOT, "models")
NORMALS = os.path.join(MODELS, "normals")
HIGH = os.path.join(MODELS, "original.glb")
os.makedirs(NORMALS, exist_ok=True)

LEVELS = ["meshopt-10", "meshopt-05"]


def args_after_dd():
    if "--" not in sys.argv:
        return {}
    raw = sys.argv[sys.argv.index("--") + 1 :]
    out = {}
    i = 0
    while i < len(raw):
        if raw[i].startswith("--"):
            key = raw[i][2:]
            if i + 1 < len(raw) and not raw[i + 1].startswith("--"):
                out[key] = raw[i + 1]
                i += 2
            else:
                out[key] = True
                i += 1
        else:
            i += 1
    return out


def mesh_objects():
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def import_pair(low_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=HIGH)
    high = {}
    for obj in mesh_objects():
        obj.name = obj.name.split(".")[0] + "_HIGH"
        # import may suffix .001; the split above is wrong if the real name has no dot.
        high[obj.name] = obj
    # Re-key by stripping _HIGH and any blender suffix we just created.
    high = {}
    for obj in mesh_objects():
        base = obj.name[: -len("_HIGH")] if obj.name.endswith("_HIGH") else obj.name
        high[base] = obj
    bpy.ops.import_scene.gltf(filepath=low_path)
    low = {}
    for obj in mesh_objects():
        if obj.name.endswith("_HIGH") or "_HIGH." in obj.name:
            continue
        low[obj.name] = obj
    return high, low


def prepare_cycles(size):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    _ = size


def bake_object(high, low, image):
    # One temporary material so every face receives the same map.
    # This sequence matches a headless bake that actually fills the pixel buffer.
    saved_slots = [slot.material for slot in low.material_slots]
    saved_index = [poly.material_index for poly in low.data.polygons]

    bpy.ops.object.select_all(action="DESELECT")
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    if not low.data.uv_layers:
        low.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    low.data.calc_tangents(uvmap=low.data.uv_layers.active.name)

    bake_mat = bpy.data.materials.new(low.name + "_bake")
    bake_mat.use_nodes = True
    tex = bake_mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    bake_mat.node_tree.nodes.active = tex
    low.data.materials.clear()
    low.data.materials.append(bake_mat)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    bpy.ops.object.select_all(action="DESELECT")
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.bake(
        type="NORMAL",
        use_selected_to_active=True,
        cage_extrusion=0.004,
        max_ray_distance=0.03,
        normal_space="TANGENT",
        margin=16,
        use_clear=True,
    )
    # Reassigning the image to another material drops this buffer.
    # Snapshot first and write it back after the slots are restored.
    baked = array.array("f", [0.0]) * (image.size[0] * image.size[1] * 4)
    image.pixels.foreach_get(baked)

    # Restore the muscle / tendon slots and hook up the normal map.
    low.data.materials.clear()
    if not saved_slots:
        saved_slots = [bake_mat]
    for mat in saved_slots:
        if mat is None:
            continue
        attach_normal(mat, image)
        low.data.materials.append(mat)
    for poly, index in zip(low.data.polygons, saved_index):
        poly.material_index = min(index, max(0, len(low.data.materials) - 1))
    bpy.data.materials.remove(bake_mat)
    image.pixels.foreach_set(baked)
    image.update()


def attach_normal(mat, image):
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    # Drop a previous bake node if we re-run.
    for node in list(nodes):
        if node.type == "NORMAL_MAP" or (node.type == "TEX_IMAGE" and node.image == image):
            nodes.remove(node)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.image.colorspace_settings.name = "Non-Color"
    tex.location = (-500, -200)
    nmap = nodes.new("ShaderNodeNormalMap")
    nmap.location = (-200, -200)
    nmap.space = "TANGENT"
    links.new(tex.outputs["Color"], nmap.inputs["Color"])
    links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])


def export_low(low_objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in low_objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = low_objs[0]
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_normals=True,
        export_texcoords=True,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
    )


def write_png(path, width, height, rgba):
    """rgba is a float array, bottom-left origin, length width*height*4."""

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    rows = []
    stride = width * 4
    for y in range(height - 1, -1, -1):
        row = bytearray(1 + width * 3)
        base = y * stride
        for x in range(width):
            i = base + x * 4
            row[1 + x * 3] = int(max(0.0, min(1.0, rgba[i])) * 255 + 0.5)
            row[2 + x * 3] = int(max(0.0, min(1.0, rgba[i + 1])) * 255 + 0.5)
            row[3 + x * 3] = int(max(0.0, min(1.0, rgba[i + 2])) * 255 + 0.5)
        rows.append(row)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows), 6))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def image_stats(image):
    width, height = image.size
    # foreach_get returns a stale zero buffer right after a bake.
    # Copying the pixel sequence flushes it.
    buf = array.array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(buf)
    n = width * height
    # Sample every pixel; these maps are at most 2048^2.
    rs = gs = bs = 0.0
    r2 = g2 = b2 = 0.0
    used = 0
    for i in range(0, len(buf), 4):
        r, g, b, a = buf[i], buf[i + 1], buf[i + 2], buf[i + 3]
        if r + g + b < 0.02:
            continue
        used += 1
        rs += r
        gs += g
        bs += b
        r2 += r * r
        g2 += g * g
        b2 += b * b
    if not used:
        peak = max(buf) if buf else 0
        return buf, f"empty peak={peak:.3f}"
    inv = 1.0 / used
    mean = (rs * inv, gs * inv, bs * inv)
    var = (
        max(0.0, r2 * inv - mean[0] ** 2) ** 0.5,
        max(0.0, g2 * inv - mean[1] ** 2) ** 0.5,
        max(0.0, b2 * inv - mean[2] ** 2) ** 0.5,
    )
    return buf, f"used={used}/{n} mean={[round(v, 3) for v in mean]} std={[round(v, 3) for v in var]}"


def bake_level(level, size, only):
    low_path = os.path.join(MODELS, f"{level}.glb")
    high, low = import_pair(low_path)
    prepare_cycles(size)
    print("HIGH", sorted(high))
    print("LOW", sorted(low))
    images = {}
    for name, low_obj in sorted(low.items()):
        if only and name != only:
            continue
        high_obj = high.get(name)
        if high_obj is None:
            print("skip, no high", name)
            continue
        image = bpy.data.images.new(f"{level}_{name}", size, size, alpha=True)
        image.colorspace_settings.name = "Non-Color"
        t0 = time.time()
        bake_object(high_obj, low_obj, image)
        buf, stats = image_stats(image)
        png = os.path.join(NORMALS, f"{level}_{name}_{size}.png")
        write_png(png, size, size, buf)
        print(f"PIXELS {name} {stats} uv={len(low_obj.data.uv_layers)} faces={len(low_obj.data.polygons)}")
        images[name] = image
        print(f"BAKED {level} {name} {size} in {time.time() - t0:.1f}s -> {png}")

    if only:
        return

    out2k = os.path.join(MODELS, f"{level}-nm.glb")
    export_low(list(low.values()), out2k)
    print("WROTE", out2k, os.path.getsize(out2k))

    for image in images.values():
        image.scale(1024, 1024)
    out1k = os.path.join(MODELS, f"{level}-nm1k.glb")
    export_low(list(low.values()), out1k)
    print("WROTE", out1k, os.path.getsize(out1k))


def main():
    opt = args_after_dd()
    size = int(opt.get("size", 2048))
    only = opt.get("only")
    levels = [opt["level"]] if opt.get("level") else LEVELS
    for level in levels:
        bake_level(level, size, only)


if __name__ == "__main__":
    main()
