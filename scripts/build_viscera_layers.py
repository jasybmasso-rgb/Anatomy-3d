#!/usr/bin/env python3
"""Build nerves.glb, organs.glb and vessels.glb from BodyParts3D (+ schematic nerves).

Three mutually exclusive Couches layers. Same worldMatrix as skeleton.glb.
Source: BodyParts3D / Anatomography (DBCLS), CC BY-SA 2.1 Japan.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import trimesh
from trimesh.exchange.gltf import export_glb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_skeleton_glb as sk
from anatomy_fr import region_from_point, slug_id, translate_en
from build_synthetic_nerves import build as build_synthetic_nerves

SKELETON_META = sk.ROOT / "public" / "models" / "skeleton.meta.json"
OUT_DIR = sk.ROOT / "public" / "models"
DATA_DIR = sk.ROOT / "src" / "data"

MAX_FACES = {
    "nerve": 2200,
    "organ": 4500,
    "vessel": 1800,
}
PRE_FACES = {"nerve": 1800, "organ": 2800, "vessel": 1400}
MAX_GLB_MIB = {"nerve": 8.0, "organ": 16.0, "vessel": 12.0}

ORGAN_INCLUSION = (
    "Organes viscéraux BodyParts3D 4.0 (reins, rate, estomac, pancréas, vessie, "
    "vésicule, œsophage, trachée, prostate, testicules, surrénales, thymus, "
    "foie par segments, cœur parois/cavités, intestin, arbre bronchique comme "
    "stand-in pulmonaire, encéphale / cervelet). Absent de BP3D 4.0 : parenchyme "
    "pulmonaire nommé, foie d’un seul tenant, cœur d’un seul tenant. "
    "Les artères/veines et le muscle diaphragme sont exclus (couches Vaisseaux / Muscles)."
)
VESSEL_INCLUSION = (
    "Vaisseaux sanguins seulement : troncs artériels et veineux nommés BodyParts3D "
    "(aorte, carotides, iliaques, fémorales, pulmonaires, caves, portes, coronaires…) "
    "plus un arbre artériel et un arbre veineux résiduels pour les branches non nommées. "
    "Pas d’organes (cœur-muscle, poumons, foie) dans cette couche."
)
NERVE_INCLUSION = (
    "Nerfs crâniens / orbitaires BodyParts3D 4.0 (optique, trochléaire, oculomoteur, "
    "ophtalmique, ciliaires). Les grands troncs périphériques (plexus brachial, "
    "médian, ulnaire, radial, sciatique, fémoral, tibial, fibulaire, phrénique…) "
    "sont des tubes schématiques synthetic-v2 plus fins, calés sur le trajet usuel : "
    "BP3D 4.0 n’a pas ces maillages."
)

# Exact English names (isa_parts_list_e.txt) for searchable key vessels.
PRIORITY_VESSELS = [
    "ascending aorta",
    "arch of aorta",
    "descending thoracic aorta",
    "abdominal aorta",
    "brachiocephalic artery",
    "right common carotid artery",
    "left common carotid artery",
    "right internal carotid artery",
    "left internal carotid artery",
    "right external carotid artery",
    "left external carotid artery",
    "right subclavian artery",
    "left subclavian artery",
    "right vertebral artery",
    "left vertebral artery",
    "right axillary artery",
    "left axillary artery",
    "right brachial artery",
    "left brachial artery",
    "right radial artery",
    "left radial artery",
    "right ulnar artery",
    "left ulnar artery",
    "pulmonary trunk",
    "right pulmonary artery",
    "left pulmonary artery",
    "celiac artery",
    "celiac trunk",
    "common hepatic artery",
    "hepatic artery proper",
    "splenic artery",
    "superior mesenteric artery",
    "inferior mesenteric artery",
    "right renal artery",
    "left renal artery",
    "right common iliac artery",
    "left common iliac artery",
    "right external iliac artery",
    "left external iliac artery",
    "right internal iliac artery",
    "left internal iliac artery",
    "right femoral artery",
    "left femoral artery",
    "right deep femoral artery",
    "left deep femoral artery",
    "right popliteal artery",
    "left popliteal artery",
    "right anterior tibial artery",
    "left anterior tibial artery",
    "right posterior tibial artery",
    "left posterior tibial artery",
    "trunk of right coronary artery",
    "trunk of left coronary artery",
    "circumflex branch of left coronary artery",
    "anterior interventricular branch of left coronary artery",
    "right internal thoracic artery",
    "left internal thoracic artery",
    "basilar artery",
    "right anterior cerebral artery",
    "left anterior cerebral artery",
    "superior vena cava",
    "inferior vena cava",
    "right brachiocephalic vein",
    "left brachiocephalic vein",
    "right internal jugular vein",
    "left internal jugular vein",
    "right external jugular vein",
    "left external jugular vein",
    "right subclavian vein",
    "left subclavian vein",
    "right femoral vein",
    "left femoral vein",
    "right great saphenous vein",
    "left great saphenous vein",
    "hepatic portal vein",
    "right hepatic vein",
    "left hepatic vein",
    "middle hepatic vein",
    "right renal vein",
    "left renal vein",
    "right common iliac vein",
    "left common iliac vein",
    "right pulmonary vein",
    "left pulmonary vein",
    "right superior pulmonary vein",
    "left superior pulmonary vein",
    "right inferior pulmonary vein",
    "left inferior pulmonary vein",
    "azygos vein",
    "coronary sinus",
    "great cardiac vein",
    "right cephalic vein",
    "left cephalic vein",
    "right basilic vein",
    "left basilic vein",
]

ORGAN_GROUPS: list[dict] = [
    {
        "id": "rein-d",
        "name": "Rein droit",
        "nameLatin": "Ren dexter",
        "tone": "kidney",
        "exact": ["right kidney"],
    },
    {
        "id": "rein-g",
        "name": "Rein gauche",
        "nameLatin": "Ren sinister",
        "tone": "kidney",
        "exact": ["left kidney"],
    },
    {
        "id": "rate",
        "name": "Rate",
        "nameLatin": "Splen",
        "tone": "spleen",
        "exact": ["spleen"],
    },
    {
        "id": "estomac",
        "name": "Estomac",
        "nameLatin": "Gaster",
        "tone": "gut",
        "exact": ["stomach"],
    },
    {
        "id": "pancreas",
        "name": "Pancréas",
        "nameLatin": "Pancreas",
        "tone": "gland",
        "contains": ["pancreas"],
        "exclude": ["artery", "vein"],
    },
    {
        "id": "vessie",
        "name": "Vessie",
        "nameLatin": "Vesica urinaria",
        "tone": "gut",
        "exact": ["urinary bladder"],
    },
    {
        "id": "vesicule-biliaire",
        "name": "Vésicule biliaire",
        "nameLatin": "Vesica biliaris",
        "tone": "gland",
        "exact": ["gallbladder"],
    },
    {
        "id": "oesophage",
        "name": "Œsophage",
        "nameLatin": "Oesophagus",
        "tone": "gut",
        "exact": ["esophagus"],
    },
    {
        "id": "trachee",
        "name": "Trachée",
        "nameLatin": "Trachea",
        "tone": "lung",
        "exact": ["trachea"],
    },
    {
        "id": "prostate",
        "name": "Prostate",
        "nameLatin": "Prostata",
        "tone": "gland",
        "exact": ["prostate"],
    },
    {
        "id": "testicule-d",
        "name": "Testicule droit",
        "nameLatin": "Testis dexter",
        "tone": "gland",
        "exact": ["right testis"],
    },
    {
        "id": "testicule-g",
        "name": "Testicule gauche",
        "nameLatin": "Testis sinister",
        "tone": "gland",
        "exact": ["left testis"],
    },
    {
        "id": "surrenale-d",
        "name": "Glande surrénale droite",
        "nameLatin": "Glandula suprarenalis dextra",
        "tone": "gland",
        "exact": ["right adrenal gland"],
    },
    {
        "id": "surrenale-g",
        "name": "Glande surrénale gauche",
        "nameLatin": "Glandula suprarenalis sinistra",
        "tone": "gland",
        "exact": ["left adrenal gland"],
    },
    {
        "id": "thymus",
        "name": "Thymus",
        "nameLatin": "Thymus",
        "tone": "gland",
        "contains": ["thymus"],
        "exclude": ["artery", "vein"],
    },
    {
        "id": "hypophyse",
        "name": "Hypophyse",
        "nameLatin": "Hypophysis",
        "tone": "gland",
        "contains": ["pituitary"],
        "exclude": ["artery", "vein"],
    },
    {
        "id": "glandes-salivaires",
        "name": "Glandes salivaires",
        "nameLatin": "Glandulae salivariae",
        "tone": "gland",
        "contains": ["salivary"],
        "exclude": ["artery", "vein", "muscle"],
    },
    {
        "id": "foie",
        "name": "Foie",
        "nameLatin": "Hepar",
        "tone": "liver",
        "contains": ["liver"],
        "exclude": ["artery", "vein", "duct", "portal", "biliary", "tributary"],
        "notes": "Segments / secteurs BodyParts3D — le foie n’existe pas comme organe unique nommé.",
    },
    {
        "id": "coeur",
        "name": "Cœur",
        "nameLatin": "Cor",
        "tone": "heart",
        "contains": [
            "atrium",
            "ventricle",
            "wall of heart",
            "cardiac valve",
            "cardiac chamber",
            "papillary muscle of",
        ],
        "exclude": ["artery", "vein", "sinus"],
        "notes": "Parois, cavités et valves. Les coronaires sont dans la couche Vaisseaux.",
    },
    {
        "id": "poumons",
        "name": "Poumons (arbre bronchique)",
        "nameLatin": "Arbor bronchialis",
        "tone": "lung",
        "contains": ["bronch"],
        "exclude": ["artery", "vein", "aorta"],
        "notes": "BP3D 4.0 n’a pas de parenchyme pulmonaire nommé ; l’arbre bronchique en tient lieu.",
    },
    {
        "id": "intestin-grele",
        "name": "Intestin grêle",
        "nameLatin": "Intestinum tenue",
        "tone": "gut",
        "contains": ["small intestine", "ileum", "jejunum", "duodenum"],
        "exclude": ["artery", "vein", "mesentery"],
    },
    {
        "id": "gros-intestin",
        "name": "Gros intestin",
        "nameLatin": "Intestinum crassum",
        "tone": "gut",
        "contains": ["large intestine", "colon", "rectum", "cecum"],
        "exclude": ["artery", "vein", "mesentery", "marginal"],
    },
    {
        "id": "cervelet",
        "name": "Cervelet",
        "nameLatin": "Cerebellum",
        "tone": "brain",
        "contains": ["cerebellum"],
        "exclude": ["artery", "vein"],
    },
    {
        "id": "encephale",
        "name": "Encéphale",
        "nameLatin": "Encephalon",
        "tone": "brain",
        "contains": [
            "neuraxis",
            "telencephalon",
            "cerebral",
            "thalamus",
            "hypothalamus",
            "hippocamp",
            "amygdala",
            "putamen",
            "caudate nucleus",
            "pons",
            "medulla oblongata",
            "midbrain",
            "forebrain",
            "hindbrain",
            "diencephalon",
            "brain",
        ],
        "exclude": ["artery", "vein", "nerve", "cerebellum", "pituitary", "choroid plexus"],
        "notes": "Substance blanche/grise et noyaux BP3D. Pas un atlas IRM complet.",
    },
    {
        "id": "oeil-d",
        "name": "Œil droit",
        "nameLatin": "Oculus dexter",
        "tone": "default",
        "contains": ["eyeball", "cornea", "sclera", "lens", "retina"],
        "require": ["right"],
        "exclude": ["artery", "vein", "nerve", "muscle", "ligament", "eyebrow", "eyelid", "tarsal"],
    },
    {
        "id": "oeil-g",
        "name": "Œil gauche",
        "nameLatin": "Oculus sinister",
        "tone": "default",
        "contains": ["eyeball", "cornea", "sclera", "lens", "retina"],
        "require": ["left"],
        "exclude": ["artery", "vein", "nerve", "muscle", "ligament", "eyebrow", "eyelid", "tarsal"],
    },
]

ORGAN_RGB = {
    "kidney": (168, 72, 64),
    "spleen": (150, 48, 52),
    "gut": (196, 118, 88),
    "gland": (214, 176, 132),
    "liver": (132, 52, 42),
    "heart": (156, 36, 40),
    "lung": (214, 154, 154),
    "brain": (232, 196, 186),
    "default": (196, 140, 120),
}
NERVE_RGB = (246, 214, 72, 255)
ARTERY_RGB = (188, 42, 42, 255)
VEIN_RGB = (42, 74, 168, 255)

SKIP_VESSEL = (
    "subdivision of",
    "segment of",
    "set of",
    "region of vascular",
    "tree organ",
    "tributary of",
    "variant ",
    "anastomosis",
    "zone of",
    "organ system",
)
ORDINAL_RE = re.compile(
    r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b",
    re.I,
)


def descendants(children: dict[str, list[str]], roots: list[str]) -> set[str]:
    seen: set[str] = set()
    q = deque(roots)
    while q:
        n = q.popleft()
        if n in seen:
            continue
        seen.add(n)
        q.extend(children.get(n, []))
    return seen


def _simplify(mesh: trimesh.Trimesh, max_faces: int) -> trimesh.Trimesh:
    if len(mesh.faces) <= max_faces:
        return mesh
    try:
        out = mesh.simplify_quadric_decimation(face_count=max_faces)
        if out is not None and len(out.faces) > 0:
            return out
    except Exception as exc:  # noqa: BLE001
        print(f"    simplify skip ({exc})", flush=True)
    return mesh


def _focus(mesh: trimesh.Trimesh) -> dict:
    verts = mesh.vertices
    centroid = verts.mean(0)
    extents = verts.max(0) - verts.min(0)
    radius = float(np.linalg.norm(extents) * 0.5)
    distance = float(min(1.45, max(0.55, radius * 2.2)))
    return {
        "position": [round(float(x), 5) for x in centroid],
        "distance": round(distance, 3),
    }


def _load_files(file_ids: list[str], obj_map: dict[str, Path], pre_faces: int) -> trimesh.Trimesh | None:
    meshes: list[trimesh.Trimesh] = []
    for fid in file_ids:
        path = obj_map.get(fid) or obj_map.get(fid.upper())
        if path is None:
            continue
        mesh = sk.load_mesh(path)
        if mesh is None:
            continue
        mesh = _simplify(mesh, max(pre_faces, 200))
        meshes.append(mesh)
    if not meshes:
        return None
    return meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)


def _claim(file_ids: list[str], claimed: set[str]) -> list[str]:
    out = []
    for fid in file_ids:
        if fid in claimed:
            continue
        claimed.add(fid)
        out.append(fid)
    return out


def _catalog_row(
    *,
    part_id: str,
    name: str,
    latin: str,
    kind: str,
    source: str,
    source_names: list[str],
    fma_ids: list[str],
    file_ids: list[str],
    mesh: trimesh.Trimesh,
    notes: str,
    aliases: list[str] | None = None,
    extra: dict | None = None,
) -> dict:
    c = mesh.vertices.mean(0)
    row = {
        "id": part_id,
        "name": name,
        "nameLatin": latin,
        "aliases": aliases or [],
        "region": region_from_point(float(c[0]), float(c[1]), float(c[2])),
        "notes": notes,
        "source": source,
        "sourceNames": source_names,
        "fmaIds": fma_ids,
        "fileIds": sorted(set(file_ids)),
        "centroid": [round(float(x), 5) for x in c],
        "focus": _focus(mesh),
        "vertexCount": int(len(mesh.vertices)),
        "faceCount": int(len(mesh.faces)),
        "kind": kind,
    }
    if extra:
        row.update(extra)
    return row


def _match_group(group: dict, name: str) -> bool:
    low = name.lower()
    if any(x in low for x in group.get("exclude", [])):
        return False
    req = group.get("require") or []
    if req and not all(r in low for r in req):
        return False
    exact = {n.lower() for n in group.get("exact", [])}
    if exact and low in exact:
        return True
    contains = group.get("contains") or []
    if contains and any(tok in low for tok in contains):
        return True
    return False


def _is_vessel_name(name: str) -> bool:
    low = name.lower()
    if any(s in low for s in SKIP_VESSEL):
        return False
    if ORDINAL_RE.search(low):
        return False
    if any(s in low for s in ("muscle", "nerve", "ligament", "bone", "cartilage")):
        return False
    keys = ("artery", "vein", "aorta", "vena cava", "carotid", "jugular", "coronary sinus")
    return any(k in low for k in keys)


def _vessel_kind(name: str) -> str:
    low = name.lower()
    if any(k in low for k in ("vein", "vena cava", "sinus", "azygos", "saphenous", "portal", "jugular")):
        if "artery" in low:
            return "artery"
        return "vein"
    return "artery"


def _write_glb(
    kind: str,
    items: list[tuple[str, trimesh.Trimesh, dict]],
    catalog: list[dict],
    inclusion: str,
    extra_meta: dict | None = None,
) -> None:
    scene = trimesh.Scene()
    for part_id, mesh, rec in items:
        rgb = rec.pop("_rgb")
        mesh.visual.vertex_colors = list(rgb)
        mesh.metadata["name"] = part_id
        scene.add_geometry(mesh, node_name=part_id, geom_name=part_id)

    stem = {"nerve": "nerves", "organ": "organs", "vessel": "vessels"}[kind]
    out_glb = OUT_DIR / f"{stem}.glb"
    out_meta = OUT_DIR / f"{stem}.meta.json"
    out_cat = DATA_DIR / f"{stem}.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_glb.write_bytes(export_glb(scene, include_normals=True))
    size_mb = out_glb.stat().st_size / (1024 * 1024)
    cap = MAX_GLB_MIB[kind]
    if size_mb > cap:
        print(f"warning: {stem}.glb {size_mb:.2f} MiB exceeds {cap}", file=sys.stderr)

    n_bp3d = sum(1 for p in catalog if p.get("source") == "bodyparts3d")
    n_synth = sum(1 for p in catalog if str(p.get("source", "")).startswith("synthetic"))
    faces = sum(p.get("faceCount", 0) for p in catalog)
    verts = sum(p.get("vertexCount", 0) for p in catalog)
    meta = {
        "glbBytes": out_glb.stat().st_size,
        "glbMiB": round(size_mb, 2),
        "partCount": len(catalog),
        "countBodyparts3d": n_bp3d,
        "countSynthetic": n_synth,
        "vertexCount": verts,
        "faceCount": faces,
        "maxFacesPerPart": MAX_FACES[kind],
        "license": "CC BY-SA 2.1 Japan (BP3D meshes); synthetic-v2 tubes are original educational approximations",
        "alignedTo": "public/models/skeleton.glb",
        "inclusionRules": inclusion,
    }
    if extra_meta:
        meta.update(extra_meta)
    out_meta.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    payload = {
        "version": 1,
        "defaultVisible": False,
        "inclusionRules": inclusion,
        "count": len(catalog),
        "countBodyparts3d": n_bp3d,
        "countSynthetic": n_synth,
        f"{stem}": catalog,
    }
    if kind == "nerve":
        payload["syntheticDisclaimer"] = (
            "Les pièces source=synthetic-v2 sont des tubes loftés le long du trajet "
            "anatomique usuel (repères osseux), pas des nerfs segmentés. "
            "Les maillages crâniens BP3D restent source=bodyparts3d."
        )
    out_cat.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_glb} ({size_mb:.2f} MiB), {len(catalog)} parts, {faces} faces", flush=True)


def main() -> int:
    if not SKELETON_META.exists():
        print("missing skeleton.meta.json — run scripts/build_skeleton_glb.py first", file=sys.stderr)
        return 1
    sk_meta = json.loads(SKELETON_META.read_text(encoding="utf-8"))
    matrix = np.array(sk_meta["worldMatrix"], dtype=float)
    if matrix.shape != (4, 4):
        print("invalid worldMatrix", file=sys.stderr)
        return 1

    sk.CACHE.mkdir(parents=True, exist_ok=True)
    parts_path = sk.CACHE / "isa_parts_list_e.txt"
    inc_path = sk.CACHE / "isa_inclusion_relation_list.txt"
    element_path = sk.CACHE / "isa_element_parts.txt"
    zip_path = sk.CACHE / "isa_BP3D_4.0_obj_99.zip"
    sk.download(sk.PARTS_URL, parts_path)
    sk.download(sk.INC_URL, inc_path)
    sk.download(sk.ELEMENT_URL, element_path)
    sk.download(sk.ZIP_URL, zip_path, require_zip=True)

    parts = sk.load_tsv(parts_path)
    inc_rows = sk.load_tsv(inc_path)
    element_map = sk.load_element_map(element_path)
    id_to_name = {row[0]: row[2] for row in parts if len(row) >= 3}
    name_to_row = {row[2].lower(): row for row in parts if len(row) >= 3}
    children: dict[str, list[str]] = defaultdict(list)
    for row in inc_rows:
        if len(row) >= 4:
            children[row[0]].append(row[2])

    extract = sk.CACHE / "isa_obj"
    if not extract.exists() or not any(extract.rglob("*.obj")):
        print(f"extract {zip_path}", flush=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract)
    obj_map = sk.find_obj_map(extract)
    claimed: set[str] = set()

    def files_for_names(names: list[str]) -> tuple[list[str], list[str], list[str]]:
        fids: list[str] = []
        fmas: list[str] = []
        used_names: list[str] = []
        for en in names:
            row = name_to_row.get(en.lower())
            if row is None:
                continue
            cid = row[0]
            raw = element_map.get(cid, [])
            got = _claim(raw, claimed)
            if not got:
                continue
            fids.extend(got)
            fmas.append(cid)
            used_names.append(en)
        return fids, fmas, used_names

    def add_mesh(kind: str, file_ids: list[str], max_faces: int, pre_faces: int | None = None) -> trimesh.Trimesh | None:
        mesh = _load_files(file_ids, obj_map, pre_faces if pre_faces is not None else PRE_FACES[kind])
        if mesh is None:
            return None
        mesh.apply_transform(matrix)
        return _simplify(mesh, max_faces)

    # --- nerves (BP3D cranial / orbital) ---
    print("building nerves…", flush=True)
    nerve_roots = [cid for cid, name in id_to_name.items() if name.lower() in {
        "nerve", "nerve trunk", "cranial nerve", "branch of cranial nerve", "ganglion",
        "ciliary ganglion", "optic nerve", "optic chiasm", "optic tract",
    }]
    nerve_ids = descendants(children, nerve_roots or ["FMA65132", "FMA5913", "FMA5865"])
    nerve_items: list[tuple[str, trimesh.Trimesh, dict]] = []
    nerve_cat: list[dict] = []
    # Prefer laterality leaves
    nerve_rows = []
    for cid in nerve_ids:
        name = id_to_name.get(cid, "")
        low = name.lower()
        if not name or low in {
            "nerve",
            "nerve trunk",
            "cranial nerve",
            "ganglion",
            "autonomic ganglion",
            "parasympathetic ganglion",
            "cranial parasympathetic ganglion",
            "branch of cranial nerve",
        }:
            continue
        if low.startswith("branch of ") and "left" not in low and "right" not in low:
            continue
        if any(k in low for k in ("artery", "vein", "muscle", "choroid plexus", "basal ganglion")):
            continue
        if not any(k in low for k in ("nerve", "ganglion", "chiasm", "optic tract")):
            continue
        nerve_rows.append((cid, name))

    # skip parent if L/R children also selected
    def _bare(label: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"\b(left|right)\b", "", label.lower())).strip()

    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for cid, name in nerve_rows:
        grouped[_bare(name)].append((cid, name))
    filtered = []
    for items in grouped.values():
        sided = [(c, n) for c, n in items if re.search(r"\b(left|right)\b", n, re.I)]
        filtered.extend(sided if sided else items)

    for cid, name in sorted(filtered, key=lambda x: x[1].lower()):
        fids = _claim(element_map.get(cid, []), claimed)
        if not fids:
            continue
        mesh = add_mesh("nerve", fids, MAX_FACES["nerve"])
        if mesh is None:
            continue
        fr = translate_en(name)
        part_id = slug_id(fr)
        rec = _catalog_row(
            part_id=part_id,
            name=fr,
            latin=name,
            kind="nerve",
            source="bodyparts3d",
            source_names=[name],
            fma_ids=[cid],
            file_ids=fids,
            mesh=mesh,
            notes="Maillage BodyParts3D (nerf crânien / orbitaire).",
            aliases=[name],
        )
        rec["_rgb"] = NERVE_RGB
        nerve_items.append((part_id, mesh, rec))
        nerve_cat.append({k: v for k, v in rec.items() if k != "_rgb"})
        print(f"  + nerve {part_id:40s} {len(mesh.faces):5d} faces  {name}", flush=True)

    print("synthesizing peripheral nerve trunks…", flush=True)
    synth_meshes, synth_cat = build_synthetic_nerves()
    for part_id, mesh in synth_meshes:
        mesh.visual.vertex_colors = NERVE_RGB
        rec = next(c for c in synth_cat if c["id"] == part_id)
        rec["_rgb"] = NERVE_RGB
        nerve_items.append((part_id, mesh, rec))
        nerve_cat.append({k: v for k, v in rec.items() if k != "_rgb"})
        print(f"  + nerve {part_id:40s} {len(mesh.faces):5d} faces  synthetic", flush=True)

    if len(nerve_items) < 8:
        print("too few nerves; abort", file=sys.stderr)
        return 1
    _write_glb("nerve", nerve_items, nerve_cat, NERVE_INCLUSION)

    # Reset claimed: organs and vessels should not steal nerve files, but they
    # live in different GLBs so overlapping FJ is OK geometrically. Reclaim from
    # scratch for organs vs vessels (must not overlap each other).
    claimed = set()

    # --- organs ---
    print("building organs…", flush=True)
    organ_items: list[tuple[str, trimesh.Trimesh, dict]] = []
    organ_cat: list[dict] = []
    for group in ORGAN_GROUPS:
        names = []
        for row in parts:
            if len(row) < 3:
                continue
            if _match_group(group, row[2]):
                names.append(row[2])
        fids, fmas, used = files_for_names(names)
        if not fids:
            print(f"  skip empty organ {group['id']}", flush=True)
            continue
        mesh = add_mesh("organ", fids, MAX_FACES["organ"])
        if mesh is None:
            continue
        rgb = ORGAN_RGB.get(group["tone"], ORGAN_RGB["default"])
        rec = _catalog_row(
            part_id=group["id"],
            name=group["name"],
            latin=group["nameLatin"],
            kind="organ",
            source="bodyparts3d",
            source_names=used,
            fma_ids=fmas,
            file_ids=fids,
            mesh=mesh,
            notes=group.get("notes") or "Maillage BodyParts3D (organe / viscère).",
            aliases=[group["nameLatin"], *used[:8]],
            extra={"organTone": group["tone"]},
        )
        rec["_rgb"] = (*rgb, 255)
        organ_items.append((group["id"], mesh, rec))
        organ_cat.append({k: v for k, v in rec.items() if k != "_rgb"})
        print(f"  + organ {group['id']:24s} {len(mesh.faces):5d} faces  {len(used)} parts", flush=True)

    if len(organ_items) < 8:
        print("too few organs; abort", file=sys.stderr)
        return 1
    _write_glb("organ", organ_items, organ_cat, ORGAN_INCLUSION)

    # --- vessels ---
    print("building vessels…", flush=True)
    vessel_items: list[tuple[str, trimesh.Trimesh, dict]] = []
    vessel_cat: list[dict] = []
    missing_priority = []
    for en in PRIORITY_VESSELS:
        row = name_to_row.get(en.lower())
        if row is None:
            missing_priority.append(en)
            continue
        fids = _claim(element_map.get(row[0], []), claimed)
        if not fids:
            missing_priority.append(en + " (no unique mesh)")
            continue
        mesh = add_mesh("vessel", fids, MAX_FACES["vessel"])
        if mesh is None:
            continue
        kind_v = _vessel_kind(en)
        fr = translate_en(en)
        part_id = slug_id(fr)
        # disambiguate collisions
        if any(p[0] == part_id for p in vessel_items):
            part_id = f"{part_id}-{row[0].lower()}"
        rec = _catalog_row(
            part_id=part_id,
            name=fr,
            latin=en,
            kind="vessel",
            source="bodyparts3d",
            source_names=[en],
            fma_ids=[row[0]],
            file_ids=fids,
            mesh=mesh,
            notes="Tronc vasculaire BodyParts3D (circulation seulement).",
            aliases=[en],
            extra={"vesselKind": kind_v},
        )
        rec["_rgb"] = ARTERY_RGB if kind_v == "artery" else VEIN_RGB
        vessel_items.append((part_id, mesh, rec))
        vessel_cat.append({k: v for k, v in rec.items() if k != "_rgb"})
        print(f"  + vessel {part_id:42s} {kind_v:6s} {len(mesh.faces):5d}  {en}", flush=True)

    # Remainder arterial / venous trees (unique leftover FJ).
    artery_root = next((cid for cid, n in id_to_name.items() if n.lower() == "artery"), "FMA50720")
    vein_root = next((cid for cid, n in id_to_name.items() if n.lower() == "vein"), "FMA50723")
    art_ids = descendants(children, [artery_root, "FMA66464", "FMA66326"])
    vein_ids = descendants(children, [vein_root, "FMA50723", "FMA66644"])

    def remainder(cids: set[str], label: str, kind_v: str, rgb) -> None:
        leftover: list[str] = []
        for cid in cids:
            name = id_to_name.get(cid, "")
            if not _is_vessel_name(name) and "artery" not in name.lower() and "vein" not in name.lower() and "aorta" not in name.lower():
                # still take unused FJ hanging off the tree
                pass
            leftover.extend(_claim(element_map.get(cid, []), claimed))
        leftover = list(dict.fromkeys(leftover))
        if len(leftover) < 3:
            print(f"  skip remainder {label} ({len(leftover)} files)", flush=True)
            return
        mesh = add_mesh("vessel", leftover, 5500, pre_faces=350)
        if mesh is None:
            return
        rec = _catalog_row(
            part_id=label,
            name="Arbre artériel (branches)" if kind_v == "artery" else "Arbre veineux (branches)",
            latin="Arbor arterialis" if kind_v == "artery" else "Arbor venosa",
            kind="vessel",
            source="bodyparts3d",
            source_names=[label],
            fma_ids=[],
            file_ids=leftover,
            mesh=mesh,
            notes=(
                "Branches BodyParts3D non isolées comme troncs nommés, fusionnées "
                "pour limiter le nombre de nœuds (performance Android)."
            ),
            aliases=["circulation", "vaisseaux"],
            extra={"vesselKind": kind_v},
        )
        rec["_rgb"] = rgb
        vessel_items.append((label, mesh, rec))
        vessel_cat.append({k: v for k, v in rec.items() if k != "_rgb"})
        print(f"  + vessel {label:42s} {kind_v:6s} {len(mesh.faces):5d}  remainder {len(leftover)} FJ", flush=True)

    remainder(art_ids, "arbre-arteriel", "artery", ARTERY_RGB)
    remainder(vein_ids, "arbre-veineux", "vein", VEIN_RGB)

    if len(vessel_items) < 10:
        print("too few vessels; abort", file=sys.stderr)
        return 1
    extra = {"missingPriorityNames": missing_priority} if missing_priority else {}
    if missing_priority:
        print(f"  missing priority ({len(missing_priority)}): {missing_priority[:12]}…", flush=True)
    _write_glb("vessel", vessel_items, vessel_cat, VESSEL_INCLUSION, extra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
