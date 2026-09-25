#!/usr/bin/env python3
"""Replace / append synthetic muscles in muscles.glb without re-downloading BP3D."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
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
    # Patient-right inferomedial (hands-in-pockets). +X is toward the midline;
    # applyFiberUVs mirrors X on the left half.
    "oblique-externe": [0.55, -0.72, 0.42],
    "droit-abdomen": [0.0, 0.98, 0.18],
    "grand-dorsal": [0.0, 0.88, 0.28],
}
from muscle_catalog import catalog_entry  # noqa: E402

INCLUSION = (
    INCLUSION_RULES
    + " Temporalis, masseter and pterygoids are landmark-anchored synthetics "
    "(BP3D 4.0 excludes facial / mastication meshes from this atlas). "
    "Internal / external oblique keep fleshy fibers plus a translucent aponeurosis "
    "(anterior / posterior rectus sheath). Transversus is a horizontal-fiber corset "
    "(iliac / inguinal / costal / TLF) with a tendinous medial sheath. "
    "Latissimus is a T7–L5 fan sitting posterior to SPI and iliocostalis thoracis."
)

_DEEP_UNDER_LAT = (
    "dentele-posterieur-inferieur",
    "iliocostal-thoracique",
    "iliocostal-lombaire",
)


def _push_under_latissimus(scene: trimesh.Scene, lat: trimesh.Trimesh, clearance: float = 0.0038) -> None:
    """Project SPI / iliocostalis verts that still poke behind latissimus inward."""
    from scipy.spatial import cKDTree

    lat_v = np.asarray(lat.vertices, dtype=np.float64)
    back = lat_v[(lat_v[:, 2] < 0.02) & (np.abs(lat_v[:, 0]) < 0.15)]
    if len(back) < 24:
        back = lat_v
    tree = cKDTree(back[:, :2])
    y0, y1 = float(back[:, 1].min()), float(back[:, 1].max())
    xmax = float(np.abs(back[:, 0]).max())
    for name in _DEEP_UNDER_LAT:
        geom = scene.geometry.get(name)
        if geom is None:
            continue
        v = np.asarray(geom.vertices, dtype=np.float64).copy()
        mask = (
            (v[:, 1] >= y0 - 0.010)
            & (v[:, 1] <= y1 + 0.010)
            & (np.abs(v[:, 0]) <= xmax + 0.010)
            & (v[:, 2] < 0.035)
        )
        if not np.any(mask):
            continue
        dists, idxs = tree.query(v[mask, :2], k=1)
        # Local posterior surface (nearest XY). Only nudge verts that actually poke out.
        lat_z = back[idxs, 2]
        target = lat_z + clearance
        near = dists < 0.026
        poke = near & (v[mask, 2] < lat_z + 0.0012)
        if not np.any(poke):
            continue
        sel = np.where(mask)[0][poke]
        v[sel, 2] = target[poke]
        geom.vertices = v
        print(f"  push {name}: {int(poke.sum())} verts under latissimus", flush=True)


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
    lat = synth.get("grand-dorsal")
    if lat is not None:
        _push_under_latissimus(scene, lat)

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
