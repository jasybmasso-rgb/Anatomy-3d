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
    enhance_external_oblique,
    load_lm,
)
from muscle_catalog import catalog_entry  # noqa: E402

INCLUSION = (
    INCLUSION_RULES
    + " Temporalis, masseter and pterygoids are landmark-anchored synthetics "
    "(BP3D 4.0 excludes facial / mastication meshes from this atlas). "
    "Internal oblique and transversus abdominis are nested synthetic sheets "
    "(transversus deep → internal oblique → external oblique; rectus in the sheath). "
    "External oblique keeps the BP3D fleshy belly plus a white aponeurosis over rectus."
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
    return muscle, entry


def main() -> int:
    if not OUT_GLB.exists():
        print("missing muscles.glb", file=sys.stderr)
        return 1
    scene = trimesh.load(OUT_GLB, force="scene")
    landmarks = load_lm()
    synth = build()
    eo_mesh = None
    if "oblique-externe" in scene.geometry:
        eo_mesh = enhance_external_oblique(scene.geometry["oblique-externe"], landmarks)
        _ = eo_mesh.vertex_normals
        eo_mesh.metadata["name"] = "oblique-externe"
        scene.delete_geometry("oblique-externe")
        scene.add_geometry(eo_mesh, node_name="oblique-externe", geom_name="oblique-externe")
        print(f"  + {'oblique-externe':32s}  {len(eo_mesh.faces):6d} faces  BP3D+aponeurosis", flush=True)
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

    if eo_mesh is not None and "oblique-externe" in mesh_by_id:
        mesh_by_id["oblique-externe"].update(
            {
                "vertexCount": int(len(eo_mesh.vertices)),
                "faceCount": int(len(eo_mesh.faces)),
                "notes": (
                    "BodyParts3D fleshy belly plus schematic white aponeurosis "
                    "passing superficial to rectus (anterior sheath)."
                ),
            }
        )

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
