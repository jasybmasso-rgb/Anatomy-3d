#!/usr/bin/env python3
"""Remove nasal cartilage from skeleton.glb without re-downloading BodyParts3D.

The cartilage node is a merged mesh (costal + IVD + laryngeal + nasal).
Nasal pieces sit on the midface (high Y, high Z, near the midline) and are
stripped by vertex region so costal / laryngeal cartilage stay.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from trimesh.exchange.gltf import export_glb

ROOT = Path(__file__).resolve().parents[1]
GLB = ROOT / "public" / "models" / "skeleton.glb"
META = ROOT / "public" / "models" / "skeleton.meta.json"

NASAL_CONCEPTS = {
    "septal nasal cartilage",
    "right major alar cartilage",
    "left major alar cartilage",
    "right lateral nasal cartilage",
    "left lateral nasal cartilage",
}


def is_nasal_vertex(v: np.ndarray) -> np.ndarray:
    """Midface cartilage only — not thyroid / costal."""
    return (v[:, 1] > 0.605) & (v[:, 2] > 0.105) & (np.abs(v[:, 0]) < 0.040)


def main() -> int:
    if not GLB.exists():
        print("missing skeleton.glb", file=sys.stderr)
        return 1
    scene = trimesh.load(GLB, force="scene")
    cart = scene.geometry.get("cartilage")
    if cart is None:
        print("no cartilage node", file=sys.stderr)
        return 1
    v = np.asarray(cart.vertices)
    faces = np.asarray(cart.faces)
    nasal = is_nasal_vertex(v)
    keep_face = ~nasal[faces].any(axis=1)
    n_drop_v = int(nasal.sum())
    n_drop_f = int((~keep_face).sum())
    if n_drop_f == 0:
        print("no nasal faces found — already stripped?")
        return 0
    trimmed = trimesh.Trimesh(vertices=v, faces=faces[keep_face], process=False)
    trimmed.remove_unreferenced_vertices()
    trimmed.update_faces(trimmed.nondegenerate_faces())
    trimmed.visual.vertex_colors = [185, 212, 228, 190]
    _ = trimmed.vertex_normals
    trimmed.metadata["name"] = "cartilage"
    scene.delete_geometry("cartilage")
    scene.add_geometry(trimmed, node_name="cartilage", geom_name="cartilage")
    GLB.write_bytes(export_glb(scene, include_normals=True))

    if META.exists():
        meta = json.loads(META.read_text(encoding="utf-8"))
        concepts = [c for c in meta.get("cartilageConcepts", []) if c not in NASAL_CONCEPTS]
        meta["cartilageConcepts"] = concepts
        meta["cartilageCount"] = int(meta.get("cartilageCount", 0)) - len(NASAL_CONCEPTS)
        if meta["cartilageCount"] < 0:
            meta["cartilageCount"] = len(concepts)
        meta["nasalCartilage"] = "stripped"
        meta["glbBytes"] = GLB.stat().st_size
        meta["glbMiB"] = round(GLB.stat().st_size / (1024 * 1024), 2)
        META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(
        f"stripped {n_drop_v} nasal verts / {n_drop_f} faces; "
        f"kept {len(trimmed.vertices)} verts / {len(trimmed.faces)} faces"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
