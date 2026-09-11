#!/usr/bin/env python3
"""Replace / append synthetic fascia in fascia.glb without re-downloading BP3D."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import trimesh
from trimesh.exchange.gltf import export_glb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_synthetic_fascia import NOTE, build  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GLB = ROOT / "public" / "models" / "fascia.glb"
META = ROOT / "public" / "models" / "fascia.meta.json"
CATALOG = ROOT / "src" / "data" / "fascia.json"

INCLUSION = (
    "Included from BodyParts3D: named iliotibial tract meshes (FJ1423 / FJ1423M). "
    "Fascia lata, crural fascia, thoracolumbar fascia, nuchal ligament and "
    "sacrotuberous ligaments are schematic (source=synthetic-v2)."
)


def main() -> int:
    if not GLB.exists():
        print("missing fascia.glb", file=sys.stderr)
        return 1
    scene = trimesh.load(GLB, force="scene")
    synth_meshes, synth_catalog = build()
    by_id = {part_id: mesh for part_id, mesh in synth_meshes}
    existing = list(scene.geometry.keys())
    for name in existing:
        if name in by_id:
            scene.delete_geometry(name)
    for part_id, mesh in synth_meshes:
        _ = mesh.vertex_normals
        mesh.visual.vertex_colors = [155, 182, 200, 180]
        mesh.metadata["name"] = part_id
        scene.add_geometry(mesh, node_name=part_id, geom_name=part_id)
        print(f"  + {part_id:32s}  {len(mesh.faces):6d} faces  synthetic-v2", flush=True)

    GLB.write_bytes(export_glb(scene, include_normals=True))
    size_mb = GLB.stat().st_size / (1024 * 1024)

    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    kept = [row for row in payload["fascia"] if not str(row.get("source", "")).startswith("synthetic")]
    catalog = kept + synth_catalog
    n_bp3d = sum(1 for p in catalog if p.get("source") == "bodyparts3d")
    n_synth = sum(1 for p in catalog if str(p.get("source", "")).startswith("synthetic"))
    payload.update(
        {
            "inclusionRules": INCLUSION,
            "syntheticDisclaimer": NOTE,
            "count": len(catalog),
            "countBodyparts3d": n_bp3d,
            "countSynthetic": n_synth,
            "fascia": catalog,
        }
    )
    gaps = payload.get("gaps") or []
    payload["gaps"] = [g for g in gaps if "nuchal" not in g.lower() and "nuchal" not in g]
    CATALOG.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    meta = json.loads(META.read_text(encoding="utf-8")) if META.exists() else {}
    meta.update(
        {
            "glbBytes": GLB.stat().st_size,
            "glbMiB": round(size_mb, 2),
            "partCount": len(catalog),
            "countBodyparts3d": n_bp3d,
            "countSynthetic": n_synth,
            "inclusionRules": INCLUSION,
        }
    )
    META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {GLB} ({size_mb:.2f} MiB), {len(catalog)} fascia ({n_bp3d} BP3D + {n_synth} synthetic)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
