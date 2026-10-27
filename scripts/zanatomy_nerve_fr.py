"""English Z-Anatomy nerve labels → French (fr-CA) display names.

The head noun decides the side adjective. When the label already names a parent
nerve (« du nerf … »), the side agrees with that masculine parent.
"""

from __future__ import annotations

import re
import unicodedata

# Base English name (no .l / .r, surrounding parentheses removed) → French, no side.
FR: dict[str, str] = {
    "Communicating branch of median nerve with ulnar nerve": "Branche communicante du nerf médian avec le nerf ulnaire",
    "Abducens nerve (VI)": "Nerf abducens (VI)",
    "Accessory nerve (XI)": "Nerf accessoire (XI)",
    "Anterior branch of medial antebrachial cutaneous nerve": "Rameau antérieur du nerf cutané médial de l’avant-bras",
    "Anterior branch of obturator nerve": "Rameau antérieur du nerf obturateur",
    "Anterior cutaneous branches of femoral nerve": "Rameaux cutanés antérieurs du nerf fémoral",
    "Anterior division of inferior trunk of brachial plexus": "Division antérieure du tronc inférieur du plexus brachial",
    "Anterior division of mandibular nerve": "Division antérieure du nerf mandibulaire",
    "Anterior division of middle trunk of brachial plexus": "Division antérieure du tronc moyen du plexus brachial",
    "Anterior division of superior trunk of brachial plexus": "Division antérieure du tronc supérieur du plexus brachial",
    "Anterior interosseous nerve of forearm": "Nerf interosseux antérieur de l’avant-bras",
    "Anterior root of posterior femoral cutaneous nerve": "Racine antérieure du nerf cutané postérieur de la cuisse",
    "Anterior root of spinal nerve": "Racine antérieure du nerf spinal",
    "Axillary nerve": "Nerf axillaire",
    "Buccal nerve": "Nerf buccal",
    "Cauda equina": "Queue de cheval",
    "Chorda tympani": "Corde du tympan",
    "Cochlear nerve": "Nerf cochléaire",
    "Common fibular nerve": "Nerf fibulaire commun",
    "Common palmar digital branches of median nerve": "Nerfs digitaux palmaires communs du nerf médian",
    "Common palmar digital branches of ulnar nerve": "Nerfs digitaux palmaires communs du nerf ulnaire",
    "Common plantar digital branches of lateral plantar nerve": "Nerfs digitaux plantaires communs du nerf plantaire latéral",
    "Common plantar digital branches of medial plantar nerve": "Nerfs digitaux plantaires communs du nerf plantaire médial",
    "Deep branch of radial nerve": "Rameau profond du nerf radial",
    "Deep branch of ulnar nerve": "Rameau profond du nerf ulnaire",
    "Deep fibular nerve": "Nerf fibulaire profond",
    "Dorsal branch of ulnar nerve": "Rameau dorsal du nerf ulnaire",
    "Dorsal digital branches of deep fibular nerve": "Nerfs digitaux dorsaux du nerf fibulaire profond",
    "Dorsal digital branches of radial nerve": "Nerfs digitaux dorsaux du nerf radial",
    "Dorsal digital branches of superficial fibular nerve": "Nerfs digitaux dorsaux du nerf fibulaire superficiel",
    "Dorsal digital branches of ulnar nerve": "Nerfs digitaux dorsaux du nerf ulnaire",
    "Dorsal scapular nerve": "Nerf dorsal de la scapula",
    "Facial nerve (VII)": "Nerf facial (VII)",
    "Femoral branch of genitofemoral nerve": "Rameau fémoral du nerf génito-fémoral",
    "Femoral nerve": "Nerf fémoral",
    "Ganglia of sympathetic trunk": "Ganglions du tronc sympathique",
    "Genital branch of genitofemoral nerve": "Rameau génital du nerf génito-fémoral",
    "Genitofemoral nerve": "Nerf génito-fémoral",
    "Glossopharyngeal nerve (IX)": "Nerf glossopharyngien (IX)",
    "Hypoglossal nerve (XII)": "Nerf hypoglosse (XII)",
    "Ilio-inguinal nerve": "Nerf ilio-inguinal",
    "Iliohypogastric nerve": "Nerf ilio-hypogastrique",
    "Inferior alveolar nerve": "Nerf alvéolaire inférieur",
    "Inferior lateral brachial cutaneous nerve": "Nerf cutané brachial latéral inférieur",
    "Inferior subscapular nerve": "Nerf subscapulaire inférieur",
    "Inferior trunk of brachial plexus": "Tronc inférieur du plexus brachial",
    "Infrapatellar branch of saphenous nerve": "Rameau infrapatellaire du nerf saphène",
    "Intercostal nerves": "Nerfs intercostaux",
    "Intermediate dorsal cutaneous nerve of foot": "Nerf cutané dorsal intermédiaire du pied",
    "Lateral antebrachial cutaneous nerve": "Nerf cutané latéral de l’avant-bras",
    "Lateral femoral cutaneous nerve": "Nerf cutané latéral de la cuisse",
    "Lateral pectoral nerve": "Nerf pectoral latéral",
    "Lateral plantar nerve": "Nerf plantaire latéral",
    "Lingual nerve": "Nerf lingual",
    "Long thoracic nerve": "Nerf thoracique long",
    "Maxillary nerve": "Nerf maxillaire",
    "Medial antebrachial cutaneous nerve": "Nerf cutané médial de l’avant-bras",
    "Medial brachial cutaneous nerve": "Nerf cutané médial du bras",
    "Medial crural cutaneous branches of saphenous nerve": "Rameaux cutanés cruraux médiaux du nerf saphène",
    "Medial dorsal cutaneous nerve of foot": "Nerf cutané dorsal médial du pied",
    "Medial pectoral nerve": "Nerf pectoral médial",
    "Medial plantar nerve": "Nerf plantaire médial",
    "Medial sural cutaneous nerve": "Nerf cutané sural médial",
    "Median nerve": "Nerf médian",
    "Meningeal branch of maxillary nerve": "Rameau méningé du nerf maxillaire",
    "Mental nerve": "Nerf mentonnier",
    "Middle trunk of brachial plexus": "Tronc moyen du plexus brachial",
    "Motor root of trigeminal nerve": "Racine motrice du nerf trijumeau",
    "Muscular branches of axillary nerve": "Rameaux musculaires du nerf axillaire",
    "Muscular branches of deep fibular nerve": "Rameaux musculaires du nerf fibulaire profond",
    "Muscular branches of median nerve": "Rameaux musculaires du nerf médian",
    "Muscular branches of radial nerve": "Rameaux musculaires du nerf radial",
    "Muscular branches of ulnar nerve": "Rameaux musculaires du nerf ulnaire",
    "Musculocutaneous nerve": "Nerf musculo-cutané",
    "Nerve to mylohyoid muscle": "Nerf du muscle mylo-hyoïdien",
    "Nerve to piriformis muscle": "Nerf du muscle piriforme",
    "Nerve to quadratus femoris muscle": "Nerf du muscle carré fémoral",
    "Obturator nerve": "Nerf obturateur",
    "Oculomotor nerve (III)": "Nerf oculomoteur (III)",
    "Olfactory nerve (I)": "Nerf olfactif (I)",
    "Ophthalmic nerve": "Nerf ophtalmique",
    "Optic nerve (II)": "Nerf optique (II)",
    "Palmar branch of median nerve": "Rameau palmaire du nerf médian",
    "Palmar branch of ulnar nerve": "Rameau palmaire du nerf ulnaire",
    "Posterior antebrachial cutaneous nerve": "Nerf cutané postérieur de l’avant-bras",
    "Posterior branch of medial antebrachial cutaneous nerve": "Rameau postérieur du nerf cutané médial de l’avant-bras",
    "Posterior branch of obturator nerve": "Rameau postérieur du nerf obturateur",
    "Posterior cord of brachial plexus": "Faisceau postérieur du plexus brachial",
    "Posterior division of inferior trunk of brachial plexus": "Division postérieure du tronc inférieur du plexus brachial",
    "Posterior division of mandibular nerve": "Division postérieure du nerf mandibulaire",
    "Posterior division of middle trunk of brachial plexus": "Division postérieure du tronc moyen du plexus brachial",
    "Posterior division of superior trunk of brachial plexus": "Division postérieure du tronc supérieur du plexus brachial",
    "Posterior femoral cutaneous nerve": "Nerf cutané postérieur de la cuisse",
    "Posterior interosseous nerve of forearm": "Nerf interosseux postérieur de l’avant-bras",
    "Posterior root of posterior femoral cutaneous nerve": "Racine postérieure du nerf cutané postérieur de la cuisse",
    "Posterior root of spinal nerve": "Racine postérieure du nerf spinal",
    "Proper palmar digital branches of median nerve": "Nerfs digitaux palmaires propres du nerf médian",
    "Proper palmar digital branches of ulnar nerve": "Nerfs digitaux palmaires propres du nerf ulnaire",
    "Proper plantar digital branches of lateral plantar nerve": "Nerfs digitaux plantaires propres du nerf plantaire latéral",
    "Proper plantar digital branches of medial plantar nerve": "Nerfs digitaux plantaires propres du nerf plantaire médial",
    "Pudendal nerve": "Nerf pudendal",
    "Radial nerve": "Nerf radial",
    "Roots of brachial plexus": "Racines du plexus brachial",
    "Saphenous nerve": "Nerf saphène",
    "Sciatic nerve": "Nerf sciatique",
    "Sensory root of trigeminal nerve": "Racine sensitive du nerf trijumeau",
    "Spinal ganglion": "Ganglion spinal",
    "Subclavian nerve": "Nerf subclavier",
    "Superficial branch of radial nerve": "Rameau superficiel du nerf radial",
    "Superficial branch of ulnar nerve": "Rameau superficiel du nerf ulnaire",
    "Superficial fibular nerve": "Nerf fibulaire superficiel",
    "Superior gluteal nerve": "Nerf glutéal supérieur",
    "Superior lateral brachial cutaneous nerve": "Nerf cutané brachial latéral supérieur",
    "Superior subscapular nerve": "Nerf subscapulaire supérieur",
    "Superior trunk of brachial plexus": "Tronc supérieur du plexus brachial",
    "Suprascapular nerve": "Nerf suprascapulaire",
    "Sural communicating branch of common fibular nerve": "Rameau communicant sural du nerf fibulaire commun",
    "Sural nerve": "Nerf sural",
    "Sympathetic nerves": "Nerfs sympathiques",
    "Sympathetic trunk": "Tronc sympathique",
    "Thoracodorsal nerve": "Nerf thoraco-dorsal",
    "Tibial nerve": "Nerf tibial",
    "Trigeminal nerve (V)": "Nerf trijumeau (V)",
    "Trochlear nerve (IV)": "Nerf trochléaire (IV)",
    "Ulnar nerve": "Nerf ulnaire",
    "Vagus nerve (X)": "Nerf vague (X)",
    "Vestibular nerve": "Nerf vestibulaire",
    "Vestibulocochlear nerve (VIII)": "Nerf vestibulo-cochléaire (VIII)",
}

# Structures present as empty collections or not modeled in Startup.blend (2 May 2023).
ABSENT = [
    "Nerf phrénique (collection vide)",
    "Rameau récurrent du nerf médian (pas d’objet distinct ; les rameaux thénariens sont dans « rameaux musculaires du nerf médian »)",
    "Rameaux calcanéens médial et latéral (pas d’objet nommé ; le trajet cutané du sural et du tibial s’arrête aux nerfs nommés)",
    "Nerf cutané sural latéral comme objet distinct (présent : rameau communicant sural du fibulaire commun et nerf cutané sural médial)",
    "Nerfs digitaux dorsaux du nerf sural comme objet distinct (le nerf sural est un seul objet par côté)",
    "Chaque nerf digital propre n’est pas un objet par doigt : Z-Anatomy groupe les rameaux communs ou propres d’un même tronc et d’un même côté",
]


def _strip_side(name: str) -> tuple[str, str | None]:
    text = name.strip()
    side = None
    if text.endswith(".l"):
        text, side = text[:-2], "l"
    elif text.endswith(".r"):
        text, side = text[:-2], "r"
    text = text.strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()
    return text, side


def _side_word(french: str, side: str) -> str:
    """Side adjective at the end. Parent nerves and plexuses stay masculine singular."""
    low = french.lower()
    if any(token in low for token in (" du nerf ", " du plexus ", " du tronc ", " du muscle ")):
        return "gauche" if side == "l" else "droit"
    head = french.split()[0].lower()
    if head == "racines":
        return "gauches" if side == "l" else "droites"
    if head in {"nerfs", "rameaux", "ganglions"}:
        return "gauches" if side == "l" else "droits"
    if head in {"branche", "racine", "corde", "division", "queue"}:
        return "gauche" if side == "l" else "droite"
    return "gauche" if side == "l" else "droit"


def french_name(object_name: str, side_override: str | None = None) -> tuple[str, str, str | None]:
    """Return (french with side, english base, side l/r/None)."""
    base, side = _strip_side(object_name)
    if side_override:
        side = side_override
    french = FR.get(base)
    if french is None:
        raise KeyError(base)
    if side:
        french = f"{french} {_side_word(french, side)}"
    return french, base, side


def slug_id(name_fr: str) -> str:
    nfd = unicodedata.normalize("NFD", name_fr)
    ascii_ = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    ascii_ = ascii_.replace("œ", "oe").replace("æ", "ae").replace("’", "")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")
    slug = f"za-{slug}"
    return slug[:96]


def region_for(base: str, mean: tuple[float, float, float]) -> str:
    n = base.lower()
    x, y, _z = mean
    if any(k in n for k in ("palmar", "dorsal digital branches of radial", "dorsal digital branches of ulnar")):
        return "main"
    if "plantar" in n or "cutaneous nerve of foot" in n or ("dorsal digital" in n and "fibular" in n):
        return "pied"
    if "sural" in n or "saphenous" in n or "fibular" in n or n == "tibial nerve":
        return "jambe"
    if any(k in n for k in ("median nerve", "ulnar nerve", "radial nerve", "interosseous nerve of forearm", "antebrachial")):
        return "membre-supérieur"
    if any(k in n for k in ("brachial plexus", "axillary", "musculocutaneous", "pectoral nerve", "subscapular", "thoracodorsal", "subclavian nerve", "suprascapular", "dorsal scapular")):
        return "membre-supérieur"
    if any(k in n for k in ("femoral nerve", "obturator", "sciatic", "gluteal", "pudendal", "femoral cutaneous", "piriformis", "quadratus femoris")):
        return "membre-inférieur"
    if any(k in n for k in ("optic", "olfactory", "oculomotor", "trochlear", "trigeminal", "abducens", "facial", "vestibulo", "vestibular", "cochlear", "glossopharyngeal", "vagus", "accessory", "hypoglossal", "ophthalmic", "maxillary", "mandibular", "lingual", "alveolar", "mental", "buccal", "chorda", "mylohyoid")):
        return "tête"
    if "intercostal" in n or "sympathetic" in n or "spinal" in n or "cauda" in n:
        return "tronc"
    if y > 0.45:
        return "tête"
    if abs(x) > 0.18 and y > -0.15:
        return "membre-supérieur"
    if y < -0.35:
        return "membre-inférieur"
    return "tronc"
