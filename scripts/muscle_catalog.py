"""French pedagogical copy for BodyParts3D skeletal muscles (O / I / actions / heads)."""

from __future__ import annotations

from typing import Any

Region = str


def _h(name: str, origin: str, insertion: str) -> dict[str, str]:
    return {"name": name, "origin": origin, "insertion": insertion}


# group_key -> (French name, Latin, aliases, region)
NAMES: dict[str, tuple[str, str, list[str], Region]] = {
    "biceps brachii": ("Biceps brachial", "Musculus biceps brachii", ["biceps", "biceps du bras", "biceps brachii"], "membre-supérieur"),
    "triceps brachii": ("Triceps brachial", "Musculus triceps brachii", ["triceps", "triceps du bras"], "membre-supérieur"),
    "deltoid": ("Deltoïde", "Musculus deltoideus", ["deltoide", "deltoid"], "épaule"),
    "pectoralis major": ("Grand pectoral", "Musculus pectoralis major", ["pectoralis major", "pectoraux"], "tronc"),
    "pectoralis minor": ("Petit pectoral", "Musculus pectoralis minor", ["pectoralis minor"], "tronc"),
    "trapezius": ("Trapèze", "Musculus trapezius", ["trapeze", "trapezius"], "dos"),
    "sternocleidomastoid": ("Sterno-cléido-mastoïdien", "Musculus sternocleidomastoideus", ["SCM", "sterno-cléido-mastoïdien"], "cou"),
    "biceps femoris": ("Biceps fémoral", "Musculus biceps femoris", ["biceps crural", "biceps femoris"], "membre-inférieur"),
    "semitendinosus": ("Semi-tendineux", "Musculus semitendinosus", ["semitendinosus"], "membre-inférieur"),
    "semimembranosus": ("Semi-membraneux", "Musculus semimembranosus", ["semimembranosus"], "membre-inférieur"),
    "rectus femoris": ("Droit fémoral", "Musculus rectus femoris", ["droit antérieur", "rectus femoris"], "membre-inférieur"),
    "vastus lateralis": ("Vaste latéral", "Musculus vastus lateralis", ["vaste externe"], "membre-inférieur"),
    "vastus medialis": ("Vaste médial", "Musculus vastus medialis", ["vaste interne"], "membre-inférieur"),
    "vastus intermedius": ("Vaste intermédiaire", "Musculus vastus intermedius", ["crural"], "membre-inférieur"),
    "gluteus maximus": ("Grand fessier", "Musculus gluteus maximus", ["gluteus maximus"], "membre-inférieur"),
    "gluteus medius": ("Moyen fessier", "Musculus gluteus medius", ["gluteus medius"], "membre-inférieur"),
    "gluteus minimus": ("Petit fessier", "Musculus gluteus minimus", ["gluteus minimus"], "membre-inférieur"),
    "iliopsoas": ("Iliopsoas", "Musculus iliopsoas", ["ilio-psoas", "psoas-iliaque"], "membre-inférieur"),
    "iliacus": ("Iliaque", "Musculus iliacus", ["iliacus"], "membre-inférieur"),
    "psoas major": ("Psoas major", "Musculus psoas major", ["psoas"], "tronc"),
    "gastrocnemius": ("Gastrocnémien", "Musculus gastrocnemius", ["jumeaux", "gastrocnemius"], "membre-inférieur"),
    "soleus": ("Soléaire", "Musculus soleus", ["soleus"], "membre-inférieur"),
    "tibialis anterior": ("Tibial antérieur", "Musculus tibialis anterior", ["tibialis anterior"], "membre-inférieur"),
    "tibialis posterior": ("Tibial postérieur", "Musculus tibialis posterior", ["tibialis posterior"], "membre-inférieur"),
    "external oblique": ("Oblique externe", "Musculus obliquus externus abdominis", ["grand oblique"], "tronc"),
    "supraspinatus": ("Supra-épineux", "Musculus supraspinatus", ["sus-épineux"], "épaule"),
    "infraspinatus": ("Infra-épineux", "Musculus infraspinatus", ["sous-épineux"], "épaule"),
    "subscapularis": ("Subscapulaire", "Musculus subscapularis", ["sous-scapulaire"], "épaule"),
    "teres major": ("Grand rond", "Musculus teres major", ["teres major"], "épaule"),
    "teres minor": ("Petit rond", "Musculus teres minor", ["teres minor"], "épaule"),
    "latissimus dorsi": ("Grand dorsal", "Musculus latissimus dorsi", ["latissimus", "grand dorsal"], "dos"),
    "rectus abdominis": ("Droit de l’abdomen", "Musculus rectus abdominis", ["grands droits", "abdos"], "tronc"),
    "brachialis": ("Brachial", "Musculus brachialis", ["brachial antérieur"], "membre-supérieur"),
    "brachioradialis": ("Brachio-radial", "Musculus brachioradialis", ["long supinateur"], "membre-supérieur"),
    "coracobrachialis": ("Coraco-brachial", "Musculus coracobrachialis", ["coracobrachialis"], "membre-supérieur"),
    "anconeus": ("Anconé", "Musculus anconeus", ["anconeus"], "membre-supérieur"),
    "supinator": ("Supinateur", "Musculus supinator", ["court supinateur"], "membre-supérieur"),
    "pronator teres": ("Rond pronateur", "Musculus pronator teres", ["pronator teres"], "membre-supérieur"),
    "pronator quadratus": ("Carré pronateur", "Musculus pronator quadratus", ["pronator quadratus"], "membre-supérieur"),
    "flexor carpi radialis": ("Fléchisseur radial du carpe", "Musculus flexor carpi radialis", ["grand palmaire"], "membre-supérieur"),
    "flexor carpi ulnaris": ("Fléchisseur ulnaire du carpe", "Musculus flexor carpi ulnaris", ["cubital antérieur"], "membre-supérieur"),
    "palmaris longus": ("Long palmaire", "Musculus palmaris longus", ["petit palmaire"], "membre-supérieur"),
    "flexor digitorum superficialis": ("Fléchisseur superficiel des doigts", "Musculus flexor digitorum superficialis", ["FDS"], "membre-supérieur"),
    "flexor digitorum profundus": ("Fléchisseur profond des doigts", "Musculus flexor digitorum profundus", ["FDP"], "membre-supérieur"),
    "flexor pollicis longus": ("Long fléchisseur du pouce", "Musculus flexor pollicis longus", ["FPL"], "membre-supérieur"),
    "extensor carpi radialis longus": ("Long extenseur radial du carpe", "Musculus extensor carpi radialis longus", ["premier radial"], "membre-supérieur"),
    "extensor carpi radialis brevis": ("Court extenseur radial du carpe", "Musculus extensor carpi radialis brevis", ["deuxième radial"], "membre-supérieur"),
    "extensor carpi ulnaris": ("Extenseur ulnaire du carpe", "Musculus extensor carpi ulnaris", ["cubital postérieur"], "membre-supérieur"),
    "extensor digitorum": ("Extenseur des doigts", "Musculus extensor digitorum", ["extenseur commun"], "membre-supérieur"),
    "extensor digiti minimi": ("Extenseur du petit doigt", "Musculus extensor digiti minimi", ["extenseur propre du 5e"], "membre-supérieur"),
    "extensor indicis": ("Extenseur de l’index", "Musculus extensor indicis", ["extenseur propre de l’index"], "membre-supérieur"),
    "extensor pollicis longus": ("Long extenseur du pouce", "Musculus extensor pollicis longus", ["EPL"], "membre-supérieur"),
    "extensor pollicis brevis": ("Court extenseur du pouce", "Musculus extensor pollicis brevis", ["EPB"], "membre-supérieur"),
    "abductor pollicis longus": ("Long abducteur du pouce", "Musculus abductor pollicis longus", ["APL"], "membre-supérieur"),
    "abductor pollicis brevis": ("Court abducteur du pouce", "Musculus abductor pollicis brevis", ["APB"], "main"),
    "flexor pollicis brevis": ("Court fléchisseur du pouce", "Musculus flexor pollicis brevis", ["FPB"], "main"),
    "opponens pollicis": ("Opposant du pouce", "Musculus opponens pollicis", ["opposant"], "main"),
    "adductor pollicis": ("Adducteur du pouce", "Musculus adductor pollicis", ["adducteur du I"], "main"),
    "abductor digiti minimi of hand": ("Abducteur du petit doigt", "Musculus abductor digiti minimi manus", ["abducteur du V"], "main"),
    "flexor digiti minimi brevis of hand": ("Court fléchisseur du petit doigt", "Musculus flexor digiti minimi brevis manus", ["fléchisseur du V"], "main"),
    "opponens digiti minimi of hand": ("Opposant du petit doigt", "Musculus opponens digiti minimi manus", ["opposant du V"], "main"),
    "subclavius": ("Subclavier", "Musculus subclavius", ["sous-clavier"], "épaule"),
    "levator scapulae": ("Élévateur de la scapula", "Musculus levator scapulae", ["angulaire de l’omoplate"], "dos"),
    "rhomboid major": ("Grand rhomboïde", "Musculus rhomboideus major", ["rhomboïde major"], "dos"),
    "rhomboid minor": ("Petit rhomboïde", "Musculus rhomboideus minor", ["rhomboïde minor"], "dos"),
    "serratus anterior": ("Dentelé antérieur", "Musculus serratus anterior", ["grand dentelé"], "tronc"),
    "serratus posterior superior": ("Dentelé postérieur supérieur", "Musculus serratus posterior superior", ["SPS"], "dos"),
    "serratus posterior inferior": ("Dentelé postérieur inférieur", "Musculus serratus posterior inferior", ["SPI"], "dos"),
    "splenius capitis": ("Splénius de la tête", "Musculus splenius capitis", ["splenius capitis"], "cou"),
    "splenius cervicis": ("Splénius du cou", "Musculus splenius cervicis", ["splenius cervicis"], "cou"),
    "semispinalis capitis": ("Semi-épineux de la tête", "Musculus semispinalis capitis", ["complexus"], "cou"),
    "semispinalis cervicis": ("Semi-épineux du cou", "Musculus semispinalis cervicis", ["semispinalis cervicis"], "cou"),
    "semispinalis thoracis": ("Semi-épineux du thorax", "Musculus semispinalis thoracis", ["semispinalis thoracis"], "dos"),
    "iliocostalis cervicis": ("Iliocostal cervical", "Musculus iliocostalis cervicis", ["iliocostalis cervicis"], "cou"),
    "iliocostalis thoracis": ("Iliocostal thoracique", "Musculus iliocostalis thoracis", ["iliocostalis thoracis"], "dos"),
    "iliocostalis lumborum": ("Iliocostal lombaire", "Musculus iliocostalis lumborum", ["iliocostalis lumborum"], "dos"),
    "longissimus capitis": ("Longissimus de la tête", "Musculus longissimus capitis", ["longissimus capitis"], "cou"),
    "longissimus cervicis": ("Longissimus du cou", "Musculus longissimus cervicis", ["longissimus cervicis"], "cou"),
    "longissimus thoracis": ("Longissimus du thorax", "Musculus longissimus thoracis", ["longissimus thoracis"], "dos"),
    "spinalis thoracis": ("Épineux du thorax", "Musculus spinalis thoracis", ["spinalis thoracis"], "dos"),
    "cervical rotator": ("Rotateurs cervicaux", "Musculi rotatores cervicis", ["rotatores colli"], "cou"),
    "thoracic rotator": ("Rotateurs thoraciques", "Musculi rotatores thoracis", ["rotatores thoracis"], "dos"),
    "lumbar rotator": ("Rotateurs lombaires", "Musculi rotatores lumborum", ["rotatores lumborum"], "dos"),
    "interspinalis thoracis": ("Inter-épineux thoraciques", "Musculi interspinales thoracis", ["interspinalis thoracis"], "dos"),
    "lateral lumbar intertransversarius": ("Intertransversaire lombaire latéral", "Musculus intertransversarius lateralis lumborum", ["intertransversaire latéral"], "dos"),
    "medial lumbar intertransversarius": ("Intertransversaire lombaire médial", "Musculus intertransversarius medialis lumborum", ["intertransversaire médial"], "dos"),
    "scalenus anterior": ("Scalène antérieur", "Musculus scalenus anterior", ["scalenus anterior"], "cou"),
    "scalenus medius": ("Scalène moyen", "Musculus scalenus medius", ["scalenus medius"], "cou"),
    "scalenus posterior": ("Scalène postérieur", "Musculus scalenus posterior", ["scalenus posterior"], "cou"),
    "longus capitis": ("Long de la tête", "Musculus longus capitis", ["longus capitis"], "cou"),
    "longus colli": ("Long du cou", "Musculus longus colli", ["longus colli"], "cou"),
    "rectus capitis anterior": ("Droit antérieur de la tête", "Musculus rectus capitis anterior", ["rectus capitis anterior"], "cou"),
    "rectus capitis lateralis": ("Droit latéral de la tête", "Musculus rectus capitis lateralis", ["rectus capitis lateralis"], "cou"),
    "rectus capitis posterior major": ("Grand droit postérieur de la tête", "Musculus rectus capitis posterior major", ["RCP major"], "cou"),
    "rectus capitis posterior minor": ("Petit droit postérieur de la tête", "Musculus rectus capitis posterior minor", ["RCP minor"], "cou"),
    "obliquus capitis inferior": ("Oblique inférieur de la tête", "Musculus obliquus capitis inferior", ["OCI"], "cou"),
    "obliquus capitis superior": ("Oblique supérieur de la tête", "Musculus obliquus capitis superior", ["OCS"], "cou"),
    "platysma": ("Peaucier du cou", "Platysma", ["platysma"], "cou"),
    "digastric": ("Digastrique", "Musculus digastricus", ["digastrique"], "cou"),
    "mylohyoid": ("Mylo-hyoïdien", "Musculus mylohyoideus", ["mylohyoid"], "cou"),
    "geniohyoid": ("Génio-hyoïdien", "Musculus geniohyoideus", ["geniohyoid"], "cou"),
    "stylohyoid": ("Stylo-hyoïdien", "Musculus stylohyoideus", ["stylohyoid"], "cou"),
    "omohyoid": ("Omo-hyoïdien", "Musculus omohyoideus", ["omohyoid"], "cou"),
    "sternohyoid": ("Sterno-hyoïdien", "Musculus sternohyoideus", ["sternohyoid"], "cou"),
    "sternothyroid": ("Sterno-thyroïdien", "Musculus sternothyroideus", ["sternothyroid"], "cou"),
    "thyrohyoid": ("Thyro-hyoïdien", "Musculus thyrohyoideus", ["thyrohyoid"], "cou"),
    "external intercostal muscle": ("Intercostaux externes", "Musculi intercostales externi", ["intercostaux externes"], "tronc"),
    "internal intercostal muscle": ("Intercostaux internes", "Musculi intercostales interni", ["intercostaux internes"], "tronc"),
    "innermost intercostal muscle": ("Intercostaux intimes", "Musculi intercostales intimi", ["intercostaux intimes"], "tronc"),
    "transversus thoracis": ("Transverse du thorax", "Musculus transversus thoracis", ["triangulaire du sternum"], "tronc"),
    "diaphragm": ("Diaphragme", "Diaphragma", ["diaphragme"], "tronc"),
    "sartorius": ("Sartorius", "Musculus sartorius", ["couturier"], "membre-inférieur"),
    "gracilis": ("Gracile", "Musculus gracilis", ["droit interne"], "membre-inférieur"),
    "pectineus": ("Pectiné", "Musculus pectineus", ["pectineus"], "membre-inférieur"),
    "adductor longus": ("Long adducteur", "Musculus adductor longus", ["adductor longus"], "membre-inférieur"),
    "adductor brevis": ("Court adducteur", "Musculus adductor brevis", ["adductor brevis"], "membre-inférieur"),
    "adductor magnus": ("Grand adducteur", "Musculus adductor magnus", ["adductor magnus"], "membre-inférieur"),
    "adductor minimus": ("Petit adducteur", "Musculus adductor minimus", ["adductor minimus"], "membre-inférieur"),
    "tensor fasciae latae": ("Tenseur du fascia lata", "Musculus tensor fasciae latae", ["TFL"], "membre-inférieur"),
    "piriformis": ("Piriforme", "Musculus piriformis", ["pyramidal du bassin"], "membre-inférieur"),
    "obturator internus": ("Obturateur interne", "Musculus obturatorius internus", ["obturateur interne"], "membre-inférieur"),
    "obturator externus": ("Obturateur externe", "Musculus obturatorius externus", ["obturateur externe"], "membre-inférieur"),
    "gemellus superior": ("Jumeau supérieur", "Musculus gemellus superior", ["gemellus superior"], "membre-inférieur"),
    "gemellus inferior": ("Jumeau inférieur", "Musculus gemellus inferior", ["gemellus inferior"], "membre-inférieur"),
    "quadratus femoris": ("Carré fémoral", "Musculus quadratus femoris", ["carré crural"], "membre-inférieur"),
    "plantaris": ("Plantaire", "Musculus plantaris", ["plantaire grêle"], "membre-inférieur"),
    "popliteus": ("Poplité", "Musculus popliteus", ["popliteus"], "membre-inférieur"),
    "fibularis longus": ("Long fibulaire", "Musculus fibularis longus", ["long péronier latéral"], "membre-inférieur"),
    "fibularis brevis": ("Court fibulaire", "Musculus fibularis brevis", ["court péronier"], "membre-inférieur"),
    "fibularis tertius": ("Troisième fibulaire", "Musculus fibularis tertius", ["péronier antérieur"], "membre-inférieur"),
    "extensor digitorum longus": ("Extenseur long des orteils", "Musculus extensor digitorum longus", ["EDL"], "membre-inférieur"),
    "extensor hallucis longus": ("Extenseur long de l’hallux", "Musculus extensor hallucis longus", ["EHL"], "membre-inférieur"),
    "flexor digitorum longus": ("Fléchisseur long des orteils", "Musculus flexor digitorum longus", ["FDL"], "membre-inférieur"),
    "flexor hallucis longus": ("Fléchisseur long de l’hallux", "Musculus flexor hallucis longus", ["FHL"], "membre-inférieur"),
    "extensor hallucis brevis": ("Court extenseur de l’hallux", "Musculus extensor hallucis brevis", ["EHB"], "pied"),
    "flexor digitorum brevis": ("Court fléchisseur des orteils", "Musculus flexor digitorum brevis", ["FDB"], "pied"),
    "abductor hallucis": ("Abducteur de l’hallux", "Musculus abductor hallucis", ["abducteur du I"], "pied"),
    "abductor digiti minimi of foot": ("Abducteur du petit orteil", "Musculus abductor digiti minimi pedis", ["abducteur du V pied"], "pied"),
    "flexor hallucis brevis": ("Court fléchisseur de l’hallux", "Musculus flexor hallucis brevis", ["FHB"], "pied"),
    "adductor hallucis": ("Adducteur de l’hallux", "Musculus adductor hallucis", ["adducteur du I pied"], "pied"),
    "flexor digiti minimi brevis of foot": ("Court fléchisseur du petit orteil", "Musculus flexor digiti minimi brevis pedis", ["fléchisseur du V pied"], "pied"),
    "opponens digiti minimi of foot": ("Opposant du petit orteil", "Musculus opponens digiti minimi pedis", ["opposant du V pied"], "pied"),
    "flexor accessorius": ("Carré plantaire", "Musculus quadratus plantae", ["flexor accessorius"], "pied"),
    "first lumbrical of foot": ("Premier lombrical du pied", "Musculus lumbricalis I pedis", ["lombrical 1 pied"], "pied"),
    "second lumbrical of foot": ("Deuxième lombrical du pied", "Musculus lumbricalis II pedis", ["lombrical 2 pied"], "pied"),
    "third lumbrical of foot": ("Troisième lombrical du pied", "Musculus lumbricalis III pedis", ["lombrical 3 pied"], "pied"),
    "fourth lumbrical of foot": ("Quatrième lombrical du pied", "Musculus lumbricalis IV pedis", ["lombrical 4 pied"], "pied"),
    "first plantar interosseous of foot": ("Premier interosseux plantaire", "Musculus interosseus plantaris I", ["interosseux plantaire 1"], "pied"),
    "second plantar interosseous of foot": ("Deuxième interosseux plantaire", "Musculus interosseus plantaris II", ["interosseux plantaire 2"], "pied"),
    "third plantar interosseous of foot": ("Troisième interosseux plantaire", "Musculus interosseus plantaris III", ["interosseux plantaire 3"], "pied"),
    "coccygeus": ("Coccygien", "Musculus coccygeus", ["ischio-coccygien"], "périnée"),
    "iliococcygeus": ("Ilio-coccygien", "Musculus iliococcygeus", ["iliococcygeus"], "périnée"),
    "pubococcygeus": ("Pubo-coccygien", "Musculus pubococcygeus", ["pubococcygeus"], "périnée"),
    "puborectalis": ("Pubo-rectal", "Musculus puborectalis", ["puborectalis"], "périnée"),
    "external anal sphincter": ("Sphincter anal externe", "Musculus sphincter ani externus", ["sphincter anal"], "périnée"),
}

# Extra fallback names for keys that may appear after expansion.
_WORD_FR = {
    "abductor": "Abducteur",
    "adductor": "Adducteur",
    "flexor": "Fléchisseur",
    "extensor": "Extenseur",
    "opponens": "Opposant",
    "levator": "Élévateur",
    "tensor": "Tenseur",
    "pronator": "Pronateur",
    "supinator": "Supinateur",
    "of": "de",
    "the": "",
    "foot": "pied",
    "hand": "main",
    "head": "chef",
    "muscle": "",
}


def french_name_for(key: str) -> str:
    if key in NAMES:
        return NAMES[key][0]
    parts = [p for p in key.split() if p not in {"the"}]
    out = []
    for p in parts:
        out.append(_WORD_FR.get(p, p))
    return " ".join(w for w in out if w).strip().capitalize() or key


def latin_for(key: str) -> str:
    if key in NAMES:
        return NAMES[key][1]
    return f"Musculus {key}"


def aliases_for(key: str) -> list[str]:
    if key in NAMES:
        return list(NAMES[key][2])
    return [key]


def region_for(key: str) -> Region:
    if key in NAMES:
        return NAMES[key][3]
    k = key.lower()
    if any(w in k for w in ("pollicis", "digiti minimi of hand", "palmar", "carpi", "indicis")):
        return "main" if any(w in k for w in ("brevis", "opponens", "abductor pollicis brevis", "adductor pollicis")) else "membre-supérieur"
    if any(w in k for w in ("halluc", "pedis", "of foot", "plantar", "lumbrical of foot")):
        return "pied"
    if any(w in k for w in ("capitis", "colli", "cervic", "hyoid", "scalen", "platysma", "digastric")):
        return "cou"
    if any(w in k for w in ("spinatus", "deltoid", "teres", "subscapular", "subclav")):
        return "épaule"
    if any(w in k for w in ("iliocost", "longissim", "spinalis", "rhomboid", "trapez", "latissim", "rotator", "serratus posterior")):
        return "dos"
    if any(w in k for w in ("coccy", "pubo", "ilio-cocc", "sphincter", "perine")):
        return "périnée"
    if any(w in k for w in ("oblique", "intercostal", "diaphragm", "pectoral", "transversus")):
        return "tronc"
    if any(w in k for w in ("femor", "glute", "vastus", "sartor", "gracilis", "adductor", "gastroc", "soleus", "tibial", "fibular", "poplit")):
        return "membre-inférieur"
    if any(w in k for w in ("brach", "triceps", "biceps brach", "ancone", "supinator", "pronator")):
        return "membre-supérieur"
    return "tronc"


ANATOMY: dict[str, dict[str, Any]] = {}


def _a(
    key: str,
    origin: str,
    insertion: str,
    actions: list[str],
    secondary: list[str] | None = None,
    heads: list[dict[str, str]] | None = None,
) -> None:
    ANATOMY[key] = {
        "origin": origin,
        "insertion": insertion,
        "actions": actions,
        "secondaryActions": secondary or [],
        "heads": heads,
    }


_a(
    "biceps brachii",
    "Chef long : tubercule supra-glénoïdien de la scapula. Chef court : processus coracoïde.",
    "Tubérosité du radius et aponévrose bicipitale (lacertus fibrosus) vers le fascia antébrachial.",
    ["Flexion du coude", "Supination de l’avant-bras"],
    ["Flexion accessoire de l’épaule (surtout chef court)"],
    [
        _h("Chef long", "Tubercule supra-glénoïdien de la scapula (labrum adjacent).", "Tubérosité radiale et aponévrose bicipitale."),
        _h("Chef court", "Processus coracoïde de la scapula.", "Tubérosité radiale et aponévrose bicipitale."),
    ],
)
_a(
    "triceps brachii",
    "Chef long : tubercule infra-glénoïdien. Chef latéral : face postérieure de l’humérus au-dessus du sillon radial. Chef médial : face postérieure au-dessous de ce sillon.",
    "Face supérieure de l’olécrane de l’ulna et fascia antébrachial adjacent.",
    ["Extension du coude"],
    ["Adduction et extension de l’épaule (chef long)"],
    [
        _h("Chef long", "Tubercule infra-glénoïdien de la scapula.", "Olécrane."),
        _h("Chef latéral", "Face postérieure de l’humérus, au-dessus du sillon du nerf radial.", "Olécrane."),
        _h("Chef médial", "Face postérieure de l’humérus, au-dessous du sillon radial.", "Olécrane."),
    ],
)
_a(
    "deltoid",
    "Tiers latéral de la clavicule, bord latéral de l’acromion et épine de la scapula.",
    "Tubérosité deltoïdienne de l’humérus.",
    ["Abduction du bras (faisceau moyen / acromial)"],
    ["Flexion et rotation médiale (faisceau claviculaire)", "Extension et rotation latérale (faisceau spinal)"],
    [
        _h("Faisceau claviculaire", "Tiers latéral du bord antérieur de la clavicule.", "Tubérosité deltoïdienne."),
        _h("Faisceau acromial", "Bord latéral de l’acromion.", "Tubérosité deltoïdienne."),
        _h("Faisceau spinal", "Épine de la scapula.", "Tubérosité deltoïdienne."),
    ],
)
_a(
    "pectoralis major",
    "Faisceau claviculaire : moitié médiale de la clavicule. Sterno-costal : sternum et cartilages costaux 1–6. Abdominal : gaine du droit.",
    "Lèvre latérale du sillon intertuberculaire de l’humérus (tendon en U).",
    ["Adduction et rotation médiale du bras"],
    ["Flexion (faisceau claviculaire)", "Extension depuis une flexion (faisceau sterno-costal)"],
    [
        _h("Faisceau claviculaire", "Moitié médiale de la clavicule.", "Sillon intertuberculaire de l’humérus."),
        _h("Faisceau sterno-costal", "Sternum et cartilages costaux.", "Sillon intertuberculaire de l’humérus."),
        _h("Faisceau abdominal", "Gaine du muscle droit de l’abdomen.", "Sillon intertuberculaire de l’humérus."),
    ],
)
_a("pectoralis minor", "Face externe des côtes 3–5.", "Processus coracoïde.", ["Abaisse et bascule en avant la scapula"], ["Inspirateur accessoire"])
_a(
    "trapezius",
    "Ligne nuchale supérieure, ligament nuchal, processus épineux C7–T12.",
    "Tiers latéral de la clavicule, acromion et épine de la scapula.",
    ["Élévation de la scapula (descendant)", "Rétraction (transverse)", "Abaissement et rotation supérieure (ascendant)"],
    ["Extension cervicale (faisceaux descendants, action bilatérale)"],
    [
        _h("Faisceau descendant", "Ligne nuchale / ligament nuchal / C7.", "Clavicule latérale et acromion."),
        _h("Faisceau transverse", "Épineuses thoraciques hautes.", "Épine de la scapula."),
        _h("Faisceau ascendant", "Épineuses thoraciques basses.", "Épine de la scapula (racine)."),
    ],
)
_a("sternocleidomastoid", "Chef sternal : manubrium. Chef claviculaire : tiers médial de la clavicule.", "Processus mastoïde et ligne nuchale supérieure.", ["Inclinaison homolatérale et rotation controlatérale de la tête"], ["Flexion cervicale (bilatéral)", "Inspirateur accessoire"])
_a(
    "biceps femoris",
    "Chef long : tubérosité ischiatique. Chef court : lèvre latérale de la ligne âpre.",
    "Tête de la fibula (et condyle tibial latéral adjacent).",
    ["Flexion du genou", "Rotation latérale de jambe genou fléchi"],
    ["Extension de hanche (chef long)"],
    [
        _h("Chef long", "Tubérosité ischiatique (tendon commun avec le semi-tendineux).", "Tête de la fibula."),
        _h("Chef court", "Lèvre latérale de la ligne âpre et septum intermusculaire latéral.", "Tête de la fibula."),
    ],
)
_a("semitendinosus", "Tubérosité ischiatique.", "Face médiale du tibia proximal (patte d’oie).", ["Extension de hanche", "Flexion du genou", "Rotation médiale de jambe genou fléchi"])
_a("semimembranosus", "Tubérosité ischiatique.", "Condyle tibial médial (et fascia poplité / ligament poplité oblique).", ["Extension de hanche", "Flexion du genou", "Rotation médiale de jambe genou fléchi"])
_a("rectus femoris", "Épine iliaque antéro-inférieure et sillon supra-acétabulaire.", "Base de la patella puis tubérosité tibiale via le ligament patellaire.", ["Extension du genou"], ["Flexion de hanche"])
_a("vastus lateralis", "Grand trochanter, lèvre latérale de la ligne âpre.", "Patella et tubérosité tibiale (quadriceps).", ["Extension du genou"])
_a("vastus medialis", "Lèvre médiale de la ligne âpre et ligne intertrochantérique.", "Patella et tubérosité tibiale (quadriceps).", ["Extension du genou"], ["Stabilisation médiale de la patella"])
_a("vastus intermedius", "Face antérieure et latérale du fémur.", "Patella et tubérosité tibiale (quadriceps).", ["Extension du genou"])
_a("gluteus maximus", "Aile iliaque (derrière la ligne glutéale postérieure), sacrum, coccyx, ligament sacro-tubéral.", "Tractus ilio-tibial et tubérosité glutéale du fémur.", ["Extension de hanche", "Rotation latérale de hanche"], ["Stabilisation du genou via le TFL / tractus"])
_a("gluteus medius", "Face glutéale de l’ilium entre lignes glutéales antérieure et postérieure.", "Face latérale du grand trochanter.", ["Abduction de hanche"], ["Rotation médiale (fibres antérieures)", "Rotation latérale (fibres postérieures)"])
_a("gluteus minimus", "Ilium entre lignes glutéales antérieure et inférieure.", "Face antérieure du grand trochanter.", ["Abduction de hanche", "Rotation médiale de hanche"])
_a(
    "iliopsoas",
    "Psoas : flancs des vertèbres T12–L5 et disques, processus transverses lombaires. Iliaque : fosse iliaque.",
    "Petit trochanter du fémur (tendon commun).",
    ["Flexion de hanche"],
    ["Inclinaison du tronc (psoas)", "Rotation latérale accessoire de hanche"],
    [
        _h("Psoas major", "Vertèbres T12–L5, disques et transverses lombaires.", "Petit trochanter."),
        _h("Iliaque", "Fosse iliaque et lèvre interne de la crête.", "Petit trochanter."),
    ],
)
_a(
    "gastrocnemius",
    "Chef médial : condyle fémoral médial. Chef latéral : condyle fémoral latéral.",
    "Face postérieure du calcanéus via le tendon calcanéen.",
    ["Flexion plantaire de cheville"],
    ["Flexion du genou"],
    [
        _h("Chef médial", "Face postérieure du condyle fémoral médial.", "Tendon calcanéen."),
        _h("Chef latéral", "Face postérieure du condyle fémoral latéral.", "Tendon calcanéen."),
    ],
)
_a("soleus", "Tête et face postérieure de la fibula, ligne soléaire du tibia, arcade tendineuse.", "Calcanéus via le tendon calcanéen.", ["Flexion plantaire de cheville"], ["Postural (contrôle de l’avancée tibiale)"])
_a("tibialis anterior", "Condyle tibial latéral et face latérale du tibia, membrane interosseuse.", "Cunéiforme médial et base du 1er métatarsien.", ["Flexion dorsale de cheville", "Inversion du pied"])
_a("tibialis posterior", "Tibia, fibula et membrane interosseuse (loge postérieure profonde).", "Naviculaire, cunéiformes et bases métatarsiennes 2–4.", ["Inversion du pied", "Flexion plantaire accessoire"], ["Soutien de la voûte médiale"])
_a("external oblique", "Face externe des côtes 5–12.", "Ligne blanche, crête iliaque, ligament inguinal.", ["Flexion du tronc (bilatéral)", "Rotation controlatérale"], ["Expiration forcée", "Stabilisation abdominale"])
_a("supraspinatus", "Fosse supra-épineuse de la scapula.", "Facette supérieure du tubercule majeur.", ["Amorcer l’abduction du bras"], ["Coaptation de la tête humérale"])
_a("infraspinatus", "Fosse infra-épineuse.", "Facette moyenne du tubercule majeur.", ["Rotation latérale du bras"], ["Coaptation gléno-humérale"])
_a("subscapularis", "Fosse subscapulaire.", "Tubercule mineur de l’humérus.", ["Rotation médiale du bras"], ["Coaptation gléno-humérale"])
_a("teres major", "Angle inférieur de la scapula.", "Lèvre médiale du sillon intertuberculaire.", ["Adduction, extension et rotation médiale du bras"])
_a("teres minor", "Bord latéral de la scapula.", "Facette inférieure du tubercule majeur.", ["Rotation latérale du bras"], ["Coaptation"])
_a("latissimus dorsi", "Épineuses T7–L5, fascia thoraco-lombaire, crête iliaque, côtes inférieures.", "Fond du sillon intertuberculaire de l’humérus.", ["Adduction, extension et rotation médiale du bras"], ["Abaissement de la scapula / inspirateur accessoire"])
_a("rectus abdominis", "Crête et symphyse pubiennes.", "Processus xiphoïde et cartilages costaux 5–7.", ["Flexion du tronc"], ["Rétroversion du bassin", "Expiration forcée"])
_a("brachialis", "Face antérieure de la moitié distale de l’humérus.", "Tubérosité ulnaire (processus coronoïde).", ["Flexion du coude (principal fléchisseur, avant-bras en pronation ou supination)"])
_a("brachioradialis", "Crête supra-condylaire latérale de l’humérus.", "Processus styloïde du radius.", ["Flexion du coude"], ["Ramène l’avant-bras en position neutre (semi-pronation)"])
_a("coracobrachialis", "Processus coracoïde.", "Face médiale du tiers moyen de l’humérus.", ["Flexion et adduction de l’épaule"])
_a("anconeus", "Épicondyle latéral de l’humérus.", "Olécrane et face postérieure de l’ulna proximal.", ["Extension du coude"], ["Stabilisation ulnaire / abduction de l’ulna en pronation"])
_a("supinator", "Épicondyle latéral, ligament collatéral radial, crête du supinateur de l’ulna.", "Face latérale du radius proximal.", ["Supination de l’avant-bras"])
_a(
    "pronator teres",
    "Chef huméral : épicondyle médial. Chef ulnaire : processus coronoïde.",
    "Face latérale du radius (tiers moyen).",
    ["Pronation de l’avant-bras"],
    ["Flexion accessoire du coude"],
    [
        _h("Chef huméral", "Épicondyle médial (tendon commun des fléchisseurs).", "Face latérale du radius."),
        _h("Chef ulnaire", "Processus coronoïde de l’ulna.", "Face latérale du radius."),
    ],
)
_a("pronator quadratus", "Quart distal de la face antérieure de l’ulna.", "Quart distal de la face antérieure du radius.", ["Pronation de l’avant-bras"], ["Stabilisation de la syndesmose radio-ulnaire distale"])
_a("flexor carpi radialis", "Épicondyle médial (tendon commun).", "Bases des 2e et 3e métacarpiens.", ["Flexion du poignet", "Abduction radiale du poignet"])
_a(
    "flexor carpi ulnaris",
    "Chef huméral : épicondyle médial. Chef ulnaire : olécrane et bord postérieur de l’ulna.",
    "Pisiforme, hamatum et 5e métacarpien.",
    ["Flexion du poignet", "Adduction ulnaire du poignet"],
    None,
    [
        _h("Chef huméral", "Épicondyle médial.", "Pisiforme / hamatum / 5e métacarpien."),
        _h("Chef ulnaire", "Olécrane et bord postérieur de l’ulna.", "Pisiforme / hamatum / 5e métacarpien."),
    ],
)
_a("palmaris longus", "Épicondyle médial.", "Aponévrose palmaire.", ["Flexion du poignet"], ["Mise en tension de l’aponévrose palmaire"])
_a("flexor digitorum superficialis", "Épicondyle médial, processus coronoïde, bord antérieur du radius.", "Bords des phalanges moyennes des doigts 2–5.", ["Flexion des IPP des doigts 2–5"], ["Flexion des MP et du poignet"])
_a("flexor digitorum profundus", "Face antérieure de l’ulna et membrane interosseuse.", "Base des phalanges distales des doigts 2–5.", ["Flexion des IPD des doigts 2–5"], ["Flexion IPP / MP / poignet"])
_a("flexor pollicis longus", "Face antérieure du radius et membrane interosseuse.", "Base de la phalange distale du pouce.", ["Flexion de l’IP du pouce"], ["Flexion MP du pouce"])
_a("extensor carpi radialis longus", "Crête supra-condylaire latérale.", "Base dorsale du 2e métacarpien.", ["Extension du poignet", "Abduction radiale"])
_a("extensor carpi radialis brevis", "Épicondyle latéral (tendon commun des extenseurs).", "Base dorsale du 3e métacarpien.", ["Extension du poignet"], ["Abduction radiale accessoire"])
_a("extensor carpi ulnaris", "Épicondyle latéral et bord postérieur de l’ulna.", "Base du 5e métacarpien.", ["Extension du poignet", "Adduction ulnaire"])
_a("extensor digitorum", "Épicondyle latéral.", "Expansions dorsales des doigts 2–5.", ["Extension des MP des doigts 2–5"], ["Extension du poignet"])
_a("extensor digiti minimi", "Épicondyle latéral.", "Expansion dorsale du 5e doigt.", ["Extension du petit doigt"])
_a("extensor indicis", "Face postérieure de l’ulna et membrane interosseuse.", "Expansion dorsale de l’index.", ["Extension de l’index"], ["Adduction de l’index / extension du poignet"])
_a("extensor pollicis longus", "Face postérieure de l’ulna et membrane interosseuse.", "Base de la phalange distale du pouce.", ["Extension de l’IP du pouce"], ["Extension / rétropulsion du 1er métacarpien"])
_a("extensor pollicis brevis", "Radius et membrane interosseuse.", "Base de la phalange proximale du pouce.", ["Extension de la MP du pouce"])
_a("abductor pollicis longus", "Ulna, radius et membrane interosseuse.", "Base du 1er métacarpien.", ["Abduction et extension du 1er métacarpien"])
_a("abductor pollicis brevis", "Rétinaculum des fléchisseurs, scaphoïde et trapèze.", "Phalange proximale du pouce (côté radial) et expansion dorsale.", ["Abduction du pouce"], ["Opposition accessoire"])
_a("flexor pollicis brevis", "Rétinaculum des fléchisseurs et trapèze (superficiel) ; trapézoïde / capitatum (profond).", "Phalange proximale du pouce.", ["Flexion de la MP du pouce"])
_a("opponens pollicis", "Rétinaculum des fléchisseurs et trapèze.", "Bord latéral du 1er métacarpien.", ["Opposition du pouce"])
_a(
    "adductor pollicis",
    "Chef oblique : capitatum et bases des 2e–3e métacarpiens. Chef transverse : 3e métacarpien.",
    "Phalange proximale du pouce (côté ulnaire) et sésamoïde.",
    ["Adduction du pouce"],
    None,
    [
        _h("Chef oblique", "Capitatum et bases M2–M3.", "Phalange proximale du pouce."),
        _h("Chef transverse", "3e métacarpien.", "Phalange proximale du pouce."),
    ],
)
_a("abductor digiti minimi of hand", "Pisiforme et tendon du fléchisseur ulnaire du carpe.", "Phalange proximale du 5e doigt (côté ulnaire).", ["Abduction du petit doigt"])
_a("flexor digiti minimi brevis of hand", "Hamulus de l’hamatum et rétinaculum.", "Phalange proximale du 5e doigt.", ["Flexion de la MP du petit doigt"])
_a("opponens digiti minimi of hand", "Hamulus de l’hamatum et rétinaculum.", "5e métacarpien.", ["Opposition / concavité de la paume (5e rayon)"])
_a("subclavius", "1re côte et cartilage.", "Face inférieure de la clavicule.", ["Stabilise et abaisse la clavicule"])
_a("levator scapulae", "Transverses C1–C4.", "Angle supérieur de la scapula.", ["Élève la scapula"], ["Inclinaison cervicale homolatérale"])
_a("rhomboid major", "Épineuses T2–T5.", "Bord médial de la scapula sous l’épine.", ["Rétraction et rotation inférieure de la scapula"])
_a("rhomboid minor", "Ligament nuchal et épineuses C7–T1.", "Bord médial de la scapula à la racine de l’épine.", ["Rétraction de la scapula"])
_a("serratus anterior", "Face externe des côtes 1–8/9.", "Bord médial de la scapula (face antérieure).", ["Diduction / antépulsion de la scapula", "Rotation supérieure (fibres inférieures)"], ["Maintien de la scapula contre le thorax"])
_a("serratus posterior superior", "Épineuses C7–T3.", "Côtes 2–5.", ["Élève les côtes (inspirateur accessoire)"])
_a("serratus posterior inferior", "Épineuses T11–L2.", "Côtes 9–12.", ["Abaisse les côtes inférieures"], ["Stabilise la charnière thoraco-lombaire"])
_a("splenius capitis", "Ligament nuchal et épineuses C7–T3/4.", "Mastoïde et ligne nuchale supérieure.", ["Extension de la tête (bilatéral)", "Rotation et inclinaison homolatérales"])
_a("splenius cervicis", "Épineuses T3–T6.", "Transverses C1–C3.", ["Extension cervicale", "Rotation / inclinaison homolatérales"])
_a("semispinalis capitis", "Transverses thoraciques hautes et cervicales.", "Os occipital entre les lignes nuchales.", ["Extension de la tête"], ["Rotation controlatérale"])
_a("semispinalis cervicis", "Transverses thoraciques.", "Épineuses cervicales (surtout C2).", ["Extension cervicale", "Rotation controlatérale"])
_a("semispinalis thoracis", "Transverses thoraciques basses.", "Épineuses thoraciques hautes / cervicales basses.", ["Extension thoracique", "Rotation controlatérale"])
_a("iliocostalis cervicis", "Côtes 3–6.", "Transverses C4–C6.", ["Extension et inclinaison homolatérale du rachis"])
_a("iliocostalis thoracis", "Côtes inférieures.", "Angles des côtes supérieures.", ["Extension et inclinaison homolatérale du rachis thoracique"])
_a("iliocostalis lumborum", "Sacrum, crête iliaque, fascia thoraco-lombaire.", "Angles des côtes inférieures.", ["Extension et inclinaison homolatérale lombaire"])
_a("longissimus capitis", "Transverses thoraciques / articulaires cervicales.", "Processus mastoïde.", ["Extension de la tête", "Rotation homolatérale"])
_a("longissimus cervicis", "Transverses thoraciques.", "Transverses cervicales.", ["Extension et inclinaison cervicales"])
_a("longissimus thoracis", "Sacrum, épineuses lombaires, crête iliaque.", "Transverses thoraciques et côtes.", ["Extension du rachis thoraco-lombaire"])
_a("spinalis thoracis", "Épineuses T11–L2.", "Épineuses thoraciques hautes.", ["Extension du rachis thoracique"])
_a("cervical rotator", "Processus transverses cervicaux.", "Lame / épineuse de la vertèbre sus-jacente (1–2 niveaux).", ["Rotation controlatérale fine", "Stabilisation segmentaire"])
_a("thoracic rotator", "Transverses thoraciques.", "Lame / épineuse sus-jacente.", ["Rotation controlatérale fine", "Stabilisation segmentaire"])
_a("lumbar rotator", "Transverses lombaires.", "Lame / épineuse sus-jacente.", ["Rotation controlatérale fine", "Stabilisation segmentaire"])
_a("interspinalis thoracis", "Processus épineux thoraciques adjacents.", "Épineuse voisine.", ["Extension segmentaire", "Proprioception / stabilisation"])
_a("lateral lumbar intertransversarius", "Processus transverses lombaires adjacents (portion latérale).", "Transverse voisin.", ["Inclinaison homolatérale", "Stabilisation"])
_a("medial lumbar intertransversarius", "Processus accessoires / mamillaires lombaires.", "Niveau adjacent.", ["Stabilisation segmentaire lombaire"])
_a("scalenus anterior", "Transverses C3–C6.", "Tubercule du scalène de la 1re côte.", ["Élève la 1re côte", "Inclinaison cervicale homolatérale"], ["Flexion cervicale"])
_a("scalenus medius", "Transverses C2–C7.", "1re côte (en arrière du sillon du plexus).", ["Élève la 1re côte", "Inclinaison cervicale"])
_a("scalenus posterior", "Transverses C4–C6.", "2e côte.", ["Élève la 2e côte", "Inclinaison cervicale"])
_a("longus capitis", "Transverses C3–C6.", "Partie basale de l’occipital.", ["Flexion de la tête"])
_a(
    "longus colli",
    "Corps vertébraux et transverses cervico-thoraciques (faisceaux supérieur, vertical, inférieur).",
    "Corps et transverses cervicaux (atlas / C2–C4 selon le faisceau).",
    ["Flexion du cou"],
    ["Inclinaison homolatérale"],
    [
        _h("Faisceau oblique supérieur", "Transverses C3–C5.", "Tubercule antérieur de l’atlas."),
        _h("Faisceau vertical", "Corps C5–T3.", "Corps C2–C4."),
        _h("Faisceau oblique inférieur", "Corps T1–T3.", "Transverses C5–C6."),
    ],
)
_a("rectus capitis anterior", "Masse latérale de l’atlas.", "Occipital (en avant du condyle).", ["Flexion atlanto-occipitale"])
_a("rectus capitis lateralis", "Processus transverse de l’atlas.", "Processus jugulaire de l’occipital.", ["Inclinaison atlanto-occipitale"])
_a("rectus capitis posterior major", "Épineuse de l’axis.", "Ligne nuchale inférieure (latéral).", ["Extension de la tête", "Rotation homolatérale"])
_a("rectus capitis posterior minor", "Tubercule postérieur de l’atlas.", "Ligne nuchale inférieure (médial).", ["Extension de la tête"])
_a("obliquus capitis inferior", "Épineuse de l’axis.", "Transverse de l’atlas.", ["Rotation homolatérale de l’atlas (tête)"])
_a("obliquus capitis superior", "Transverse de l’atlas.", "Occipital entre les lignes nuchales.", ["Extension et inclinaison de la tête"])
_a("platysma", "Fascia pectoral / deltoïdien superficiel.", "Mandibule et peau de la commissure.", ["Tense la peau du cou"], ["Abaisse la commissure (mimique)"])
_a("digastric", "Ventre postérieur : mastoïde / incisure. Ventre antérieur : fosse digastrique mandibulaire.", "Os hyoïde via une poulie tendineuse.", ["Élève l’hyoïde", "Abaisse la mandibule (hyoïde fixé)"])
_a("mylohyoid", "Ligne mylo-hyoïdienne de la mandibule.", "Raphe médian et corps de l’hyoïde.", ["Élève le plancher buccal et l’hyoïde"])
_a("geniohyoid", "Épine mentonnière inférieure.", "Corps de l’hyoïde.", ["Tire l’hyoïde en haut et en avant"])
_a("stylohyoid", "Processus styloïde.", "Corps de l’hyoïde.", ["Élève et recule l’hyoïde"])
_a("omohyoid", "Bord supérieur de la scapula (incisure).", "Corps de l’hyoïde.", ["Abaisse l’hyoïde"])
_a("sternohyoid", "Manubrium et clavicule médiale.", "Corps de l’hyoïde.", ["Abaisse l’hyoïde"])
_a("sternothyroid", "Manubrium.", "Ligne oblique du cartilage thyroïde.", ["Abaisse le larynx"])
_a("thyrohyoid", "Ligne oblique du thyroïde.", "Grande corne de l’hyoïde.", ["Abaisse l’hyoïde ou élève le larynx"])
_a("external intercostal muscle", "Bord inférieur de la côte sus-jacente (tubercule → jonction chondro-costale).", "Bord supérieur de la côte sous-jacente.", ["Élève les côtes (inspiration)"])
_a("internal intercostal muscle", "Bord inférieur de la côte (sternum → angle).", "Côte sous-jacente.", ["Abaisse les côtes (expiration)", "Intercartilagineux : inspiration"])
_a("innermost intercostal muscle", "Face interne des espaces intercostaux.", "Côte adjacente.", ["Expiration / rigidification de la paroi"])
_a("transversus thoracis", "Face postérieure du sternum / xiphoïde.", "Cartilages costaux 2–6.", ["Abaisse les cartilages costaux (expiration)"])
_a("diaphragm", "Xiphoïde, cartilages 7–12, arcade du psoas / carré des lombes, piliers L1–L3.", "Centre phrénique.", ["Inspiration principale (abaissement du centre phrénique)"], ["Rôle de continence / presse abdominale"])
_a("sartorius", "Épine iliaque antéro-supérieure.", "Face médiale du tibia proximal (patte d’oie).", ["Flexion, abduction et rotation latérale de hanche", "Flexion du genou"])
_a("gracilis", "Corps du pubis / branche inférieure.", "Patte d’oie (tibia médial).", ["Adduction de hanche", "Flexion du genou et rotation médiale de jambe"])
_a("pectineus", "Pecten du pubis.", "Ligne pectinéale du fémur.", ["Adduction et flexion de hanche"])
_a("adductor longus", "Corps du pubis sous la crête.", "Tiers moyen de la ligne âpre.", ["Adduction de hanche"], ["Flexion accessoire"])
_a("adductor brevis", "Branche inférieure du pubis.", "Ligne pectinéale et ligne âpre (haute).", ["Adduction de hanche"], ["Flexion accessoire"])
_a("adductor magnus", "Branche ischio-pubienne et tubérosité ischiatique.", "Ligne âpre et tubercule de l’adducteur (hiatus).", ["Adduction de hanche"], ["Extension de hanche (portion ischio-condylaire)"])
_a("adductor minimus", "Branche ischio-pubienne (portion haute du grand adducteur).", "Ligne âpre proximale.", ["Adduction de hanche"])
_a("tensor fasciae latae", "EIAS et lèvre externe de la crête iliaque.", "Tractus ilio-tibial vers le tubercule de Gerdy.", ["Flexion, abduction et rotation médiale de hanche"], ["Stabilisation latérale du genou"])
_a("piriformis", "Face antérieure du sacrum (S2–S4).", "Sommet du grand trochanter.", ["Rotation latérale de hanche (hanche tendue)", "Abduction hanche fléchie"])
_a("obturator internus", "Cadre et membrane obturateurs (face interne).", "Face médiale du grand trochanter.", ["Rotation latérale de hanche"])
_a("obturator externus", "Cadre obturateur (face externe).", "Fosse trochantérique.", ["Rotation latérale de hanche"])
_a("gemellus superior", "Épine ischiatique.", "Tendon de l’obturateur interne (grand trochanter).", ["Rotation latérale de hanche"])
_a("gemellus inferior", "Tubérosité ischiatique.", "Tendon de l’obturateur interne.", ["Rotation latérale de hanche"])
_a("quadratus femoris", "Bord latéral de la tubérosité ischiatique.", "Crête intertrochantérique.", ["Rotation latérale de hanche"])
_a("plantaris", "Ligne supra-condylaire latérale du fémur.", "Calcanéus (médial au tendon calcanéen).", ["Flexion plantaire accessoire", "Flexion du genou accessoire"])
_a("popliteus", "Condyle fémoral latéral (et ménisque latéral).", "Face postérieure du tibia au-dessus de la ligne soléaire.", ["Déverrouille le genou (rotation médiale du tibia)", "Flexion accessoire"])
_a("fibularis longus", "Tête et face latérale de la fibula.", "Cunéiforme médial et base du 1er métatarsien (plante).", ["Éversion du pied", "Flexion plantaire accessoire"], ["Soutien de la voûte transversale"])
_a("fibularis brevis", "Face latérale de la fibula (2/3 inférieurs).", "Tubérosité du 5e métatarsien.", ["Éversion du pied"])
_a("fibularis tertius", "Face antérieure de la fibula distale et membrane interosseuse.", "Base du 5e métatarsien (dorsale).", ["Flexion dorsale", "Éversion"])
_a("extensor digitorum longus", "Condyle tibial latéral, fibula et membrane interosseuse.", "Expansions dorsales des orteils 2–5.", ["Extension des orteils 2–5", "Flexion dorsale de cheville"])
_a("extensor hallucis longus", "Fibula et membrane interosseuse.", "Base de la phalange distale de l’hallux.", ["Extension de l’hallux", "Flexion dorsale accessoire"])
_a("flexor digitorum longus", "Face postérieure du tibia.", "Phalanges distales des orteils 2–5.", ["Flexion des orteils 2–5", "Flexion plantaire accessoire"])
_a("flexor hallucis longus", "Face postérieure de la fibula.", "Phalange distale de l’hallux.", ["Flexion de l’hallux"], ["Soutien de la voûte médiale"])
_a("extensor hallucis brevis", "Calcanéus dorsal / sinus du tarse.", "Phalange proximale de l’hallux.", ["Extension de la MP de l’hallux"])
_a("flexor digitorum brevis", "Tubérosité calcanéenne et aponévrose plantaire.", "Phalanges moyennes des orteils 2–5.", ["Flexion des IPP des orteils 2–5"])
_a("abductor hallucis", "Tubérosité calcanéenne médiale, rétinaculum, aponévrose.", "Phalange proximale de l’hallux (côté médial) et sésamoïde.", ["Abduction et flexion de l’hallux"])
_a("abductor digiti minimi of foot", "Tubérosité calcanéenne latérale et aponévrose.", "Phalange proximale du 5e orteil.", ["Abduction et flexion du 5e orteil"])
_a(
    "flexor hallucis brevis",
    "Chef médial et latéral : cuboïde / cunéiformes / tibialis posterior.",
    "Phalange proximale de l’hallux (sésamoïdes).",
    ["Flexion de la MP de l’hallux"],
    None,
    [
        _h("Chef médial", "Cuboïde / cunéiforme médial.", "Sésamoïde médial et phalange proximale."),
        _h("Chef latéral", "Cuboïde / ligaments plantaires.", "Sésamoïde latéral et phalange proximale."),
    ],
)
_a(
    "adductor hallucis",
    "Chef oblique : bases M2–M4. Chef transverse : ligaments métatarsiens plantaires.",
    "Sésamoïde latéral et phalange proximale de l’hallux.",
    ["Adduction de l’hallux"],
    ["Soutien de la voûte transversale (chef transverse)"],
    [
        _h("Chef oblique", "Bases des métatarsiens 2–4.", "Sésamoïde latéral / P1 hallux."),
        _h("Chef transverse", "Capsules MP 3–5 / ligaments profonds.", "Sésamoïde latéral / P1 hallux."),
    ],
)
_a("flexor digiti minimi brevis of foot", "Base du 5e métatarsien et ligament plantaire long.", "Phalange proximale du 5e orteil.", ["Flexion de la MP du 5e orteil"])
_a("opponens digiti minimi of foot", "Ligament plantaire long / gaine du fibulaire long.", "5e métatarsien.", ["Stabilise le 5e rayon / légère opposition"])
_a("flexor accessorius", "Calcanéus (deux chefs médial et latéral).", "Tendon du fléchisseur long des orteils.", ["Corrige la traction du FDL (flexion axiale des orteils)"])
_a("first lumbrical of foot", "Tendon médial du fléchisseur long des orteils (orteil 2).", "Expansion dorsale de l’orteil 2 (côté médial).", ["Flexion MP et extension IP de l’orteil 2"])
_a("second lumbrical of foot", "Tendons FDL adjacents (orteils 2–3).", "Expansion dorsale de l’orteil 3.", ["Flexion MP et extension IP de l’orteil 3"])
_a("third lumbrical of foot", "Tendons FDL adjacents (orteils 3–4).", "Expansion dorsale de l’orteil 4.", ["Flexion MP et extension IP de l’orteil 4"])
_a("fourth lumbrical of foot", "Tendons FDL adjacents (orteils 4–5).", "Expansion dorsale de l’orteil 5.", ["Flexion MP et extension IP de l’orteil 5"])
_a("first plantar interosseous of foot", "Métatarsien 3 (face médiale).", "Phalange proximale de l’orteil 3 (côté médial).", ["Adduction de l’orteil 3 (axe du 2e rayon)"])
_a("second plantar interosseous of foot", "Métatarsien 4 (face médiale).", "Phalange proximale de l’orteil 4.", ["Adduction de l’orteil 4"])
_a("third plantar interosseous of foot", "Métatarsien 5 (face médiale).", "Phalange proximale de l’orteil 5.", ["Adduction de l’orteil 5"])
_a("coccygeus", "Épine ischiatique et ligament sacro-épineux.", "Bord latéral du coccyx / sacrum inférieur.", ["Soutien du plancher pelvien", "Tire le coccyx en avant"])
_a("iliococcygeus", "Arc tendineux du muscle élévateur / épine ischiatique.", "Coccyx et raphé ano-coccygien.", ["Soutien des viscères pelviens"])
_a("pubococcygeus", "Pubis (face postérieure).", "Coccyx / raphé / organes pelviens.", ["Soutien pelvien", "Continence"])
_a("puborectalis", "Pubis (deux chefs droit et gauche).", "Sangle derrière la jonction ano-rectale.", ["Maintien de l’angle ano-rectal (continence fécale)"])
_a("external anal sphincter", "Raphé ano-coccygien / peau.", "Périnée antérieur / fibres circulaires.", ["Continence anale volontaire"])


def _heads_from_labels(labels: list[str], origin: str, insertion: str) -> list[dict[str, str]]:
    if len(labels) < 2:
        return []
    return [_h(label, origin, insertion) for label in labels]


def catalog_entry(key: str, head_labels: list[str] | None = None) -> dict[str, Any]:
    name, latin = french_name_for(key), latin_for(key)
    aliases = aliases_for(key)
    region = region_for(key)
    anatomy = ANATOMY.get(key)
    labels = head_labels or []
    if anatomy:
        heads = anatomy.get("heads") or _heads_from_labels(labels, anatomy["origin"], anatomy["insertion"])
        return {
            "name": name,
            "nameLatin": latin,
            "aliases": aliases,
            "region": region,
            "origin": anatomy["origin"],
            "insertion": anatomy["insertion"],
            "actions": list(anatomy["actions"]),
            "secondaryActions": list(anatomy.get("secondaryActions") or []),
            "heads": heads or None,
        }
    origin = (
        f"Origines des chefs BodyParts3D"
        + (f" ({', '.join(labels)})" if labels else "")
        + " — insertions osseuses du muscle « "
        + name
        + " » selon l’anatomie classique."
    )
    insertion = f"Insertions distales du {name} (tous les chefs convergent vers les insertions habituelles de ce muscle)."
    actions = ["Action principale du groupe : voir région et chefs."]
    secondary = ["Détail des actions secondaires à préciser selon le chef (sélection fine : à venir)."]
    return {
        "name": name,
        "nameLatin": latin,
        "aliases": aliases,
        "region": region,
        "origin": origin,
        "insertion": insertion,
        "actions": actions,
        "secondaryActions": secondary,
        "heads": _heads_from_labels(labels, origin, insertion) or None,
    }
