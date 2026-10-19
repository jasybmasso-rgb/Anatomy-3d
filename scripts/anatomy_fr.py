"""English BodyParts3D labels → display French (fr-CA) for viscera catalogs."""

from __future__ import annotations

import re
import unicodedata

# Longest phrases first.
_PHRASES: list[tuple[str, str]] = [
    ("superior vena cava", "veine cave supérieure"),
    ("inferior vena cava", "veine cave inférieure"),
    ("internal jugular vein", "veine jugulaire interne"),
    ("external jugular vein", "veine jugulaire externe"),
    ("common carotid artery", "artère carotide commune"),
    ("internal carotid artery", "artère carotide interne"),
    ("external carotid artery", "artère carotide externe"),
    ("common iliac artery", "artère iliaque commune"),
    ("external iliac artery", "artère iliaque externe"),
    ("internal iliac artery", "artère iliaque interne"),
    ("common iliac vein", "veine iliaque commune"),
    ("external iliac vein", "veine iliaque externe"),
    ("internal iliac vein", "veine iliaque interne"),
    ("brachiocephalic artery", "tronc brachio-céphalique"),
    ("brachiocephalic vein", "veine brachiocéphalique"),
    ("pulmonary trunk", "tronc pulmonaire"),
    ("pulmonary arterial trunk", "tronc pulmonaire"),
    ("hepatic portal vein", "veine porte"),
    ("great saphenous vein", "grande veine saphène"),
    ("small saphenous vein", "petite veine saphène"),
    ("great cardiac vein", "grande veine cardiaque"),
    ("middle cardiac vein", "veine cardiaque moyenne"),
    ("coronary sinus", "sinus coronaire"),
    ("ascending aorta", "aorte ascendante"),
    ("arch of aorta", "arc aortique"),
    ("abdominal aorta", "aorte abdominale"),
    ("descending thoracic aorta", "aorte thoracique descendante"),
    ("descending aorta", "aorte descendante"),
    ("trunk of right coronary artery", "artère coronaire droite"),
    ("trunk of left coronary artery", "artère coronaire gauche"),
    ("anterior interventricular branch of left coronary artery", "artère interventriculaire antérieure"),
    ("circumflex branch of left coronary artery", "artère circonflexe"),
    ("optic chiasm", "chiasma optique"),
    ("optic tract", "tractus optique"),
    ("optic nerve", "nerf optique"),
    ("trochlear nerve", "nerf trochléaire"),
    ("oculomotor nerve", "nerf oculomoteur"),
    ("trigeminal nerve", "nerf trijumeau"),
    ("ophthalmic nerve", "nerf ophtalmique"),
    ("ciliary ganglion", "ganglion ciliaire"),
    ("short ciliary nerve", "nerfs ciliaires courts"),
    ("long ciliary nerve", "nerf ciliaire long"),
    ("urinary bladder", "vessie"),
    ("adrenal gland", "glande surrénale"),
    ("pituitary gland", "hypophyse"),
    ("salivary gland", "glande salivaire"),
    ("major salivary gland", "glandes salivaires majeures"),
    ("small intestine", "intestin grêle"),
    ("large intestine", "gros intestin"),
    ("cerebral hemisphere", "hémisphère cérébral"),
    ("white matter", "substance blanche"),
    ("gray matter", "substance grise"),
    ("main bronchus", "bronche souche"),
    ("segment of bronchial tree", "arbre bronchique"),
    ("pulmonary segment of bronchial tree", "arbre bronchique pulmonaire"),
    ("caudate lobe of liver", "lobe caudé du foie"),
    ("wall of right atrium", "paroi de l’oreillette droite"),
    ("wall of left atrium", "paroi de l’oreillette gauche"),
    ("cavity of right atrium", "cavité de l’oreillette droite"),
    ("cavity of left atrium", "cavité de l’oreillette gauche"),
    ("cavity of right ventricle", "cavité du ventricule droit"),
    ("cavity of left ventricle", "cavité du ventricule gauche"),
    ("wall of right ventricle", "paroi du ventricule droit"),
    ("wall of left ventricle", "paroi du ventricule gauche"),
]

_WORDS: list[tuple[str, str]] = [
    ("artery", "artère"),
    ("vein", "veine"),
    ("aorta", "aorte"),
    ("nerve", "nerf"),
    ("plexus", "plexus"),
    ("ganglion", "ganglion"),
    ("trunk", "tronc"),
    ("branch", "branche"),
    ("tributary", "affluent"),
    ("common", "commune"),
    ("internal", "interne"),
    ("external", "externe"),
    ("anterior", "antérieure"),
    ("posterior", "postérieure"),
    ("superior", "supérieure"),
    ("inferior", "inférieure"),
    ("middle", "moyenne"),
    ("medial", "médiale"),
    ("lateral", "latérale"),
    ("deep", "profonde"),
    ("superficial", "superficielle"),
    ("ascending", "ascendante"),
    ("descending", "descendante"),
    ("femoral", "fémorale"),
    ("popliteal", "poplitée"),
    ("tibial", "tibiale"),
    ("fibular", "fibulaire"),
    ("radial", "radiale"),
    ("ulnar", "ulnaire"),
    ("brachial", "brachiale"),
    ("axillary", "axillaire"),
    ("subclavian", "subclavière"),
    ("vertebral", "vertébrale"),
    ("carotid", "carotide"),
    ("jugular", "jugulaire"),
    ("iliac", "iliaque"),
    ("renal", "rénale"),
    ("hepatic", "hépatique"),
    ("splenic", "splénique"),
    ("gastric", "gastrique"),
    ("mesenteric", "mésentérique"),
    ("celiac", "cœliaque"),
    ("coronary", "coronaire"),
    ("pulmonary", "pulmonaire"),
    ("basilic", "basilique"),
    ("cephalic", "céphalique"),
    ("saphenous", "saphène"),
    ("azygos", "azygos"),
    ("portal", "porte"),
    ("thyroid", "thyroïdienne"),
    ("phrenic", "phrénique"),
    ("epigastric", "épigastrique"),
    ("circumflex", "circonflexe"),
    ("interosseous", "interosseuse"),
    ("intercostal", "intercostale"),
    ("lumbar", "lombaire"),
    ("sacral", "sacrée"),
    ("cervical", "cervicale"),
    ("thoracic", "thoracique"),
    ("abdominal", "abdominale"),
    ("cerebral", "cérébrale"),
    ("cerebellar", "cérébelleuse"),
    ("basilar", "basilaire"),
    ("communicating", "communicante"),
    ("oculomotor", "oculomoteur"),
    ("ophthalmic", "ophtalmique"),
    ("with", "avec"),
    ("lacrimal", "lacrymal"),
    ("frontal", "frontal"),
    ("nasociliary", "naso-ciliaire"),
    ("ethmoidal", "ethmoïdal"),
    ("ciliary", "ciliaire"),
    ("supra-orbital", "supra-orbitaire"),
    ("supratrochlear", "supra-trochléaire"),
    ("infratrochlear", "infra-trochléaire"),
    ("kidney", "rein"),
    ("liver", "foie"),
    ("spleen", "rate"),
    ("stomach", "estomac"),
    ("pancreas", "pancréas"),
    ("bladder", "vessie"),
    ("gallbladder", "vésicule biliaire"),
    ("esophagus", "œsophage"),
    ("trachea", "trachée"),
    ("bronchus", "bronche"),
    ("colon", "côlon"),
    ("rectum", "rectum"),
    ("ileum", "iléon"),
    ("jejunum", "jéjunum"),
    ("duodenum", "duodénum"),
    ("prostate", "prostate"),
    ("testis", "testicule"),
    ("thymus", "thymus"),
    ("cornea", "cornée"),
    ("sclera", "sclérotique"),
    ("lens", "cristallin"),
    ("retina", "rétine"),
    ("cerebellum", "cervelet"),
    ("thalamus", "thalamus"),
    ("hypothalamus", "hypothalamus"),
    ("hippocampus", "hippocampe"),
    ("amygdala", "amygdale"),
    ("pons", "pont"),
    ("midbrain", "mésencéphale"),
    ("proper", "propre"),
    ("of", "de"),
    ("and", "et"),
]


_FEMININE_HEAD = (
    "artère",
    "veine",
    "aorte",
    "branche",
    "bronche",
    "glande",
    "vessie",
    "rate",
    "trachée",
    "cornée",
    "sclérotique",
    "rétine",
    "amygdale",
    "substance",
    "paroi",
    "cavité",
    "hypophyse",
    "prostate",
    "vésicule",
)


_HEAD_NOUNS: list[tuple[str, str, bool]] = [
    ("artery", "artère", True),
    ("vein", "veine", True),
    ("nerve", "nerf", False),
    ("ganglion", "ganglion", False),
    ("plexus", "plexus", False),
    ("trunk", "tronc", False),
    ("aorta", "aorte", True),
]


def _elide_de(head: str, feminine: bool = False) -> str:
    if not head:
        return "de"
    body = head[0].lower() + head[1:]
    if body[0] in "aeiouéèêàâîïù":
        return f"de l’{body}"
    if feminine:
        return f"de la {body}"
    return f"du {body}"


def _translate_core(low: str) -> tuple[str, bool]:
    low = re.sub(r"\s+", " ", low).strip()
    for src, dst in _PHRASES:
        if low == src:
            head = dst.split()[0].lower()
            return dst, head in _FEMININE_HEAD
    if " with " in low:
        left, right = low.split(" with ", 1)
        a, _ = _translate_core(left)
        b, fem = _translate_core(right)
        b_low = b[0].lower() + b[1:] if b else b
        return f"{a} avec {b_low}", fem
    if low.endswith(" artery proper"):
        rest = _apply_words(_apply_phrases(low[: -len(" artery proper")])).strip()
        return (f"artère {rest} propre" if rest else "artère propre"), True
    m = re.match(r"^(.*?)branch of (.+)$", low)
    if m:
        qual = _apply_words(_apply_phrases(m.group(1).strip())).strip()
        inner, inner_fem = _translate_core(m.group(2).strip())
        de = _elide_de(inner, inner_fem)
        if qual:
            return f"branche {qual} {de}", True
        return f"branche {de}", True
    m = re.match(r"^trunk of (.+)$", low)
    if m:
        inner, inner_fem = _translate_core(m.group(1).strip())
        return f"tronc {_elide_de(inner, inner_fem)}", False
    for en_n, fr_n, fem in _HEAD_NOUNS:
        if low == en_n:
            return fr_n, fem
        suffix = f" {en_n}"
        if low.endswith(suffix):
            rest = low[: -len(suffix)].strip()
            rest_fr = _apply_words(_apply_phrases(rest)).strip()
            if rest_fr:
                return f"{fr_n} {rest_fr}", fem
            return fr_n, fem
    fr = _apply_words(_apply_phrases(low))
    fr = re.sub(r"\s+", " ", fr).strip()
    head = fr.split()[0].lower() if fr else ""
    return fr, head in _FEMININE_HEAD


def _strip_side(en: str) -> tuple[str, str | None]:
    text = re.sub(r"\s+", " ", en.strip())
    found = re.findall(r"\b(left|right)\b", text, flags=re.I)
    side = None
    if found:
        side = "gauche" if found[0].lower() == "left" else "droit"
    core = re.sub(r"\b(left|right)\b", " ", text, flags=re.I)
    return re.sub(r"\s+", " ", core).strip(), side


def translate_en(en: str) -> str:
    core, side = _strip_side(en)
    low = core.lower().strip()
    fr, feminine = _translate_core(low)
    fr = re.sub(r"\s+", " ", fr).strip()
    if fr:
        fr = fr[0].upper() + fr[1:]
    if side:
        adj = "droite" if feminine and side == "droit" else (
            "gauche" if feminine and side == "gauche" else (
                "droit" if side == "droit" else "gauche"
            )
        )
        fr = f"{fr} {adj}"
    return fr


def _apply_phrases(low: str) -> str:
    out = low
    for src, dst in sorted(_PHRASES, key=lambda kv: -len(kv[0])):
        out = out.replace(src, dst)
    return out


def _apply_words(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        word = match.group(0).lower()
        for src, dst in _WORDS:
            if word == src:
                return dst
        return match.group(0)

    return re.sub(r"[A-Za-zàâäéèêëïîôùûüçœ-]+", repl, text)


def slug_id(name_fr: str, prefix: str = "") -> str:
    nfd = unicodedata.normalize("NFD", name_fr)
    ascii_ = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    ascii_ = ascii_.replace("œ", "oe").replace("æ", "ae")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")
    if prefix:
        slug = f"{prefix}-{slug}" if not slug.startswith(prefix) else slug
    return slug[:80]


def region_from_point(x: float, y: float, z: float) -> str:  # noqa: ARG001
    if y > 0.58:
        return "tête"
    if y > 0.42:
        return "cou"
    if abs(x) > 0.16 and y > -0.05:
        return "membre-supérieur"
    if abs(x) > 0.08 and y < -0.12:
        return "membre-inférieur"
    return "tronc"
