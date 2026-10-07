"""Move fascial envelopes out of the muscle and ligament GLBs.

The Draco bytes are copied unchanged: this does not decimate or requantize.
Run from the repo root:

  python3 scripts/split_zanatomy_fascia.py
"""

import json
import os
import struct

ROOT = os.path.join(os.path.dirname(__file__), "..", "public", "models", "zanatomy-original")

MUSCLE_COLOR = [0.70, 0.20, 0.16, 1.0]
TENDON_COLOR = [0.96, 0.93, 0.86, 1.0]
FASCIA_COLOR = [0.84, 0.73, 0.67, 1.0]


def is_envelope(name: str) -> bool:
    """Fascia, aponeurotic sheets, sheaths and retinacula — not muscle bellies."""
    n = name.lower()
    if n.startswith("tensor fasciae latae"):
        return False
    if "palmaris longus" in n or "interossei" in n or n.startswith("plantaris muscle"):
        return False
    if n.startswith("tendon of ") or n.startswith("calcaneal tendon"):
        return False
    if n == "linea alba":
        return True
    needles = (
        "fascia",
        "fascial",
        "aponeurosis",
        "iliotibial tract",
        "intermuscular septum",
        "tendon sheath",
        "synovial sheath",
        "fibrous sheath",
        "bursa",
        "retinacul",
        "investing",
    )
    return any(token in n for token in needles)


def read_glb(path):
    data = open(path, "rb").read()
    magic, version, _length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2:
        raise SystemExit(f"not a glb: {path}")
    json_len, json_type = struct.unpack_from("<I4s", data, 12)
    if json_type != b"JSON":
        raise SystemExit("missing JSON chunk")
    js = json.loads(data[20 : 20 + json_len])
    bin_off = 20 + json_len
    bin_len, bin_type = struct.unpack_from("<I4s", data, bin_off)
    if bin_type != b"BIN\x00":
        raise SystemExit("missing BIN chunk")
    blob = data[bin_off + 8 : bin_off + 8 + bin_len]
    return js, blob


def write_glb(path, js, blob):
    js_bytes = json.dumps(js, separators=(",", ":")).encode("utf-8")
    js_bytes += b" " * ((4 - len(js_bytes) % 4) % 4)
    blob += b"\x00" * ((4 - len(blob) % 4) % 4)
    total = 12 + 8 + len(js_bytes) + 8 + len(blob)
    out = struct.pack("<4sII", b"glTF", 2, total)
    out += struct.pack("<I4s", len(js_bytes), b"JSON") + js_bytes
    out += struct.pack("<I4s", len(blob), b"BIN\x00") + blob
    with open(path, "wb") as fh:
        fh.write(out)


def subset(js, blob, names):
    """Return a glTF document containing only the named nodes. Draco bytes are copied."""
    wanted = set(names)
    nodes = [node for node in js["nodes"] if node.get("name") in wanted]
    if len(nodes) != len(wanted):
        found = {node.get("name") for node in nodes}
        missing = sorted(wanted - found)
        raise SystemExit(f"missing nodes: {missing[:8]}")

    mesh_ids = []
    seen_mesh = set()
    for node in nodes:
        mesh_id = node["mesh"]
        if mesh_id not in seen_mesh:
            seen_mesh.add(mesh_id)
            mesh_ids.append(mesh_id)

    accessor_ids = []
    seen_acc = set()
    view_ids = []
    seen_view = set()
    material_ids = []
    seen_mat = set()

    def add_acc(index):
        if index not in seen_acc:
            seen_acc.add(index)
            accessor_ids.append(index)

    def add_view(index):
        if index not in seen_view:
            seen_view.add(index)
            view_ids.append(index)

    def add_mat(index):
        if index not in seen_mat:
            seen_mat.add(index)
            material_ids.append(index)

    for mesh_id in mesh_ids:
        for prim in js["meshes"][mesh_id]["primitives"]:
            for accessor in prim.get("attributes", {}).values():
                add_acc(accessor)
            if "indices" in prim:
                add_acc(prim["indices"])
            if "material" in prim:
                add_mat(prim["material"])
            draco = prim.get("extensions", {}).get("KHR_draco_mesh_compression")
            if draco:
                add_view(draco["bufferView"])

    acc_map = {old: new for new, old in enumerate(accessor_ids)}
    view_map = {old: new for new, old in enumerate(view_ids)}
    mesh_map = {old: new for new, old in enumerate(mesh_ids)}
    mat_map = {old: new for new, old in enumerate(material_ids)}

    new_bin = bytearray()
    new_views = []
    for old in view_ids:
        view = js["bufferViews"][old]
        start = view.get("byteOffset", 0)
        chunk = blob[start : start + view["byteLength"]]
        if len(chunk) != view["byteLength"]:
            raise SystemExit("bufferView out of range")
        pad = (4 - len(new_bin) % 4) % 4
        new_bin += b"\x00" * pad
        copied = dict(view)
        copied["buffer"] = 0
        copied["byteOffset"] = len(new_bin)
        new_bin += chunk
        new_views.append(copied)

    new_meshes = []
    for old in mesh_ids:
        mesh = json.loads(json.dumps(js["meshes"][old]))
        for prim in mesh["primitives"]:
            prim["attributes"] = {key: acc_map[value] for key, value in prim["attributes"].items()}
            if "indices" in prim:
                prim["indices"] = acc_map[prim["indices"]]
            if "material" in prim:
                prim["material"] = mat_map[prim["material"]]
            draco = prim.get("extensions", {}).get("KHR_draco_mesh_compression")
            if draco:
                draco["bufferView"] = view_map[draco["bufferView"]]
        new_meshes.append(mesh)

    new_nodes = []
    for node in nodes:
        copied = {"mesh": mesh_map[node["mesh"]], "name": node["name"]}
        new_nodes.append(copied)

    out = {
        "asset": js.get("asset", {"version": "2.0"}),
        "extensionsUsed": ["KHR_draco_mesh_compression"],
        "extensionsRequired": ["KHR_draco_mesh_compression"],
        "scene": 0,
        "scenes": [{"name": "Scene", "nodes": list(range(len(new_nodes)))}],
        "nodes": new_nodes,
        "materials": [js["materials"][index] for index in material_ids],
        "meshes": new_meshes,
        "accessors": [js["accessors"][index] for index in accessor_ids],
        "bufferViews": new_views,
        "buffers": [{"byteLength": len(new_bin)}],
    }
    return out, bytes(new_bin)


def merge_docs(parts):
    """Concatenate already-subset documents. Draco bytes stay intact."""
    nodes = []
    meshes = []
    materials = []
    accessors = []
    views = []
    blob = bytearray()
    for js, part_blob in parts:
        node_base = len(nodes)
        mesh_base = len(meshes)
        mat_base = len(materials)
        acc_base = len(accessors)
        view_base = len(views)
        pad = (4 - len(blob) % 4) % 4
        blob += b"\x00" * pad
        bin_base = len(blob)
        blob += part_blob
        for view in js["bufferViews"]:
            copied = dict(view)
            copied["byteOffset"] = bin_base + view.get("byteOffset", 0)
            copied["buffer"] = 0
            views.append(copied)
        accessors.extend(js["accessors"])
        for mesh in js["meshes"]:
            copied = json.loads(json.dumps(mesh))
            for prim in copied["primitives"]:
                prim["attributes"] = {key: acc_base + value for key, value in prim["attributes"].items()}
                if "indices" in prim:
                    prim["indices"] = acc_base + prim["indices"]
                if "material" in prim:
                    prim["material"] = mat_base + prim["material"]
                draco = prim.get("extensions", {}).get("KHR_draco_mesh_compression")
                if draco:
                    draco["bufferView"] = view_base + draco["bufferView"]
            meshes.append(copied)
        for node in js["nodes"]:
            nodes.append({"mesh": mesh_base + node["mesh"], "name": node["name"]})
        materials.extend(js["materials"])
        _ = node_base
    out = {
        "asset": {"version": "2.0", "generator": "split_zanatomy_fascia.py"},
        "extensionsUsed": ["KHR_draco_mesh_compression"],
        "extensionsRequired": ["KHR_draco_mesh_compression"],
        "scene": 0,
        "scenes": [{"name": "Scene", "nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "materials": materials,
        "meshes": meshes,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(blob)}],
    }
    return out, bytes(blob)


def paint(js, name, color, roughness):
    for material in js["materials"]:
        if material.get("name") != name:
            continue
        pbr = material.setdefault("pbrMetallicRoughness", {})
        pbr["baseColorFactor"] = color
        pbr["metallicFactor"] = 0
        pbr["roughnessFactor"] = roughness


def force_fascia_material(js):
    js["materials"] = [
        {
            "doubleSided": True,
            "name": "ZA_fascias",
            "pbrMetallicRoughness": {
                "baseColorFactor": FASCIA_COLOR,
                "metallicFactor": 0,
                "roughnessFactor": 0.78,
            },
        }
    ]
    for mesh in js["meshes"]:
        for prim in mesh["primitives"]:
            prim["material"] = 0


def triangles(js):
    total = 0
    accessors = js["accessors"]
    for mesh in js["meshes"]:
        for prim in mesh["primitives"]:
            if "indices" in prim:
                total += accessors[prim["indices"]]["count"] // 3
    return total


def names_where(js, predicate):
    return [node["name"] for node in js["nodes"] if predicate(node.get("name", ""))]


def main():
    muscles_js, muscles_bin = read_glb(os.path.join(ROOT, "muscles.glb"))
    ligaments_js, ligaments_bin = read_glb(os.path.join(ROOT, "ligaments.glb"))

    muscle_fascia = names_where(muscles_js, is_envelope)
    ligament_fascia = names_where(ligaments_js, is_envelope)
    muscle_keep = [node["name"] for node in muscles_js["nodes"] if node["name"] not in set(muscle_fascia)]
    ligament_keep = [node["name"] for node in ligaments_js["nodes"] if node["name"] not in set(ligament_fascia)]

    muscles_out, muscles_blob = subset(muscles_js, muscles_bin, muscle_keep)
    paint(muscles_out, "ZA_muscles", MUSCLE_COLOR, 0.64)
    paint(muscles_out, "ZA_tendon", TENDON_COLOR, 0.74)

    fascia_parts = []
    if muscle_fascia:
        part_js, part_bin = subset(muscles_js, muscles_bin, muscle_fascia)
        force_fascia_material(part_js)
        fascia_parts.append((part_js, part_bin))
    if ligament_fascia:
        part_js, part_bin = subset(ligaments_js, ligaments_bin, ligament_fascia)
        force_fascia_material(part_js)
        fascia_parts.append((part_js, part_bin))
    fascia_js, fascia_blob = merge_docs(fascia_parts)

    ligaments_out, ligaments_blob = subset(ligaments_js, ligaments_bin, ligament_keep)

    write_glb(os.path.join(ROOT, "muscles.glb"), muscles_out, muscles_blob)
    write_glb(os.path.join(ROOT, "fascias.glb"), fascia_js, fascia_blob)
    write_glb(os.path.join(ROOT, "ligaments.glb"), ligaments_out, ligaments_blob)

    manifest_path = os.path.join(ROOT, "manifest.json")
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    by_id = {system["id"]: system for system in manifest["systems"]}

    def file_info(filename, js):
        path = os.path.join(ROOT, filename)
        return {
            "url": f"/models/zanatomy-original/{filename}",
            "bytes": os.path.getsize(path),
            "triangles": triangles(js),
            "objects": len(js["nodes"]),
        }

    muscle_file = file_info("muscles.glb", muscles_out)
    fascia_file = file_info("fascias.glb", fascia_js)
    ligament_file = file_info("ligaments.glb", ligaments_out)
    by_id["muscles"]["files"] = [muscle_file]
    by_id["muscles"]["triangles"] = muscle_file["triangles"]
    by_id["muscles"]["objects"] = muscle_file["objects"]
    by_id["ligaments"]["files"] = [ligament_file]
    by_id["ligaments"]["triangles"] = ligament_file["triangles"]
    by_id["ligaments"]["objects"] = ligament_file["objects"]
    fascia_system = {
        "id": "fascias",
        "label": "Fascias",
        "defaultOn": False,
        "triangles": fascia_file["triangles"],
        "objects": fascia_file["objects"],
        "files": [fascia_file],
    }
    systems = []
    inserted = False
    for system in manifest["systems"]:
        if system["id"] == "fascias":
            continue
        systems.append(system)
        if system["id"] == "muscles":
            systems.append(fascia_system)
            inserted = True
    if not inserted:
        systems.append(fascia_system)
    manifest["systems"] = systems
    manifest["totalTriangles"] = sum(system["triangles"] for system in systems)
    manifest["totalBytes"] = sum(item["bytes"] for system in systems for item in system["files"])
    note = manifest.get("compression", {}).get("note", "")
    extra = " Les fascias, aponévroses d'enveloppe, gaines et rétinaculums sont dans fascias.glb, pas dans les muscles."
    if "fascias.glb" not in note:
        manifest["compression"]["note"] = note + extra
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")

    print(f"muscles objects={muscle_file['objects']} tris={muscle_file['triangles']} bytes={muscle_file['bytes']}")
    print(f"fascias objects={fascia_file['objects']} tris={fascia_file['triangles']} bytes={fascia_file['bytes']}")
    print(f"ligaments objects={ligament_file['objects']} tris={ligament_file['triangles']} bytes={ligament_file['bytes']}")
    print(f"total tris={manifest['totalTriangles']} bytes={manifest['totalBytes']}")
    print(f"moved from muscles: {len(muscle_fascia)}; from ligaments: {len(ligament_fascia)}")


if __name__ == "__main__":
    main()
