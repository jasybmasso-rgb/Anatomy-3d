#!/usr/bin/env python3
"""Replace synthetic-v2 meshes in ligaments.glb without re-downloading BodyParts3D."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import trimesh
from trimesh.exchange.gltf import export_glb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_synthetic_ligaments import build

ROOT = Path(__file__).resolve().parents[1]
GLB = ROOT / "public" / "models" / "ligaments.glb"
META = ROOT / "public" / "models" / "ligaments.meta.json"
CATALOG = ROOT / "src" / "data" / "ligaments.json"

INCLUSION_RULES = (
    "Included from BodyParts3D: named ligaments, interosseous membranes "
    "(syndesmoses) and flexor retinacula. "
    "Excluded: calcaneal tendons, extraocular check ligaments, lens zonules, "
    "trochleae, abstract parents. Crude capsule/stick synthetics (v1) and "
    "rectangular lofted ribbons are not exported. Missing major ligaments of "
    "knee, hip, shoulder, elbow and ankle are schematic tapered fascicle bundles "
    "(flared fascicles that blend onto bone, no mushroom caps; "
    "source=synthetic-v3), not cadaver meshes. Annular ligament "
    "of the radius is a torus. Spinal stick ligaments and menisci are omitted "
    "(quality > quantity)."
)


def main() -> int:
    if not GLB.exists():
        print("missing ligaments.glb", file=sys.stderr)
        return 1
    scene = trimesh.load(GLB, force="scene")
    synth_meshes, synth_catalog = build()
    by_id = {part_id: mesh for part_id, mesh in synth_meshes}
    if not by_id:
        print("no synthetic meshes", file=sys.stderr)
        return 1

    existing = list(scene.geometry.keys())
    for name in existing:
        if name in by_id:
            scene.delete_geometry(name)
    for part_id, mesh in synth_meshes:
        mesh.visual.vertex_colors = [210, 120, 36, 200]
        _ = mesh.vertex_normals
        mesh.metadata["name"] = part_id
        scene.add_geometry(mesh, node_name=part_id, geom_name=part_id)

    GLB.write_bytes(export_glb(scene, include_normals=True))
    size_mb = GLB.stat().st_size / (1024 * 1024)

    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    kept = [row for row in payload["ligaments"] if not str(row.get("source", "")).startswith("synthetic")]
    catalog = kept + synth_catalog
    n_bp3d = sum(1 for p in catalog if p.get("source") == "bodyparts3d")
    n_synth = sum(1 for p in catalog if str(p.get("source", "")).startswith("synthetic"))
    payload.update(
        {
            "inclusionRules": INCLUSION_RULES,
            "syntheticDisclaimer": (
                "Entries with source=synthetic-v3 are schematic fascicle "
                "bundles (lofted strands that flare onto bone, no bulbous caps) "
                "between named landmarks. They are not segmented from cadaver "
                "imaging and must not be treated as morphologically accurate. "
                "BodyParts3D connective meshes (interosseous membranes, "
                "retinacula, named ligaments) remain source=bodyparts3d."
            ),
            "count": len(catalog),
            "countBodyparts3d": n_bp3d,
            "countSynthetic": n_synth,
            "ligaments": catalog,
        }
    )
    CATALOG.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    meta = {
        "glbBytes": GLB.stat().st_size,
        "glbMiB": round(size_mb, 2),
        "partCount": len(catalog),
        "countBodyparts3d": n_bp3d,
        "countSynthetic": n_synth,
        "license": "CC BY-SA 2.1 Japan (BP3D meshes); synthetic-v2 fascicle bundles are original educational approximations",
        "alignedTo": "public/models/skeleton.glb",
        "inclusionRules": INCLUSION_RULES,
    }
    META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {GLB} ({size_mb:.2f} MiB), {len(catalog)} parts ({n_bp3d} BP3D + {n_synth} synthetic)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
