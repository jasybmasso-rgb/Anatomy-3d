"""Enumerate BodyParts3D skeletal muscle groups (named organs / heads / zones)."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Iterable

MUSCLE_ROOTS = ("FMA5022", "FMA85453", "FMA10474")
EXCLUDE_ROOTS = (
    "FMA49033",  # extra-ocular
    "FMA46689",  # tongue
    "FMA46726",  # palate
    "FMA46619",  # pharynx
    "FMA46562",  # larynx
    "FMA46751",  # face
    "FMA46602",  # aryepiglotticus
    "FMA46608",  # cricothyroid zone
    "FMA46601",
)

ABSTRACT_EXACT = {
    "muscle organ",
    "head of muscle organ",
    "zone of muscle organ",
    "skeletal muscle",
    "smooth muscle",
    "cardiac muscle",
}

ABSTRACT_SUB = (
    "compartment of",
    "extrinsic muscle of",
    "intrinsic muscle of",
    "postvertebral",
    "gluteal muscle",
    "set of ",
    "organ system",
    "muscle of perineum",
    "muscle of abdomen",
    "muscle of thorax",
    "muscle of neck",
    "muscle of back",
    "muscle of arm",
    "muscle of forearm",
    "muscle of hand",
    "muscle of thigh",
    "muscle of leg",
    "muscle of foot",
    "muscle of pelvis",
    "muscle of hip",
    "muscle of shoulder",
    "muscle of head",
    "pectoral muscle",
    "hamstring",
    "quadriceps femoris",
    "rotator cuff",
    "erector spinae",
    "transversospinal",
)

DROP_KEYS = {
    "infrahyoid muscle",
    "suprahyoid muscle",
    "prevertebral muscle",
    "rotator muscle",
    "scalene muscle",
    "obturator muscle",
    "interosseous of foot",
    "levator ani",
    "perineal muscle",
    "superficial perineal muscle",
    "interspinalis muscle",
    "intertransversarius muscle",
    "lumbar intertransversarius",
    "iliocostalis",
    "longissimus",
    "spinalis",
    "semispinalis",
    "serratus posterior",
    "splenius",
    "gemellus",
    "deep muscle of anterior compartment of forearm",
    "deep muscle of posterior compartment of forearm",
    "deep muscle of posterior compartment of leg",
    "deep extrinsic muscle of shoulder",
    "extrinsic muscle of shoulder",
    "deep postvertebral muscle",
    "anterior suboccipital muscle",
    "posterior suboccipital muscle",
    "thenar muscle",
    "hypothenar muscle",
    "intercostal muscle",
    "lumbrical of foot",
    "plantar interosseous of foot",
}

# Merge distinct BP3D organs that the app treats as one selectable muscle.
MERGE = {
    "iliacus": "iliopsoas",
    "psoas major": "iliopsoas",
    "longus colli": "longus colli",
    "inferior oblique part of longus colli": "longus colli",
    "superior oblique part of longus colli": "longus colli",
    "vertical intermediate part of longus colli": "longus colli",
    "infraspinatus": "infraspinatus",
    "infraspinatus muscle": "infraspinatus",
}

STABLE_IDS = {
    "biceps brachii": "biceps-brachial",
    "triceps brachii": "triceps-brachial",
    "deltoid": "deltoide",
    "pectoralis major": "grand-pectoral",
    "trapezius": "trapeze",
    "sternocleidomastoid": "sterno-cleido-mastoidien",
    "biceps femoris": "biceps-femoral",
    "semitendinosus": "semi-tendineux",
    "semimembranosus": "semi-membraneux",
    "rectus femoris": "droit-femoral",
    "vastus lateralis": "vaste-lateral",
    "vastus medialis": "vaste-medial",
    "vastus intermedius": "vaste-intermediaire",
    "gluteus maximus": "grand-fessier",
    "iliopsoas": "iliopsoas",
    "gastrocnemius": "gastrocnemien",
    "soleus": "soleaire",
    "tibialis anterior": "tibial-anterieur",
    "external oblique": "oblique-externe",
    "internal oblique": "oblique-interne",
    "transversus abdominis": "transverse-de-l-abdomen",
    "supraspinatus": "supra-epineux",
    "latissimus dorsi": "grand-dorsal",
    "rectus abdominis": "droit-abdomen",
}

LAT = re.compile(r"\b(left|right)\b")
HEAD_PREFIX = re.compile(
    r"^(short|long|medial|lateral|clavicular|acromial|spinal|sternocostal|"
    r"abdominal|ascending|transverse|descending|superior|inferior|oblique|"
    r"straight|reflected|humeral|ulnar|radial|tibial|fibular|costal|sternal|"
    r"vertebral|iliac|lumbar|thoracic|cervical|pubic|ischial|femoral|deep|"
    r"superficial|anterior|posterior|upper|lower|middle|dorsal|palmar|plantar|"
    r"vertical|oblique) (head|part|belly|bundle) of ",
    re.I,
)
HEAD2 = re.compile(r"^(head|part|zone) of ", re.I)

HEAD_FR = {
    "long head": "Chef long",
    "short head": "Chef court",
    "medial head": "Chef médial",
    "lateral head": "Chef latéral",
    "clavicular part": "Faisceau claviculaire",
    "acromial part": "Faisceau acromial",
    "spinal part": "Faisceau spinal",
    "sternocostal part": "Faisceau sterno-costal",
    "abdominal part": "Faisceau abdominal",
    "ascending part": "Faisceau ascendant",
    "transverse part": "Faisceau transverse",
    "descending part": "Faisceau descendant",
    "humeral head": "Chef huméral",
    "ulnar head": "Chef ulnaire",
    "oblique head": "Chef oblique",
    "transverse head": "Chef transverse",
    "superior oblique part": "Faisceau oblique supérieur",
    "inferior oblique part": "Faisceau oblique inférieur",
    "vertical intermediate part": "Faisceau vertical",
    "deep head": "Chef profond",
    "superficial head": "Chef superficiel",
}


@dataclass
class MuscleGroup:
    key: str
    id: str
    source_names: list[str] = field(default_factory=list)
    concept_ids: list[str] = field(default_factory=list)
    file_ids: list[str] = field(default_factory=list)

    def head_labels(self) -> list[str]:
        labels: list[str] = []
        seen: set[str] = set()
        for name in self.source_names:
            label = head_label(name)
            if label and label not in seen:
                seen.add(label)
                labels.append(label)
        return labels


def group_key(name: str) -> str:
    n = LAT.sub("", name.lower())
    n = re.sub(r"\s+", " ", n).strip()
    n = HEAD_PREFIX.sub("", n)
    n = HEAD2.sub("", n)
    n = n.replace(" of the ", " of ")
    n = re.sub(r"^(left|right) ", "", n)
    return n.strip()


def head_label(name: str) -> str | None:
    low = LAT.sub("", name.lower())
    low = re.sub(r"\s+", " ", low).strip()
    for en, fr in HEAD_FR.items():
        if low.startswith(en):
            return fr
    m = re.match(r"^(.+? (?:head|part|belly)) of ", low)
    if m:
        key = m.group(1)
        return HEAD_FR.get(key, key.replace(" part", "").replace(" head", "").title())
    return None


def _descendants(children: dict[str, list[str]], roots: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    q = deque(roots)
    while q:
        n = q.popleft()
        if n in seen:
            continue
        seen.add(n)
        q.extend(children.get(n, []))
    return seen


def _slug(text: str) -> str:
    nfd = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    stripped = re.sub(r"[^a-z0-9]+", "-", stripped).strip("-")
    return stripped or "muscle"


def muscle_id_for(key: str, french_name: str) -> str:
    if key in STABLE_IDS:
        return STABLE_IDS[key]
    return _slug(french_name)


def _is_laterality(name: str) -> bool:
    low = name.lower()
    return "left" in low or "right" in low


def enumerate_muscle_groups(
    parts: list[list[str]],
    inclusion: list[list[str]],
    element_map: dict[str, list[str]],
) -> list[MuscleGroup]:
    id_to_name = {row[0]: row[2] for row in parts if len(row) >= 3}
    children: dict[str, list[str]] = defaultdict(list)
    for row in inclusion:
        if len(row) >= 4:
            children[row[0]].append(row[2])

    muscle_ids = _descendants(children, MUSCLE_ROOTS)
    exclude_ids = _descendants(children, EXCLUDE_ROOTS)

    # All mesh-bearing named concepts, for IS-A gaps (trapezius parts, etc.).
    named_meshes: list[tuple[str, str, list[str]]] = []
    for cid, name in id_to_name.items():
        files = element_map.get(cid, [])
        if files:
            named_meshes.append((cid, name, files))

    buckets: dict[str, list[tuple[str, str, list[str]]]] = defaultdict(list)
    for cid in muscle_ids:
        if cid in exclude_ids:
            continue
        name = id_to_name.get(cid, "")
        low = name.lower()
        if not name or low in ABSTRACT_EXACT:
            continue
        if any(s in low for s in ABSTRACT_SUB):
            continue
        files = element_map.get(cid, [])
        if not files:
            continue
        buckets[group_key(name)].append((cid, name, files))

    # Expand each key against the full named list (catches unlinked heads).
    known = set(buckets)
    for cid, name, files in named_meshes:
        if cid in exclude_ids:
            continue
        key = group_key(name)
        if key not in known:
            continue
        existing = {(c, n) for c, n, _ in buckets[key]}
        if (cid, name) not in existing:
            buckets[key].append((cid, name, files))

    merged: dict[str, list[tuple[str, str, list[str]]]] = defaultdict(list)
    for key, items in buckets.items():
        if key in DROP_KEYS or key.startswith("muscle of") or "compartment" in key:
            continue
        dest = MERGE.get(key, key)
        merged[dest].extend(items)

    groups: list[MuscleGroup] = []
    used_ids: set[str] = set()
    for key in sorted(merged):
        items = merged[key]
        has_lat = any(_is_laterality(n) for _, n, _ in items)
        if has_lat:
            items = [it for it in items if _is_laterality(it[1])]
        # Unique by concept id
        uniq: list[tuple[str, str, list[str]]] = []
        seen_c: set[str] = set()
        for cid, name, files in items:
            if cid in seen_c:
                continue
            seen_c.add(cid)
            uniq.append((cid, name, files))
        if not uniq:
            continue
        from muscle_catalog import french_name_for  # local import to avoid cycle at module load

        fr = french_name_for(key)
        mid = muscle_id_for(key, fr)
        if mid in used_ids:
            mid = f"{mid}-{_slug(key)}"
        used_ids.add(mid)
        file_ids: list[str] = []
        for _c, _n, files in uniq:
            for fid in files:
                if fid not in file_ids:
                    file_ids.append(fid)
        groups.append(
            MuscleGroup(
                key=key,
                id=mid,
                source_names=[n for _c, n, _f in uniq],
                concept_ids=[c for c, _n, _f in uniq],
                file_ids=file_ids,
            )
        )
    return groups
