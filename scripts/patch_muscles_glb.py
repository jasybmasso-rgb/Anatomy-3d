#!/usr/bin/env python3
"""Replace / append synthetic muscles in muscles.glb without re-downloading BP3D."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import trimesh
from trimesh.exchange.gltf import export_glb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_muscles_glb import (  # noqa: E402
    INCLUSION_RULES,
    MAX_GLB_MIB,
    MUSCLES_JSON,
    OUT_CATALOG,
    OUT_GLB,
    OUT_META,
    _catalog_row,
)
from build_synthetic_muscles import (  # noqa: E402
    SYNTH_KEYS,
    SYNTH_NOTES,
    build,
    load_lm,
)

_FIBER_AXIS_OVERRIDE = {
    "transverse-de-l-abdomen": [1.0, 0.04, 0.02],
    "oblique-interne": [0.0, 0.92, 0.18],
    "oblique-externe": [0.0, -0.92, 0.18],
    "droit-abdomen": [0.0, 0.98, 0.18],
    "grand-dorsal": [0.0, 0.88, 0.28],
}
from muscle_catalog import catalog_entry  # noqa: E402

INCLUSION = (
    INCLUSION_RULES
    + " Temporalis, masseter and pterygoids are landmark-anchored synthetics "
    "(BP3D 4.0 excludes facial / mastication meshes from this atlas). "
    "Internal / external oblique and transversus are nested synthetic sheets "
    "(transversus deep → internal oblique → rectus in the sheath → external oblique "
    "with rib digitations and a white aponeurosis staying superficial). "
    "Latissimus is a T7–L5 fan with a white thoracolumbar origin."
)


def _muscle_row(muscle_id: str, mesh: trimesh.Trimesh) -> dict:
    entry = _catalog_row(muscle_id, "synthetic", [muscle_id], [], [], mesh, notes=SYNTH_NOTES)
    key = SYNTH_KEYS.get(muscle_id, muscle_id)
    text = catalog_entry(key, [])
    muscle = {
        "id": muscle_id,
        **text,
        "focus": entry["focus"],
        "fiberAxis": entry["fiberAxis"],
        "meshSource": "synthetic",
    }
    if muscle.get("heads") is None:
        muscle.pop("heads", None)
    if not muscle.get("secondaryActions"):
        muscle.pop("secondaryActions", None)
    axis = _FIBER_AXIS_OVERRIDE.get(muscle_id)
    if axis:
        muscle["fiberAxis"] = axis
        entry["fiberAxis"] = axis
    return muscle, entry


def main() -> int:
    if not OUT_GLB.exists():
        print("missing muscles.glb", file=sys.stderr)
        return 1
    scene = trimesh.load(OUT_GLB, force="scene")
    _ = load_lm()
    synth = build()
    for muscle_id, mesh in synth.items():
        _ = mesh.vertex_normals
        if getattr(mesh.visual, "vertex_colors", None) is None or len(getattr(mesh.visual, "vertex_colors", [])) == 0:
            mesh.visual.vertex_colors = [196, 72, 58, 255]
        mesh.metadata["name"] = muscle_id
        if muscle_id in scene.geometry:
            scene.delete_geometry(muscle_id)
        scene.add_geometry(mesh, node_name=muscle_id, geom_name=muscle_id)
        print(f"  + {muscle_id:32s}  {len(mesh.faces):6d} faces  synthetic", flush=True)

    OUT_GLB.write_bytes(export_glb(scene, include_normals=True))
    size_mb = OUT_GLB.stat().st_size / (1024 * 1024)
    if size_mb > MAX_GLB_MIB:
        print(f"warning: GLB {size_mb:.2f} MiB exceeds {MAX_GLB_MIB}", file=sys.stderr)

    muscles = json.loads(MUSCLES_JSON.read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in muscles}
    mesh_cat = json.loads(OUT_CATALOG.read_text(encoding="utf-8"))
    mesh_by_id = {row["id"]: row for row in mesh_cat["muscles"]}

    for muscle_id, mesh in synth.items():
        muscle, entry = _muscle_row(muscle_id, mesh)
        by_id[muscle_id] = muscle
        mesh_by_id[muscle_id] = entry

    muscles_out = sorted(by_id.values(), key=lambda m: m["name"].lower())
    catalog = sorted(mesh_by_id.values(), key=lambda m: m["id"])
    n_bp3d = sum(1 for p in catalog if p.get("source") == "bodyparts3d")
    n_synth = sum(1 for p in catalog if p.get("source") == "synthetic")

    MUSCLES_JSON.write_text(json.dumps(muscles_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    mesh_cat.update(
        {
            "inclusionRules": INCLUSION,
            "count": len(catalog),
            "countBodyparts3d": n_bp3d,
            "countSynthetic": n_synth,
            "muscles": catalog,
        }
    )
    OUT_CATALOG.write_text(json.dumps(mesh_cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    meta = json.loads(OUT_META.read_text(encoding="utf-8")) if OUT_META.exists() else {}
    meta.update(
        {
            "glbBytes": OUT_GLB.stat().st_size,
            "glbMiB": round(size_mb, 2),
            "partCount": len(catalog),
            "countBodyparts3d": n_bp3d,
            "countSynthetic": n_synth,
            "inclusionRules": INCLUSION,
        }
    )
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_GLB} ({size_mb:.2f} MiB), {len(catalog)} muscles ({n_bp3d} BP3D + {n_synth} synthetic)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
