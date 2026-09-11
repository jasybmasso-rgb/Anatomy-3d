#!/usr/bin/env python3
"""Replace synthetic-v2 meshes in nerves.glb without re-downloading BodyParts3D."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import trimesh
from trimesh.exchange.gltf import export_glb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_synthetic_nerves import NERVE_RGB, build

NERVE_INCLUSION = (
    "Nerfs crâniens / orbitaires BodyParts3D 4.0 (optique, trochléaire, oculomoteur, "
    "ophtalmique, ciliaires). Les grands troncs périphériques (plexus brachial, "
    "médian, ulnaire, radial, sciatique, fémoral, tibial, fibulaire, phrénique…) "
    "sont des tubes schématiques synthetic-v2 plus fins, calés sur le trajet usuel : "
    "BP3D 4.0 n’a pas ces maillages."
)

ROOT = Path(__file__).resolve().parents[1]
GLB = ROOT / "public" / "models" / "nerves.glb"
META = ROOT / "public" / "models" / "nerves.meta.json"
CATALOG = ROOT / "src" / "data" / "nerves.json"


def main() -> int:
    if not GLB.exists():
        print("missing nerves.glb", file=sys.stderr)
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
        mesh.visual.vertex_colors = NERVE_RGB
        _ = mesh.vertex_normals
        mesh.metadata["name"] = part_id
        scene.add_geometry(mesh, node_name=part_id, geom_name=part_id)

    GLB.write_bytes(export_glb(scene, include_normals=True))
    size_mb = GLB.stat().st_size / (1024 * 1024)

    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    kept = [row for row in payload["nerves"] if not str(row.get("source", "")).startswith("synthetic")]
    catalog = kept + synth_catalog
    n_bp3d = sum(1 for p in catalog if p.get("source") == "bodyparts3d")
    n_synth = sum(1 for p in catalog if str(p.get("source", "")).startswith("synthetic"))
    payload.update(
        {
            "inclusionRules": NERVE_INCLUSION,
            "syntheticDisclaimer": (
                "Les pièces source=synthetic-v2 sont des tubes loftés le long du "
                "trajet anatomique usuel (repères osseux), pas des nerfs segmentés. "
                "Les maillages crâniens BP3D restent source=bodyparts3d."
            ),
            "count": len(catalog),
            "countBodyparts3d": n_bp3d,
            "countSynthetic": n_synth,
            "nerves": catalog,
        }
    )
    CATALOG.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    meta = json.loads(META.read_text(encoding="utf-8")) if META.exists() else {}
    meta.update(
        {
            "glbBytes": GLB.stat().st_size,
            "glbMiB": round(size_mb, 2),
            "partCount": len(catalog),
            "countBodyparts3d": n_bp3d,
            "countSynthetic": n_synth,
            "alignedTo": "public/models/skeleton.glb",
            "inclusionRules": NERVE_INCLUSION,
        }
    )
    META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {GLB} ({size_mb:.2f} MiB), {len(catalog)} parts ({n_bp3d} BP3D + {n_synth} synthetic-v2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
