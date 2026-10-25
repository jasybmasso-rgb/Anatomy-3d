import type { ChainStation, ChainTrack } from "./chainTracks";

function muscle(id: string, label: string, crosses = false): ChainStation {
  return { role: "muscle", label, id, pickKind: "muscle", crosses };
}

function fasciaPair(leftId: string, rightId: string, label: string): ChainStation {
  return { role: "fascia", label, leftId, rightId, pickKind: "fascia" };
}

function fasciaMid(id: string, label: string): ChainStation {
  return { role: "fascia", label, id, pickKind: "fascia", midline: true };
}

function ligamentPair(leftId: string, rightId: string, label: string): ChainStation {
  return { role: "ligament", label, leftId, rightId, pickKind: "fascia", zaKind: "ligament" };
}

function zaFascia(leftId: string, rightId: string, label: string): ChainStation {
  return { role: "fascia", label, leftId, rightId, pickKind: "fascia", zaOnly: true };
}

function organ(id: string, label: string, zaId: string): ChainStation {
  return { role: "organ", label, id, zaId, pickKind: "organ", midline: true };
}

function gap(role: ChainStation["role"], label: string): ChainStation {
  return { role, label, midline: true };
}

/** Mézière, GDS and Busquet tracks. Stations reuse catalog ids; gaps stay grey in the list. */
export const EXTRA_CHAIN_TRACKS: Record<string, ChainTrack> = {
  "meziere-posterieure": {
    direction: "De la voûte plantaire vers l’occiput",
    stations: [
      zaFascia("aponévrose-plantaire-g", "aponévrose-plantaire-d", "Aponévrose plantaire"),
      muscle("court-flechisseur-des-orteils", "Court fléchisseur des orteils"),
      muscle("abducteur-de-l-hallux", "Abducteur de l’hallux"),
      {
        role: "fascia",
        label: "Tendon calcanéen",
        leftId: "tendon-calcaneen-g",
        rightId: "tendon-calcaneen-d",
        pickKind: "muscle",
        zaOnly: true,
      },
      muscle("gastrocnemien", "Gastrocnémien"),
      muscle("soleaire", "Soléaire"),
      muscle("biceps-femoral", "Biceps fémoral"),
      muscle("semi-tendineux", "Semi-tendineux"),
      muscle("semi-membraneux", "Semi-membraneux"),
      ligamentPair("sacro-tubereux-g", "sacro-tubereux-d", "Ligament sacro-tubéreux"),
      fasciaMid("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
      gap("muscle", "Carré des lombes"),
      muscle("iliocostal-lombaire", "Iliocostal lombaire"),
      muscle("iliocostal-thoracique", "Iliocostal thoracique"),
      muscle("iliocostal-cervical", "Iliocostal cervical"),
      muscle("longissimus-du-thorax", "Longissimus du thorax"),
      muscle("longissimus-du-cou", "Longissimus du cou"),
      muscle("longissimus-de-la-tete", "Longissimus de la tête"),
      muscle("epineux-du-thorax", "Épineux du thorax"),
      muscle("semi-epineux-du-thorax", "Semi-épineux du thorax"),
      muscle("semi-epineux-du-cou", "Semi-épineux du cou"),
      muscle("semi-epineux-de-la-tete", "Semi-épineux de la tête"),
      muscle("grand-droit-posterieur-de-la-tete", "Grand droit postérieur de la tête"),
      muscle("petit-droit-posterieur-de-la-tete", "Petit droit postérieur de la tête"),
      muscle("oblique-inferieur-de-la-tete", "Oblique inférieur de la tête"),
      muscle("oblique-superieur-de-la-tete", "Oblique supérieur de la tête"),
      fasciaMid("fascia-nuchal", "Fascia nuchal"),
    ],
  },
  "meziere-cervicale": {
    direction: "Du sternum et des scalènes vers la mandibule",
    stations: [
      muscle("scalene-anterieur", "Scalène antérieur"),
      muscle("scalene-moyen", "Scalène moyen"),
      muscle("scalene-posterieur", "Scalène postérieur"),
      muscle("sterno-cleido-mastoidien", "Sterno-cléido-mastoïdien"),
      muscle("sterno-hyoidien", "Sterno-hyoïdien"),
      muscle("omo-hyoidien", "Omo-hyoïdien"),
      muscle("thyro-hyoidien", "Thyro-hyoïdien"),
      muscle("genio-hyoidien", "Génio-hyoïdien"),
      muscle("mylo-hyoidien", "Mylo-hyoïdien"),
      muscle("long-du-cou", "Long du cou"),
      muscle("long-de-la-tete", "Long de la tête"),
      muscle("droit-anterieur-de-la-tete", "Droit antérieur de la tête"),
      muscle("droit-lateral-de-la-tete", "Droit latéral de la tête"),
    ],
  },
  "meziere-brachiale": {
    direction: "De la cage thoracique vers la paume",
    stations: [
      muscle("grand-pectoral", "Grand pectoral"),
      muscle("petit-pectoral", "Petit pectoral"),
      muscle("subclavier", "Subclavier"),
      zaFascia("fascia-clavipectoral-g", "fascia-clavipectoral-d", "Fascia clavipectoral"),
      muscle("coraco-brachial", "Coraco-brachial"),
      muscle("biceps-brachial", "Biceps brachial"),
      muscle("brachial", "Brachial"),
      muscle("flechisseur-radial-du-carpe", "Fléchisseur radial du carpe"),
      muscle("flechisseur-ulnaire-du-carpe", "Fléchisseur ulnaire du carpe"),
      muscle("flechisseur-superficiel-des-doigts", "Fléchisseur superficiel des doigts"),
      muscle("flechisseur-profond-des-doigts", "Fléchisseur profond des doigts"),
      zaFascia("aponévrose-palmaire-g", "aponévrose-palmaire-d", "Aponévrose palmaire"),
    ],
  },
  "meziere-antero-interne": {
    direction: "Du diaphragme et du psoas vers les adducteurs",
    stations: [
      muscle("diaphragme", "Diaphragme"),
      muscle("droit-abdomen", "Droit de l’abdomen"),
      muscle("oblique-interne", "Oblique interne"),
      muscle("transverse-de-l-abdomen", "Transverse de l’abdomen"),
      gap("fascia", "Fascia transversalis"),
      muscle("iliopsoas", "Iliopsoas"),
      muscle("pectine", "Pectiné"),
      muscle("long-adducteur", "Long adducteur"),
      muscle("court-adducteur", "Court adducteur"),
      muscle("grand-adducteur", "Grand adducteur"),
      muscle("gracile", "Gracile"),
    ],
  },
  "gds-am": {
    direction: "De la sangle et du diaphragme vers le cou",
    stations: [
      muscle("pubo-coccygien", "Pubo-coccygien"),
      muscle("ilio-coccygien", "Ilio-coccygien"),
      muscle("droit-abdomen", "Droit de l’abdomen"),
      muscle("transverse-de-l-abdomen", "Transverse de l’abdomen"),
      muscle("intercostaux-internes", "Intercostaux internes"),
      muscle("diaphragme", "Diaphragme"),
      muscle("sterno-hyoidien", "Sterno-hyoïdien"),
      muscle("omo-hyoidien", "Omo-hyoïdien"),
      muscle("thyro-hyoidien", "Thyro-hyoïdien"),
      muscle("long-du-cou", "Long du cou"),
      muscle("long-de-la-tete", "Long de la tête"),
    ],
  },
  "gds-pm": {
    direction: "De la voûte plantaire vers la nuque",
    stations: [
      zaFascia("aponévrose-plantaire-g", "aponévrose-plantaire-d", "Aponévrose plantaire"),
      muscle("gastrocnemien", "Gastrocnémien"),
      muscle("soleaire", "Soléaire"),
      muscle("biceps-femoral", "Biceps fémoral"),
      muscle("semi-tendineux", "Semi-tendineux"),
      muscle("semi-membraneux", "Semi-membraneux"),
      muscle("grand-fessier", "Grand fessier"),
      gap("muscle", "Carré des lombes"),
      fasciaMid("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
      muscle("iliocostal-lombaire", "Iliocostal lombaire"),
      muscle("longissimus-du-thorax", "Longissimus du thorax"),
      muscle("epineux-du-thorax", "Épineux du thorax"),
      muscle("semi-epineux-de-la-tete", "Semi-épineux de la tête"),
      muscle("grand-droit-posterieur-de-la-tete", "Grand droit postérieur de la tête"),
      muscle("petit-droit-posterieur-de-la-tete", "Petit droit postérieur de la tête"),
      fasciaMid("fascia-nuchal", "Fascia nuchal"),
    ],
  },
  "gds-pa": {
    direction: "Du dos vers le devant, sur le côté",
    stations: [
      muscle("iliocostal-lombaire", "Iliocostal lombaire"),
      muscle("iliocostal-thoracique", "Iliocostal thoracique"),
      muscle("splenius-du-cou", "Splénius du cou"),
      muscle("splenius-de-la-tete", "Splénius de la tête"),
      muscle("trapeze", "Trapèze"),
      muscle("dentele-anterieur", "Dentelé antérieur"),
      muscle("oblique-externe", "Oblique externe"),
      muscle("moyen-fessier", "Moyen fessier"),
      muscle("tenseur-du-fascia-lata", "Tenseur du fascia lata"),
      fasciaPair("fascia-lata-g", "fascia-lata-d", "Fascia lata"),
      muscle("long-fibulaire", "Long fibulaire"),
      muscle("court-fibulaire", "Court fibulaire"),
    ],
  },
  "gds-ap": {
    direction: "Du devant vers le dos, en diagonale",
    stations: [
      muscle("grand-pectoral", "Grand pectoral"),
      muscle("grand-dorsal", "Grand dorsal"),
      muscle("oblique-interne", "Oblique interne"),
      muscle("long-adducteur", "Long adducteur", true),
      muscle("court-adducteur", "Court adducteur", true),
      muscle("grand-adducteur", "Grand adducteur", true),
      muscle("gracile", "Gracile", true),
      muscle("tibial-posterieur", "Tibial postérieur", true),
    ],
  },
  "gds-al": {
    direction: "Du cou et du pectoral vers le devant de la jambe",
    stations: [
      muscle("sterno-cleido-mastoidien", "Sterno-cléido-mastoïdien"),
      muscle("scalene-anterieur", "Scalène antérieur"),
      muscle("scalene-moyen", "Scalène moyen"),
      muscle("petit-pectoral", "Petit pectoral"),
      muscle("biceps-brachial", "Biceps brachial"),
      muscle("brachial", "Brachial"),
      muscle("sartorius", "Sartorius"),
      muscle("droit-femoral", "Droit fémoral"),
      muscle("vaste-lateral", "Vaste latéral"),
      muscle("vaste-medial", "Vaste médial"),
      muscle("vaste-intermediaire", "Vaste intermédiaire"),
      muscle("tibial-anterieur", "Tibial antérieur"),
    ],
  },
  "gds-pl": {
    direction: "De la ceinture scapulaire vers le dehors du pied",
    stations: [
      muscle("trapeze", "Trapèze"),
      muscle("deltoide", "Deltoïde"),
      muscle("triceps-brachial", "Triceps brachial"),
      muscle("long-extenseur-radial-du-carpe", "Long extenseur radial du carpe"),
      muscle("court-extenseur-radial-du-carpe", "Court extenseur radial du carpe"),
      muscle("extenseur-ulnaire-du-carpe", "Extenseur ulnaire du carpe"),
      muscle("extenseur-des-doigts", "Extenseur des doigts"),
      muscle("moyen-fessier", "Moyen fessier"),
      muscle("petit-fessier", "Petit fessier"),
      muscle("piriforme", "Piriforme"),
      muscle("biceps-femoral", "Biceps fémoral"),
      muscle("long-fibulaire", "Long fibulaire"),
      muscle("court-fibulaire", "Court fibulaire"),
    ],
  },
  "busquet-statique": {
    direction: "Du mollet vers la nuque, en appui tonique",
    stations: [
      muscle("gastrocnemien", "Gastrocnémien"),
      muscle("soleaire", "Soléaire"),
      muscle("biceps-femoral", "Biceps fémoral"),
      muscle("semi-tendineux", "Semi-tendineux"),
      muscle("semi-membraneux", "Semi-membraneux"),
      muscle("grand-fessier", "Grand fessier"),
      fasciaMid("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
      muscle("iliocostal-lombaire", "Iliocostal lombaire"),
      muscle("longissimus-du-thorax", "Longissimus du thorax"),
      muscle("epineux-du-thorax", "Épineux du thorax"),
      muscle("semi-epineux-de-la-tete", "Semi-épineux de la tête"),
      fasciaMid("fascia-nuchal", "Fascia nuchal"),
    ],
  },
  "busquet-flexion": {
    direction: "Du dos du pied vers le sterno-cléido-mastoïdien, du même côté",
    stations: [
      muscle("extenseur-long-des-orteils", "Extenseur long des orteils"),
      muscle("extenseur-long-de-l-hallux", "Extenseur long de l’hallux"),
      muscle("tibial-anterieur", "Tibial antérieur"),
      gap("ligament", "Tendon rotulien"),
      muscle("droit-femoral", "Droit fémoral"),
      muscle("vaste-lateral", "Vaste latéral"),
      muscle("vaste-medial", "Vaste médial"),
      muscle("vaste-intermediaire", "Vaste intermédiaire"),
      muscle("droit-abdomen", "Droit de l’abdomen"),
      muscle("sterno-cleido-mastoidien", "Sterno-cléido-mastoïdien"),
    ],
  },
  "busquet-extension": {
    direction: "De la voûte plantaire vers les sous-occipitaux, du même côté",
    stations: [
      zaFascia("aponévrose-plantaire-g", "aponévrose-plantaire-d", "Aponévrose plantaire"),
      muscle("gastrocnemien", "Gastrocnémien"),
      muscle("soleaire", "Soléaire"),
      muscle("biceps-femoral", "Biceps fémoral"),
      muscle("semi-tendineux", "Semi-tendineux"),
      muscle("semi-membraneux", "Semi-membraneux"),
      muscle("grand-fessier", "Grand fessier"),
      fasciaMid("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
      muscle("iliocostal-lombaire", "Iliocostal lombaire"),
      muscle("longissimus-du-thorax", "Longissimus du thorax"),
      muscle("semi-epineux-de-la-tete", "Semi-épineux de la tête"),
      muscle("grand-droit-posterieur-de-la-tete", "Grand droit postérieur de la tête"),
      muscle("oblique-inferieur-de-la-tete", "Oblique inférieur de la tête"),
      fasciaMid("fascia-nuchal", "Fascia nuchal"),
    ],
  },
  "busquet-fermeture": {
    direction: "Du grand pectoral vers les adducteurs opposés",
    stations: [
      muscle("grand-pectoral", "Grand pectoral"),
      muscle("oblique-externe", "Oblique externe"),
      muscle("droit-abdomen", "Droit de l’abdomen"),
      muscle("pectine", "Pectiné", true),
      muscle("long-adducteur", "Long adducteur", true),
      muscle("court-adducteur", "Court adducteur", true),
      muscle("gracile", "Gracile", true),
    ],
  },
  "busquet-ouverture": {
    direction: "Du grand dorsal vers le grand fessier opposé",
    stations: [
      muscle("grand-dorsal", "Grand dorsal"),
      fasciaMid("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
      muscle("grand-fessier", "Grand fessier", true),
      muscle("moyen-fessier", "Moyen fessier", true),
      muscle("vaste-lateral", "Vaste latéral", true),
    ],
  },
  "busquet-viscerale": {
    direction: "Du plancher pelvien vers le diaphragme et les organes suspendus",
    stations: [
      muscle("pubo-coccygien", "Pubo-coccygien"),
      muscle("ilio-coccygien", "Ilio-coccygien"),
      muscle("transverse-de-l-abdomen", "Transverse de l’abdomen"),
      muscle("diaphragme", "Diaphragme"),
      organ("oesophage", "Œsophage", "za-sophage"),
      organ("estomac", "Estomac", "za-estomac"),
      organ("foie", "Foie", "za-foie"),
      organ("rate", "Rate", "za-rate"),
      gap("fascia", "Péritoine et mésentères"),
    ],
  },
};
