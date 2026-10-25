"""French catalog for the aligned Z-Anatomy layers.

Reads /tmp/za_bounds.json (written by scripts/align_zanatomy_layers.mjs) and
writes src/data/zanatomyParts.json. Muscles that already exist in the app keep
that id so Myers chains and the fiches still match. Everything else is its own
clickable part.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zanatomy_nerve_fr import french_name

ROOT = os.path.join(os.path.dirname(__file__), "..")
BOUNDS = os.environ.get("ZA_BOUNDS", "/tmp/za_bounds.json")
OUT = os.path.join(ROOT, "src", "data", "zanatomyParts.json")

# Exact Z-Anatomy base (no .l/.r) → existing muscle id. Heads share one id.
MUSCLE_ID = {
    "rectus abdominis muscle": "droit-abdomen",
    "external abdominal oblique muscle": "oblique-externe",
    "internal abdominal oblique muscle": "oblique-interne",
    "transversus abdominis muscle": "transverse-de-l-abdomen",
    "lateral head of gastrocnemius": "gastrocnemien",
    "medial head of gastrocnemius": "gastrocnemien",
    "soleus muscle": "soleaire",
    "plantaris muscle": "plantaire",
    "long head of biceps femoris": "biceps-femoral",
    "short head of biceps femoris": "biceps-femoral",
    "semitendinosus muscle": "semi-tendineux",
    "semimembranosus muscle": "semi-membraneux",
    "iliocostalis lumborum muscle": "iliocostal-lombaire",
    "iliocostalis thoracis muscle": "iliocostal-thoracique",
    "iliocostalis colli muscle": "iliocostal-cervical",
    "longissimus thoracis muscle": "longissimus-du-thorax",
    "longissimus colli muscle": "longissimus-du-cou",
    "longissimus capitis muscle": "longissimus-de-la-tete",
    "spinalis thoracis muscle": "epineux-du-thorax",
    "spinalis capitis muscle": "semi-epineux-de-la-tete",
    "semispinalis thoracis muscle": "semi-epineux-du-thorax",
    "semispinalis colli muscle": "semi-epineux-du-cou",
    "rectus posterior major capitis muscle": "grand-droit-posterieur-de-la-tete",
    "rectus posterior minor capitis muscle": "petit-droit-posterieur-de-la-tete",
    "obliquus inferior capitis muscle": "oblique-inferieur-de-la-tete",
    "obliquus superior capitis muscle": "oblique-superieur-de-la-tete",
    "extensor digitorum longus": "extenseur-long-des-orteils",
    "extensor hallucis longus": "extenseur-long-de-l-hallux",
    "tibialis anterior muscle": "tibial-anterieur",
    "rectus femoris muscle": "droit-femoral",
    "vastus intermedius muscle": "vaste-intermediaire",
    "vastus lateralis muscle": "vaste-lateral",
    "vastus medialis muscle": "vaste-medial",
    "sternocleidomastoid muscle": "sterno-cleido-mastoidien",
    "fibularis longus muscle": "long-fibulaire",
    "fibularis brevis muscle": "court-fibulaire",
    "fibularis tertius muscle": "troisieme-fibulaire",
    "tensor fasciae latae": "tenseur-du-fascia-lata",
    "gluteus medius muscle": "moyen-fessier",
    "gluteus minimus muscle": "petit-fessier",
    "gluteus maximus muscle": "grand-fessier",
    "splenius capitis muscle": "splenius-de-la-tete",
    "splenius colli muscle": "splenius-du-cou",
    "rhomboid major muscle": "grand-rhomboide",
    "rhomboid minor muscle": "petit-rhomboide",
    "serratus anterior muscle": "dentele-anterieur",
    "tibialis posterior muscle": "tibial-posterieur",
    "flexor digitorum longus": "flechisseur-long-des-orteils",
    "flexor hallucis longus": "flechisseur-long-de-l-hallux",
    "popliteus muscle": "poplite",
    "adductor magnus": "grand-adducteur",
    "adductor longus": "long-adducteur",
    "adductor brevis": "court-adducteur",
    "adductor minimus": "petit-adducteur",
    "gracilis muscle": "gracile",
    "pectineus muscle": "pectine",
    "pubococcygeus muscle": "pubo-coccygien",
    "iliococcygeus muscle": "ilio-coccygien",
    "diaphragm": "diaphragme",
    "transversus thoracis muscle": "transverse-du-thorax",
    "external intercostal muscles": "intercostaux-externes",
    "internal intercostal muscles": "intercostaux-internes",
    "innermost intercostal muscles": "intercostaux-intimes",
    "scalenus anterior muscle": "scalene-anterieur",
    "scalenus medius muscle": "scalene-moyen",
    "scalenus posterior muscle": "scalene-posterieur",
    "longus colli muscle": "long-du-cou",
    "longus capitis muscle": "long-de-la-tete",
    "rectus anterior capitis muscle": "droit-anterieur-de-la-tete",
    "rectus lateralis capitis muscle": "droit-lateral-de-la-tete",
    "sternohyoid muscle": "sterno-hyoidien",
    "sternothyroid muscle": "sterno-thyroidien",
    "omohyoid muscle": "omo-hyoidien",
    "thyrohyoid muscle": "thyro-hyoidien",
    "geniohyoid muscle": "genio-hyoidien",
    "mylohyoid muscle": "mylo-hyoidien",
    "clavicular head of pectoralis major muscle": "grand-pectoral",
    "sternocostal head of pectoralis major muscle": "grand-pectoral",
    "abdominal part of pectoralis major muscle": "grand-pectoral",
    "latissimus dorsi muscle": "grand-dorsal",
    "palmaris longus muscle": "long-palmaire",
    "flexor carpi radialis": "flechisseur-radial-du-carpe",
    "humeral head of flexor carpi ulnaris": "flechisseur-ulnaire-du-carpe",
    "ulnar head of flexor carpi ulnaris": "flechisseur-ulnaire-du-carpe",
    "humero-ulnar head of flexor digitorum superficialis": "flechisseur-superficiel-des-doigts",
    "radial head of flexor digitorum superficialis": "flechisseur-superficiel-des-doigts",
    "pectoralis minor muscle": "petit-pectoral",
    "subclavius muscle": "subclavier",
    "long head of biceps brachii": "biceps-brachial",
    "short head of biceps brachii": "biceps-brachial",
    "coracobrachialis muscle": "coraco-brachial",
    "brachialis muscle": "brachial",
    "flexor digitorum profundus": "flechisseur-profond-des-doigts",
    "flexor pollicis longus": "long-flechisseur-du-pouce",
    "abductor pollicis brevis": "court-abducteur-du-pouce",
    "opponens pollicis muscle": "opposant-du-pouce",
    "deep head of flexor pollicis brevis": "court-flechisseur-du-pouce",
    "superficial head of flexor pollicis brevis": "court-flechisseur-du-pouce",
    "ascending part of trapezius muscle": "trapeze",
    "descending part of trapezius muscle": "trapeze",
    "transverse part of trapezius muscle": "trapeze",
    "acromial part of deltoid muscle": "deltoide",
    "clavicular part of deltoid muscle": "deltoide",
    "scapular spinal part of deltoid muscle": "deltoide",
    "anconeus muscle": "ancone",
    "extensor carpi radialis longus": "long-extenseur-radial-du-carpe",
    "extensor carpi radialis brevis": "court-extenseur-radial-du-carpe",
    "extensor digitorum": "extenseur-des-doigts",
    "humeral head of extensor carpi ulnaris": "extenseur-ulnaire-du-carpe",
    "ulnar head of extensor carpi ulnaris": "extenseur-ulnaire-du-carpe",
    "extensor digiti minimi": "extenseur-du-petit-doigt",
    "extensor indicis": "extenseur-de-l-index",
    "abductor digiti minimi of hand": "abducteur-du-petit-doigt",
    "opponens digiti minimi muscle of hand": "opposant-du-petit-doigt",
    "flexor digiti minimi of hand": "court-flechisseur-du-petit-doigt",
    "supraspinatus muscle": "supra-epineux",
    "infraspinatus muscle": "infra-epineux",
    "teres minor muscle": "petit-rond",
    "subscapularis muscle": "subscapulaire",
    "teres major muscle": "grand-rond",
    "long head of triceps brachii": "triceps-brachial",
    "lateral head of triceps brachii": "triceps-brachial",
    "medial head of triceps brachii": "triceps-brachial",
    "levator scapulae": "elevateur-de-la-scapula",
    "flexor digitorum brevis": "court-flechisseur-des-orteils",
    "abductor hallucis": "abducteur-de-l-hallux",
    "abductor digiti minimi of foot": "abducteur-du-petit-orteil",
    "iliacus muscle": "iliopsoas",
    "psoas major": "iliopsoas",
    "sartorius muscle": "sartorius",
    "serratus posterior inferior muscle": "dentele-posterieur-inferieur",
    "serratus posterior superior muscle": "dentele-posterieur-superieur",
    "platysma": "peaucier-du-cou",
    "masseter": "masseter",
    "deep part of masseter": "masseter",
    "superficial part of masseter": "masseter",
    "temporalis muscle": "temporal",
    "medial pterygoid muscle": "pterygoide-medial",
    "inferior head of lateral pterygoid muscle": "pterygoide-lateral",
    "superior head of lateral pterygoid muscle": "pterygoide-lateral",
    "external anal sphincter": "sphincter-anal-externe",
    "coccygeus muscle": "coccygien",
    "obturator externus": "obturateur-externe",
    "obturator internus": "obturateur-interne",
    "piriformis muscle": "piriforme",
    "quadratus femoris muscle": "carre-femoral",
    "quadratus plantae muscle": "carre-plantaire",
    "pronator quadratus": "carre-pronateur",
    "deep head of pronator teres": "rond-pronateur",
    "superficial head of pronator teres": "rond-pronateur",
    "brachioradialis muscle": "brachio-radial",
    "supinator": "supinateur",
    "abductor pollicis longus": "long-abducteur-du-pouce",
    "extensor pollicis brevis": "court-extenseur-du-pouce",
    "extensor pollicis longus": "long-extenseur-du-pouce",
    "extensor hallucis brevis": "court-extenseur-de-l-hallux",
    "extensor digitorum brevis": "court-extenseur-des-orteils",
    "flexor digiti minimi of foot": "court-flechisseur-du-petit-orteil",
    "opponens digiti minimi muscle of foot": "opposant-du-petit-orteil",
    "oblique head of adductor hallucis": "adducteur-de-l-hallux",
    "transverse head of adductor hallucis": "adducteur-de-l-hallux",
    "medial head of flexor hallucis brevis": "court-flechisseur-de-l-hallux",
    "lateral head of flexor hallucis brevis": "court-flechisseur-de-l-hallux",
    "oblique head of adductor pollicis": "adducteur-du-pouce",
    "transverse head of adductor pollicis": "adducteur-du-pouce",
    "anterior belly of digastric muscle": "digastrique",
    "posterior belly of digastric muscle": "digastrique",
    "intermediate tendon of digastric muscle": "digastrique",
    "stylohyoid muscle": "stylo-hyoidien",
    "interspinales thoracis muscles": "inter-epineux-thoraciques",
    "dorsal parts of lateral intertransversarii lumborum muscles": "intertransversaire-lombaire-lateral",
    "ventral parts of lateral intertransversarii lumborum muscles": "intertransversaire-lombaire-medial",
    "inferior gemellus muscle": "jumeau-inferieur",
    "superior gemellus muscle": "jumeau-superieur",
}

# (file-independent base) → (id without side, or (left id, right id), french without side)
CHAIN = {
    "plantar aponeurosis": ("aponévrose-plantaire-g", "aponévrose-plantaire-d", "Aponévrose plantaire"),
    "palmar aponeurosis": ("aponévrose-palmaire-g", "aponévrose-palmaire-d", "Aponévrose palmaire"),
    "flexor retinaculum of wrist": ("retinaculum-flechisseurs-g", "retinaculum-flechisseurs-d", "Rétinaculum des fléchisseurs"),
    "extensor retinaculum of wrist": ("retinaculum-extenseurs-g", "retinaculum-extenseurs-d", "Rétinaculum des extenseurs"),
    "medial intermuscular septum of arm": ("septum-medial-bras-g", "septum-medial-bras-d", "Septum intermusculaire médial du bras"),
    "lateral intermuscular septum of arm": ("septum-lateral-bras-g", "septum-lateral-bras-d", "Septum intermusculaire latéral du bras"),
    "clavipectoral fascia": ("fascia-clavipectoral-g", "fascia-clavipectoral-d", "Fascia clavipectoral"),
    "epicranial aponeurosis": ("fascia-epicranien-g", "fascia-epicranien-d", "Aponévrose épicrânienne"),
    "calcaneal tendon": ("tendon-calcaneen-g", "tendon-calcaneen-d", "Tendon calcanéen"),
    "iliotibial tract": ("tractus-ilio-tibial-g", "tractus-ilio-tibial-d", "Tractus ilio-tibial"),
    "fascia lata": ("fascia-lata-g", "fascia-lata-d", "Fascia lata"),
    "crural fascia": ("fascia-crural-g", "fascia-crural-d", "Fascia crural"),
    "posterior layer of thoracolumbar fascia": ("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
    "middle layer of thoracolumbar fascia": ("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
    "anterior layer of thoracolumbar fascia": ("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
    "sacrotuberous ligament": ("sacro-tubereux-g", "sacro-tubereux-d", "Ligament sacro-tubéreux"),
    "nuchal ligament": ("fascia-nuchal", "Ligament nuchal"),
    "anterior ligament of fibular head": ("ligament-tete-fibula-g", "ligament-tete-fibula-d", "Ligament antérieur de la tête de la fibula"),
    "pubic symphysis": ("symphyse-pubienne", "Symphyse pubienne"),
    "tongue": ("langue", "Langue"),
}

KIND = {
    "squelette": "bone",
    "muscles": "muscle",
    "fascias": "fascia",
    "ligaments": "ligament",
    "nerfs": "nerve",
    "vaisseaux": "vessel",
    "vaisseaux-extremites": "vessel",
    "organes": "organ",
    "organes-snc": "organ",
}

# Head noun → (French, gender). Longest match wins.
HEADS: list[tuple[str, str, str]] = [
    ("arteries", "artères", "f"),
    ("artery", "artère", "f"),
    ("veins", "veines", "f"),
    ("vein", "veine", "f"),
    ("nerves", "nerfs", "m"),
    ("nerve", "nerf", "m"),
    ("muscles", "muscles", "m"),
    ("muscle", "muscle", "m"),
    ("ligaments", "ligaments", "m"),
    ("ligament", "ligament", "m"),
    ("bones", "os", "m"),
    ("bone", "os", "m"),
    ("cartilages", "cartilages", "m"),
    ("cartilage", "cartilage", "m"),
    ("fasciae", "fascias", "m"),
    ("fascia", "fascia", "m"),
    ("aponeuroses", "aponévroses", "f"),
    ("aponeurosis", "aponévrose", "f"),
    ("tendons", "tendons", "m"),
    ("tendon", "tendon", "m"),
    ("retinacula", "rétinaculums", "m"),
    ("retinaculum", "rétinaculum", "m"),
    ("ganglia", "ganglions", "m"),
    ("ganglion", "ganglion", "m"),
    ("plexuses", "plexus", "m"),
    ("plexus", "plexus", "m"),
    ("branches", "rameaux", "m"),
    ("branch", "rameau", "m"),
    ("meniscus", "ménisque", "m"),
    ("menisci", "ménisques", "m"),
    ("disc", "disque", "m"),
    ("disk", "disque", "m"),
    ("gland", "glande", "f"),
    ("glands", "glandes", "f"),
    ("node", "nœud", "m"),
    ("nodes", "nœuds", "m"),
    ("valve", "valvule", "f"),
    ("leaflet", "cuspide", "f"),
    ("septum", "septum", "m"),
    ("membrane", "membrane", "f"),
    ("bursa", "bourse", "f"),
    ("bursae", "bourses", "f"),
    ("sheath", "gaine", "f"),
    ("capsule", "capsule", "f"),
    ("nucleus", "noyau", "m"),
    ("sinus", "sinus", "m"),
    ("lobe", "lobe", "m"),
    ("segment", "segment", "m"),
]

# adjective → (masculine, feminine)
ADJ = {
    "anterior": ("antérieur", "antérieure"),
    "posterior": ("postérieur", "postérieure"),
    "superior": ("supérieur", "supérieure"),
    "inferior": ("inférieur", "inférieure"),
    "medial": ("médial", "médiale"),
    "lateral": ("latéral", "latérale"),
    "deep": ("profond", "profonde"),
    "superficial": ("superficiel", "superficielle"),
    "common": ("commun", "commune"),
    "proper": ("propre", "propre"),
    "palmar": ("palmaire", "palmaire"),
    "plantar": ("plantaire", "plantaire"),
    "dorsal": ("dorsal", "dorsale"),
    "ventral": ("ventral", "ventrale"),
    "digital": ("digital", "digitale"),
    "cranial": ("crânien", "crânienne"),
    "caudal": ("caudal", "caudale"),
    "proximal": ("proximal", "proximale"),
    "distal": ("distal", "distale"),
    "internal": ("interne", "interne"),
    "external": ("externe", "externe"),
    "left": ("gauche", "gauche"),
    "right": ("droit", "droite"),
    "great": ("grand", "grande"),
    "small": ("petit", "petite"),
    "long": ("long", "longue"),
    "short": ("court", "courte"),
    "major": ("majeur", "majeure"),
    "minor": ("mineur", "mineure"),
    "middle": ("moyen", "moyenne"),
    "transverse": ("transverse", "transverse"),
    "oblique": ("oblique", "oblique"),
    "ascending": ("ascendant", "ascendante"),
    "descending": ("descendant", "descendante"),
    "superficial": ("superficiel", "superficielle"),
    "brachial": ("brachial", "brachiale"),
    "radial": ("radial", "radiale"),
    "ulnar": ("ulnaire", "ulnaire"),
    "femoral": ("fémoral", "fémorale"),
    "tibial": ("tibial", "tibiale"),
    "fibular": ("fibulaire", "fibulaire"),
    "peroneal": ("fibulaire", "fibulaire"),
    "parietal": ("pariétal", "pariétale"),
    "frontal": ("frontal", "frontale"),
    "occipital": ("occipital", "occipitale"),
    "temporal": ("temporal", "temporale"),
    "sphenoid": ("sphénoïde", "sphénoïde"),
    "ethmoid": ("ethmoïde", "ethmoïde"),
    "nasal": ("nasal", "nasale"),
    "maxillary": ("maxillaire", "maxillaire"),
    "mandibular": ("mandibulaire", "mandibulaire"),
    "zygomatic": ("zygomatique", "zygomatique"),
    "lacrimal": ("lacrymal", "lacrymale"),
    "palatine": ("palatin", "palatine"),
    "cervical": ("cervical", "cervicale"),
    "thoracic": ("thoracique", "thoracique"),
    "lumbar": ("lombaire", "lombaire"),
    "sacral": ("sacré", "sacrée"),
    "coccygeal": ("coccygien", "coccygienne"),
    "costal": ("costal", "costale"),
    "intercostal": ("intercostal", "intercostale"),
    "clavicular": ("claviculaire", "claviculaire"),
    "scapular": ("scapulaire", "scapulaire"),
    "humeral": ("huméral", "humérale"),
    "carpal": ("carpien", "carpienne"),
    "metacarpal": ("métacarpien", "métacarpienne"),
    "phalangeal": ("phalangien", "phalangienne"),
    "pelvic": ("pelvien", "pelvienne"),
    "iliac": ("iliaque", "iliaque"),
    "pubic": ("pubien", "pubienne"),
    "ischial": ("ischiatique", "ischiatique"),
    "acetabular": ("acétabulaire", "acétabulaire"),
    "patellar": ("patellaire", "patellaire"),
    "crural": ("crural", "crurale"),
    "sural": ("sural", "surale"),
    "tarsal": ("tarsien", "tarsienne"),
    "metatarsal": ("métatarsien", "métatarsienne"),
    "calcaneal": ("calcanéen", "calcanéenne"),
    "talar": ("talien", "talienne"),
    "navicular": ("naviculaire", "naviculaire"),
    "cuboid": ("cuboïde", "cuboïde"),
    "cuneiform": ("cunéiforme", "cunéiforme"),
    "hepatic": ("hépatique", "hépatique"),
    "renal": ("rénal", "rénale"),
    "splenic": ("splénique", "splénique"),
    "gastric": ("gastrique", "gastrique"),
    "pulmonary": ("pulmonaire", "pulmonaire"),
    "cardiac": ("cardiaque", "cardiaque"),
    "coronary": ("coronaire", "coronaire"),
    "cerebral": ("cérébral", "cérébrale"),
    "cerebellar": ("cérébelleux", "cérébelleuse"),
    "spinal": ("spinal", "spinale"),
    "cutaneous": ("cutané", "cutanée"),
    "muscular": ("musculaire", "musculaire"),
    "articular": ("articulaire", "articulaire"),
    "synovial": ("synovial", "synoviale"),
    "lymphatic": ("lymphatique", "lymphatique"),
    "venous": ("veineux", "veineuse"),
    "arterial": ("artériel", "artérielle"),
    "visceral": ("viscéral", "viscérale"),
    "parietal": ("pariétal", "pariétale"),
    "lobar": ("lobaire", "lobaire"),
    "segmental": ("segmentaire", "segmentaire"),
    "apical": ("apical", "apicale"),
    "basal": ("basal", "basale"),
    "interosseous": ("interosseux", "interosseuse"),
    "collateral": ("collatéral", "collatérale"),
    "recurrent": ("récurrent", "récurrente"),
    "communicating": ("communicant", "communicante"),
    "terminal": ("terminal", "terminale"),
    "accessory": ("accessoire", "accessoire"),
    "principal": ("principal", "principale"),
    "intermediate": ("intermédiaire", "intermédiaire"),
    "medial": ("médial", "médiale"),
    "lateral": ("latéral", "latérale"),
}

NOUN = {
    "head": "chef",
    "heads": "chefs",
    "part": "partie",
    "parts": "parties",
    "layer": "couche",
    "body": "corps",
    "neck": "col",
    "root": "racine",
    "roots": "racines",
    "trunk": "tronc",
    "arch": "arcade",
    "ring": "anneau",
    "cord": "cordon",
    "tract": "tractus",
    "sheet": "lame",
    "pad": "coussinet",
    "fat": "graisseux",
    "process": "processus",
    "spine": "épine",
    "fossa": "fosse",
    "foramen": "foramen",
    "canal": "canal",
    "groove": "sillon",
    "tubercle": "tubercule",
    "tuberosity": "tubérosité",
    "trochanter": "trochanter",
    "condyle": "condyle",
    "epicondyle": "épicondyle",
    "malleolus": "malléole",
    "shaft": "diaphyse",
    "base": "base",
    "hand": "main",
    "foot": "pied",
    "wrist": "poignet",
    "ankle": "cheville",
    "elbow": "coude",
    "knee": "genou",
    "shoulder": "épaule",
    "hip": "hanche",
    "thigh": "cuisse",
    "leg": "jambe",
    "arm": "bras",
    "forearm": "avant-bras",
    "finger": "doigt",
    "fingers": "doigts",
    "toe": "orteil",
    "toes": "orteils",
    "thumb": "pouce",
    "lung": "poumon",
    "lungs": "poumons",
    "liver": "foie",
    "heart": "cœur",
    "kidney": "rein",
    "spleen": "rate",
    "stomach": "estomac",
    "tongue": "langue",
    "brain": "encéphale",
    "eye": "œil",
    "ear": "oreille",
    "nose": "nez",
    "skull": "crâne",
    "rib": "côte",
    "ribs": "côtes",
    "sternum": "sternum",
    "clavicle": "clavicule",
    "scapula": "scapula",
    "humerus": "humérus",
    "radius": "radius",
    "ulna": "ulna",
    "femur": "fémur",
    "patella": "patella",
    "tibia": "tibia",
    "fibula": "fibula",
    "pelvis": "bassin",
    "sacrum": "sacrum",
    "coccyx": "coccyx",
    "atlas": "atlas",
    "axis": "axis",
    "mandible": "mandibule",
    "maxilla": "maxillaire",
    "hyoid": "hyoïde",
    "vertebra": "vertèbre",
    "vertebrae": "vertèbres",
    "phalanx": "phalange",
    "phalanges": "phalanges",
    "carpus": "carpe",
    "tarsus": "tarse",
    "metatarsal": "métatarsien",
    "metacarpal": "métacarpien",
    "calcaneus": "calcanéus",
    "talus": "talus",
    "diaphragm": "diaphragme",
    "pericardium": "péricarde",
    "pleura": "plèvre",
    "peritoneum": "péritoine",
    "dura": "dure-mère",
    "mater": "mère",
    "meninges": "méninges",
    "cortex": "cortex",
    "cerebellum": "cervelet",
    "cerebrum": "cerveau",
    "thalamus": "thalamus",
    "hypothalamus": "hypothalamus",
    "pituitary": "hypophyse",
    "thyroid": "thyroïde",
    "trachea": "trachée",
    "larynx": "larynx",
    "pharynx": "pharynx",
    "esophagus": "œsophage",
    "oesophagus": "œsophage",
    "aorta": "aorte",
    "vena": "veine",
    "cava": "cave",
    "portal": "porte",
    "lymph": "lymphatique",
    "tooth": "dent",
    "teeth": "dents",
    "skin": "peau",
    "scalp": "cuir chevelu",
    "nail": "ongle",
    "joint": "articulation",
    "symphysis": "symphyse",
    "labrum": "labrum",
    "annulus": "anneau",
    "anulus": "anneau",
    "pulp": "pulpe",
    "enamel": "émail",
    "dentine": "dentine",
    "gingiva": "gencive",
    "palate": "palais",
    "uvula": "uvule",
    "tonsil": "amygdale",
    "thymus": "thymus",
    "pancreas": "pancréas",
    "gallbladder": "vésicule biliaire",
    "bladder": "vessie",
    "ureter": "uretère",
    "urethra": "urètre",
    "uterus": "utérus",
    "ovary": "ovaire",
    "prostate": "prostate",
    "testis": "testicule",
    "penis": "pénis",
    "clitoris": "clitoris",
    "vagina": "vagin",
    "rectum": "rectum",
    "colon": "côlon",
    "duodenum": "duodénum",
    "jejunum": "jéjunum",
    "ileum": "iléon",
    "cecum": "cæcum",
    "appendix": "appendice",
    "mesentery": "mésentère",
    "omentum": "omentum",
    "bronchus": "bronche",
    "bronchi": "bronches",
    "lobe": "lobe",
    "segment": "segment",
    "valve": "valvule",
    "atrium": "atrium",
    "ventricle": "ventricule",
    "septum": "septum",
    "cord": "cordon",
    "chorda": "corde",
    "tympani": "tympan",
    "cauda": "queue",
    "equina": "de cheval",
    "ansa": "anse",
    "ramus": "rameau",
    "rami": "rameaux",
    "white": "blanc",
    "line": "ligne",
    "alba": "blanche",
    "intermuscular": "intermusculaire",
    "thoracolumbar": "thoraco-lombaire",
    "nuchal": "nuchal",
    "inguinal": "inguinal",
    "cruciate": "croisé",
    "collateral": "collatéral",
    "deltoid": "deltoïde",
    "coracoid": "coracoïde",
    "acromion": "acromion",
    "olecranon": "olécrane",
    "pisiform": "pisiforme",
    "hamate": "hamatum",
    "capitate": "capitatum",
    "lunate": "lunatum",
    "scaphoid": "scaphoïde",
    "triquetrum": "triquetrum",
    "trapezium": "trapèze",
    "trapezoid": "trapézoïde",
    "sesamoid": "sésamoïde",
    "hallux": "hallux",
    "pollex": "pouce",
    "index": "index",
    "digiti": "du doigt",
    "minimi": "petit",
    "first": "premier",
    "second": "deuxième",
    "third": "troisième",
    "fourth": "quatrième",
    "fifth": "cinquième",
    "i": "I",
    "ii": "II",
    "iii": "III",
    "iv": "IV",
    "v": "V",
    "vi": "VI",
    "vii": "VII",
    "viii": "VIII",
    "ix": "IX",
    "x": "X",
    "xi": "XI",
    "xii": "XII",
}


def strip_name(name: str) -> tuple[str, str | None]:
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


def slug(text: str) -> str:
    nfd = unicodedata.normalize("NFD", text)
    ascii_ = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    ascii_ = ascii_.replace("œ", "oe").replace("æ", "ae").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")[:90]


FEMININE_HEADS = {
    "artère", "artères", "veine", "veines", "aponévrose", "aponévroses",
    "branche", "glande", "glandes", "membrane", "bourse", "bourses",
    "gaine", "capsule", "valvule", "cuspide", "langue", "rate", "vessie",
    "trachée", "plèvre", "thyroïde", "clavicule", "patella", "fibula",
    "mandibule", "vertèbre", "vertèbres", "côte", "côtes", "malléole",
    "tubérosité", "fosse", "main", "épaule", "hanche", "cuisse", "jambe",
    "tête", "dent", "dents", "peau", "amygdale", "vésicule", "prostate",
    "bronche", "bronches", "corde", "arcade", "symphyse", "scapula",
}
PLURAL_HEADS = {
    "artères", "veines", "aponévroses", "nerfs", "muscles", "ligaments",
    "cartilages", "fascias", "tendons", "rameaux", "ganglions",
    "ménisques", "glandes", "nœuds", "bourses", "vertèbres", "côtes",
    "bronches", "dents", "poumons",
}


def _cap(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip(" -")
    if not text:
        return text
    return text[0].upper() + text[1:]


def _agree(word: str, gender: str) -> str:
    key = word.lower().strip("(),")
    if key in {"left", "right"}:
        return ""
    if key in ADJ:
        m, f = ADJ[key]
        return f if gender == "f" else m
    if key in NOUN:
        return NOUN[key]
    for src, fr, _gen in HEADS:
        if key == src:
            return fr
    return word.lower()


def _complement(words: list[str], gender: str) -> str:
    if not words:
        return ""
    if words[0].lower() == "of":
        words = words[1:]
    if words and words[0].lower() == "the":
        words = words[1:]
    if not words:
        return ""
    bits = [b for b in (_agree(w, "m") for w in words if w.lower() not in {"the", "a", "an", "of"}) if b]
    if not bits:
        return ""
    first = bits[0]
    article = "de l’" if first[:1].lower() in "aeiouéèêàâîôûh" else "de la " if gender == "f" else "du "
    # Complements are a noun phrase, not an adjective of the head. Use "de".
    return "de " + " ".join(bits)


def translate_loose(english: str) -> str:
    try:
        return french_name(english)[0]
    except KeyError:
        pass
    raw = english.strip()
    raw = re.sub(r"\s*\([^)]*\)\s*", " ", raw).strip()
    words = raw.split()
    head_at = None
    head_fr = None
    gender = "m"
    lowered = [w.lower().strip(",") for w in words]
    for length in (2, 1):
        for i in range(len(lowered) - length + 1):
            chunk = " ".join(lowered[i : i + length])
            for src, fr, gen in HEADS:
                if chunk == src:
                    head_at = i
                    head_fr = fr
                    gender = gen
                    break
            if head_at is not None:
                break
        if head_at is not None:
            break
    if head_at is None or head_fr is None:
        bits = [b for b in (_agree(w, "m") for w in words if w.lower() not in {"the", "of", "a"}) if b]
        return _polish(_cap(" ".join(bits) or english))
    before = words[:head_at]
    after = words[head_at + (2 if " " in (HEADS[0][0]) else 1) :]
    # head token count
    span = 1
    for src, fr, gen in HEADS:
        if " ".join(lowered[head_at : head_at + len(src.split())]) == src and fr == head_fr:
            span = len(src.split())
            break
    after = words[head_at + span :]
    adjs = [a for a in (_agree(w, gender) for w in before if w.lower() not in {"the", "a", "an", "of"}) if a]
    comp = _complement(after, gender)
    parts = [head_fr, *adjs]
    if comp:
        parts.append(comp)
    return _polish(_cap(" ".join(p for p in parts if p)))


def side_suffix(french: str, side: str | None) -> str:
    if not side:
        return french
    head = french.split()[0].lower() if french else ""
    feminine = head in FEMININE_HEADS
    plural = head in PLURAL_HEADS
    if side == "l":
        word = "gauches" if plural else "gauche"
    elif feminine:
        word = "droites" if plural else "droite"
    else:
        word = "droits" if plural else "droit"
    return f"{french} {word}"


_TOKEN = {src: fr for src, fr, _gen in HEADS}
_TOKEN.update({k: v[0] for k, v in ADJ.items()})
_TOKEN.update(NOUN)


def _polish(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        mapped = _TOKEN.get(word.lower())
        if mapped is None:
            return word
        if word[:1].isupper():
            return mapped[:1].upper() + mapped[1:]
        return mapped

    return re.sub(r"[A-Za-zÀ-ÿ]+", repl, text)


def region_of(base: str, c: list[float], kind: str) -> str:
    n = base.lower()
    x, y, _z = c
    if any(k in n for k in ("palmar", "retinaculum of wrist", "pollicis", "carpi", "digiti minimi of hand", "metacarpal")):
        return "main"
    if any(k in n for k in ("plantar", "hallucis", "calcane", "dorsalis pedis", "retinaculum of ankle")):
        return "pied"
    if y > 0.55:
        return "tête"
    if y > 0.42 and abs(x) < 0.12:
        return "cou"
    if abs(x) > 0.18 and y > -0.05:
        return "membre-supérieur"
    if y < -0.55:
        return "membre-inférieur"
    if kind == "bone" and y < -0.2:
        return "membre-inférieur"
    return "tronc"


def vessel_kind(base: str) -> str | None:
    n = base.lower()
    if any(k in n for k in ("vein", "vena", "sinus")):
        return "vein"
    if any(k in n for k in ("arter", "aorta", "trunk")):
        return "artery"
    return None


def main() -> None:
    bounds = json.load(open(BOUNDS, encoding="utf-8"))
    muscles = json.load(open(os.path.join(ROOT, "src", "data", "muscles.json"), encoding="utf-8"))
    muscle_name = {m["id"]: m["name"] for m in muscles}
    groups: dict[str, dict] = {}
    for row in bounds:
        base, side = strip_name(row["node"])
        key = base.lower()
        if side is None:
            if re.search(r"\bleft\b", key):
                side = "l"
            elif re.search(r"\bright\b", key):
                side = "r"
        kind = KIND[row["file"]]
        app = None
        french = None
        if key in CHAIN:
            spec = CHAIN[key]
            if len(spec) == 2:
                app, french = spec[0], spec[1]
            else:
                left, right, french = spec
                app = left if side == "l" else right if side == "r" else left
                french = side_suffix(french, side)
        elif kind == "muscle" and key in MUSCLE_ID:
            app = MUSCLE_ID[key]
            french = muscle_name.get(app, translate_loose(base))
        if french is None:
            french = translate_loose(base)
            if app is None:
                french = side_suffix(french, side)
        if app is None:
            app = "za-" + slug(french)
        part = groups.get(app)
        if part is None:
            part = {
                "id": app,
                "name": french if app not in muscle_name else muscle_name[app],
                "nameLatin": base,
                "aliases": [base, row["node"]],
                "region": region_of(base, row["centroid"], kind),
                "notes": "Maillage Z-Anatomy (Startup.blend, 2 mai 2023), CC BY-SA 4.0, dérivé de BodyParts3D.",
                "source": "zanatomy",
                "kind": kind,
                "file": row["file"],
                "nodes": [row["node"]],
                "centroid": row["centroid"],
                "focus": {"position": row["centroid"], "distance": 0.45},
                "triangles": row["triangles"],
                "files": [row["file"]],
                "min": list(row["min"]),
                "max": list(row["max"]),
            }
            if kind == "vessel":
                vk = vessel_kind(base)
                if vk:
                    part["vesselKind"] = vk
            if kind == "bone" and any(k in key for k in ("cartilag", "meniscus", "disc", "labrum")):
                part["tissue"] = "cartilage"
            groups[app] = part
        else:
            if row["node"] not in part["nodes"]:
                part["nodes"].append(row["node"])
            if row["node"] not in part["aliases"]:
                part["aliases"].append(row["node"])
            if row["file"] not in part["files"]:
                part["files"].append(row["file"])
            part["triangles"] += row["triangles"]
            # average centroid
            n = len(part["nodes"])
            part["centroid"] = [
                round((part["centroid"][i] * (n - 1) + row["centroid"][i]) / n, 5) for i in range(3)
            ]
            for i in range(3):
                part["min"][i] = min(part["min"][i], row["min"][i])
                part["max"][i] = max(part["max"][i], row["max"][i])
    parts = []
    for part in groups.values():
        c = part["centroid"]
        span = [part["max"][i] - part["min"][i] for i in range(3)]
        diag = (span[0] ** 2 + span[1] ** 2 + span[2] ** 2) ** 0.5
        sides = set()
        for node in part["nodes"]:
            if node.endswith(".l"):
                sides.add("l")
            elif node.endswith(".r"):
                sides.add("r")
        part["bilateral"] = "l" in sides and "r" in sides and part["kind"] == "muscle"
        part["focus"] = {
            "position": [round(v, 5) for v in c],
            "distance": round(max(0.18, min(1.15, diag * 1.7)), 3),
        }
        part.pop("files", None)
        part.pop("min", None)
        part.pop("max", None)
        parts.append(part)
    parts.sort(key=lambda p: (p["kind"], p["name"]))
    # unique ids
    seen = set()
    for part in parts:
        if part["id"] in seen:
            part["id"] = part["id"] + "-2"
        seen.add(part["id"])
    payload = {
        "version": 1,
        "source": "Z-Anatomy Startup.blend (2 May 2023)",
        "license": "CC BY-SA 4.0",
        "count": len(parts),
        "parts": parts,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("parts", len(parts), "bytes", os.path.getsize(OUT))
    from collections import Counter
    print(Counter(p["kind"] for p in parts))


if __name__ == "__main__":
    main()
