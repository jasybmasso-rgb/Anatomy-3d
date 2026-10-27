type ChainNames = { fr: string; en: string };

export type ChainSchoolId = "myers" | "meziere" | "gds" | "busquet";

export type ChainSchool = {
  id: ChainSchoolId;
  label: string;
  summary: string;
  explanation: string;
  credit: string;
  groups: { id: string; label: string }[];
};

/** Shown with every model. These readings are pedagogical, not a scientific consensus. */
export const CHAIN_MODELS_NOTE =
  "Ce modèle n’est pas un consensus scientifique : c’est une grille pédagogique, plus simple que l’anatomie réelle. Le texte est original et ne reprend pas les ouvrages sources.";

const STORAGE_KEY = "anatomy3d.chainSchool";

export const CHAIN_SCHOOLS: ChainSchool[] = [
  {
    id: "myers",
    label: "Myers (Anatomy Trains)",
    summary: "Méridiens myofasciaux : des lignes continues, droites ou en diagonale, pour lire le mouvement.",
    explanation:
      "Thomas W. Myers a popularisé des méridiens myofasciaux qui relient des muscles et des fascias déjà voisins, comme des rails de longueur plutôt que comme des muscles isolés. L’idée : une tension se propage le long d’une ligne, du pied vers la tête ou d’une ceinture vers l’autre. Les lignes sont définies par la continuité de direction (superficielle postérieure, superficielle antérieure, latérale, spirale, profonde, bras, fonctionnelles). On s’en sert comme grille de lecture du mouvement, pas comme carte anatomique unique ni comme protocole clinique.",
    credit:
      "Thomas W. Myers, Anatomy Trains (méridiens myofasciaux). Texte de l’application original.",
    groups: [
      { id: "principal", label: "Lignes principales" },
      { id: "bras", label: "Lignes du bras" },
      { id: "fonctionnelle", label: "Lignes fonctionnelles" },
    ],
  },
  {
    id: "meziere",
    label: "Françoise Mézière",
    summary: "La grande chaîne postérieure est la chaîne maîtresse ; les chaînes antérieures décrivent l’enroulement.",
    explanation:
      "Françoise Mézière, physiothérapeute française, a proposé de lire la posture comme des muscles qui se raccourcissent ensemble. Le corps debout est tiré par des chaînes trop courtes : on cherche à les allonger sur toute leur longueur, plutôt que de renforcer un seul segment déjà bref. La chaîne principale est la grande chaîne postérieure, de la voûte plantaire à l’occiput. Trois chaînes antérieures complètent la lecture : le cou (flexion et plan hyoïdien), le membre supérieur (enroulement vers l’avant) et l’antéro-interne (psoas, adducteurs, sangle abdominale et diaphragme).",
    credit:
      "Méthode de Françoise Mézière (grande chaîne postérieure et chaînes antérieures). Texte original, d’après l’enseignement de la méthode.",
    groups: [
      { id: "principale", label: "Chaîne principale" },
      { id: "anterieures", label: "Chaînes antérieures" },
    ],
  },
  {
    id: "gds",
    label: "GDS (Godelieve Denys-Struyf)",
    summary: "Six directions articulaires (AM, PM, PA, AP, AL, PL), chacune avec sa couleur d’enseignement.",
    explanation:
      "Godelieve Denys-Struyf a décrit six chaînes musculaires et articulaires pour relier un geste, une articulation et une manière de se tenir. Chaque sigle est une direction : AM s’enroule sur l’axe, PM se grandit vers l’arrière, PA va du dos vers le devant, AP du devant vers le dos, AL avance sur le côté, PL retient en arrière et latéralement. Une chaîne regroupe les muscles qui tirent dans cette logique, du pied à la tête ou sur un segment. On les affiche séparément. Les couleurs (rouge, bleu, vert, or, orange, violet) sont celles de l’enseignement GDS, reprises ici comme repère visuel.",
    credit:
      "Chaînes musculaires et articulaires de Godelieve Denys-Struyf (AM, PM, PA, AP, AL, PL) et leurs couleurs d’enseignement. Texte original.",
    groups: [{ id: "six", label: "Les six chaînes" }],
  },
  {
    id: "busquet",
    label: "Léopold Busquet",
    summary: "Statique, flexion, extension, fermeture, ouverture, et une chaîne viscérale.",
    explanation:
      "Léopold Busquet a organisé muscles, fascias et viscères en chaînes qui tirent dans le même sens. Une chaîne droite reste du même côté : l’antérieure fléchit, la postérieure étend. Une chaîne croisée traverse la ligne médiane : l’antérieure ferme, la postérieure ouvre. La statique postérieure est le hauban tonique qui tient le tronc debout, avec peu de déplacement. La chaîne viscérale rappelle que le diaphragme, la paroi et les organes suspendus participent à la forme du tronc.",
    credit:
      "Chaînes physiologiques de Léopold Busquet (statique postérieure, droites, croisées, viscérale). Texte original.",
    groups: [
      { id: "statique", label: "Statique" },
      { id: "droites", label: "Chaînes droites" },
      { id: "croisees", label: "Chaînes croisées" },
      { id: "viscerale", label: "Chaîne viscérale" },
    ],
  },
];

export type ExtraChain = {
  id: string;
  sigle: string;
  school: ChainSchoolId;
  group: string;
  name: ChainNames;
  description: ChainNames;
  tint: string;
};

export const EXTRA_CHAINS: ExtraChain[] = [
  {
    id: "meziere-posterieure",
    sigle: "GCP",
    school: "meziere",
    group: "principale",
    name: { fr: "Grande chaîne postérieure", en: "Great posterior chain" },
    description: {
      fr: "C’est la chaîne maîtresse de cette lecture. Elle réunit ce qui rapproche le talon de l’occiput : voûte plantaire, mollet, ischio-jambiers, plan des érecteurs et nuque. Quand elle se raccourcit, le corps se ferme vers l’arrière — lordose plus marquée, genoux qui cherchent l’extension, tête tirée en arrière. On la parcourt du pied vers la tête pour voir où la longueur manque.",
      en: "The master chain of this reading, from the heel toward the occiput.",
    },
    tint: "#1f7a4d",
  },
  {
    id: "meziere-cervicale",
    sigle: "CAC",
    school: "meziere",
    group: "anterieures",
    name: { fr: "Chaîne antérieure du cou", en: "Anterior cervical chain" },
    description: {
      fr: "Elle regroupe les muscles qui fléchissent la tête et le cou et qui tirent l’hyoïde vers le sternum. Une tête projetée, un cou court en avant et une respiration haute s’y lisent ensemble. Le parcours va des scalènes et du sterno-cléido-mastoïdien vers la mandibule et la base du crâne.",
      en: "Flexors of the head and neck, plus the hyoid sling.",
    },
    tint: "#c45a3a",
  },
  {
    id: "meziere-brachiale",
    sigle: "CBR",
    school: "meziere",
    group: "anterieures",
    name: { fr: "Chaîne brachiale", en: "Brachial chain" },
    description: {
      fr: "Elle relie la ceinture scapulaire à la main en flexion et en enroulement : pectoraux, coraco-brachial, biceps et fléchisseurs de l’avant-bras. Le raccourcissement se voit comme des épaules qui tombent vers l’avant et des coudes qui restent un peu fléchis. On la suit de la cage thoracique vers la paume.",
      en: "Shoulder girdle to the palm, in flexion and roll-forward.",
    },
    tint: "#8b5a2b",
  },
  {
    id: "meziere-antero-interne",
    sigle: "CAI",
    school: "meziere",
    group: "anterieures",
    name: { fr: "Chaîne antéro-interne", en: "Antero-internal chain" },
    description: {
      fr: "Elle rassemble ce qui ferme le tronc vers l’avant et vers le dedans : diaphragme, sangle abdominale, psoas et adducteurs. Elle explique un bassin qui bascule, des hanches qui se referment et un ventre qui tire le thorax vers le bas. Le fascia transversalis est nommé dans le parcours même lorsqu’aucun maillage distinct n’est disponible.",
      en: "Diaphragm, abdominal wall, psoas and adductors closing the trunk inward.",
    },
    tint: "#a33d55",
  },
  {
    id: "gds-am",
    sigle: "AM",
    school: "gds",
    group: "six",
    name: { fr: "Antéro-médiane", en: "Anteromedian chain" },
    description: {
      fr: "L’AM est la chaîne de l’enroulement sur l’axe. Elle fléchit le tronc et le cou, rapproche le pubis du sternum et fait participer le diaphragme et le plancher pelvien. On l’observe quand le corps se referme vers l’avant, comme pour se protéger, plutôt que quand il se grandit.",
      en: "Midline flexion: abdominal wall, diaphragm, pelvic floor and deep neck flexors.",
    },
    tint: "#c23b4a",
  },
  {
    id: "gds-pm",
    sigle: "PM",
    school: "gds",
    group: "six",
    name: { fr: "Postéro-médiane", en: "Posteromedian chain" },
    description: {
      fr: "La PM est la chaîne qui se grandit vers l’arrière. Érecteurs, fessiers, ischio-jambiers et mollets tiennent l’extension et ouvrent le devant du corps. Une PM trop active se lit comme un dos creusé et une nuque qui tient la tête en arrière.",
      en: "Midline extension, from the plantar vault through the erectors.",
    },
    tint: "#2f5f9a",
  },
  {
    id: "gds-pa",
    sigle: "PA",
    school: "gds",
    group: "six",
    name: { fr: "Postéro-antérieure", en: "Posteroanterior chain" },
    description: {
      fr: "La PA part du dos pour rejoindre le devant : érecteurs latéraux et splénius, trapèze, dentelé, oblique externe, puis moyen fessier, tenseur du fascia lata et fibulaires. Elle tourne et ouvre le tronc vers l’avant sur le côté. On la lit comme un relais, pas comme une deuxième ligne médiane.",
      en: "From the back toward the front, along the lateral trunk and fibular side.",
    },
    tint: "#3d8c6e",
  },
  {
    id: "gds-ap",
    sigle: "AP",
    school: "gds",
    group: "six",
    name: { fr: "Antéro-postérieure", en: "Anteroposterior chain" },
    description: {
      fr: "L’AP part du devant pour revenir vers le dos : grand pectoral et grand dorsal, oblique interne, puis adducteurs et tibial postérieur. En latéralité simple, le segment inférieur est dessiné du côté opposé, parce que cette chaîne se comporte souvent comme une diagonale. Elle referme et ramène le membre vers la ligne médiane.",
      en: "From the front toward the back. The lower limb is drawn on the opposite side.",
    },
    tint: "#d4a017",
  },
  {
    id: "gds-al",
    sigle: "AL",
    school: "gds",
    group: "six",
    name: { fr: "Antéro-latérale", en: "Anterolateral chain" },
    description: {
      fr: "L’AL est la chaîne de l’élan vers l’avant. Sterno-cléido-mastoïdien, scalènes, petit pectoral et biceps portent l’épaule et le coude ; sartorius, quadriceps et tibial antérieur portent la hanche et le pied. Le corps semble partir de l’avant, le genou et le coude un peu fléchis.",
      en: "Forward and lateral: neck, elbow flexors, quadriceps and tibialis anterior.",
    },
    tint: "#e07a2f",
  },
  {
    id: "gds-pl",
    sigle: "PL",
    school: "gds",
    group: "six",
    name: { fr: "Postéro-latérale", en: "Posterolateral chain" },
    description: {
      fr: "La PL retient le geste sur le côté et l’arrière. Trapèze, deltoïde, triceps et extenseurs du poignet freinent le membre supérieur ; moyen et petit fessiers, piriforme, biceps fémoral et fibulaires freinent la hanche et le pied. Elle s’oppose à l’élan de l’AL.",
      en: "The brake on the back and the side: extensors, hip abductors and fibulars.",
    },
    tint: "#6b4c9a",
  },
  {
    id: "busquet-statique",
    sigle: "STAT",
    school: "busquet",
    group: "statique",
    name: { fr: "Statique postérieure", en: "Posterior static chain" },
    description: {
      fr: "C’est le hauban tonique du maintien debout, avec peu de déplacement. Mollet, ischio-jambiers, grand fessier, fascia thoraco-lombaire et érecteurs tiennent le tronc au-dessus du bassin. On la distingue de la chaîne d’extension, qui sert le mouvement vers l’arrière plutôt que l’appui prolongé.",
      en: "Tonic posterior stay of upright posture, distinct from the extension chain.",
    },
    tint: "#3d6b8a",
  },
  {
    id: "busquet-flexion",
    sigle: "FLEX",
    school: "busquet",
    group: "droites",
    name: { fr: "Chaîne droite antérieure (flexion)", en: "Anterior straight chain (flexion)" },
    description: {
      fr: "Chaîne droite : elle fléchit sans changer de côté. Le tibial antérieur et les extenseurs des orteils, le quadriceps, le droit de l’abdomen et le sterno-cléido-mastoïdien rapprochent les segments vers l’avant. Le tendon rotulien fait partie du parcours même s’il n’a pas de maillage distinct.",
      en: "Same-side flexion, from the dorsum of the foot to the sternocleidomastoid.",
    },
    tint: "#d06a4f",
  },
  {
    id: "busquet-extension",
    sigle: "EXT",
    school: "busquet",
    group: "droites",
    name: { fr: "Chaîne droite postérieure (extension)", en: "Posterior straight chain (extension)" },
    description: {
      fr: "Chaîne droite d’extension, du même côté. L’aponévrose plantaire, le triceps sural, les ischio-jambiers, le grand fessier et les érecteurs ouvrent le corps vers l’arrière. Elle sert le mouvement, là où la statique postérieure sert surtout à rester debout.",
      en: "Same-side extension, from the plantar fascia to the suboccipitals.",
    },
    tint: "#3e7d5a",
  },
  {
    id: "busquet-fermeture",
    sigle: "FERM",
    school: "busquet",
    group: "croisees",
    name: { fr: "Chaîne croisée antérieure (fermeture)", en: "Anterior crossed chain (closing)" },
    description: {
      fr: "La fermeture est une diagonale. Le grand pectoral et l’oblique rejoignent les adducteurs du côté opposé : le tronc se referme, une épaule vers la hanche contraire. En latéralité simple, les stations marquées « croise » sont dessinées de l’autre côté.",
      en: "Diagonal closing, from pectoralis major toward the opposite adductors.",
    },
    tint: "#c45c7a",
  },
  {
    id: "busquet-ouverture",
    sigle: "OUV",
    school: "busquet",
    group: "croisees",
    name: { fr: "Chaîne croisée postérieure (ouverture)", en: "Posterior crossed chain (opening)" },
    description: {
      fr: "L’ouverture est l’autre diagonale. Le grand dorsal et le fascia thoraco-lombaire rejoignent le grand fessier et le vaste latéral opposés. Le geste écarte et déroule, une aisselle vers la hanche contraire. Le segment inférieur change de côté quand une seule latéralité est choisie.",
      en: "Diagonal opening, from latissimus dorsi toward the opposite gluteus maximus.",
    },
    tint: "#6a7d3a",
  },
  {
    id: "busquet-viscerale",
    sigle: "VISC",
    school: "busquet",
    group: "viscerale",
    name: { fr: "Chaîne viscérale", en: "Visceral chain" },
    description: {
      fr: "La chaîne viscérale relie le contenu abdominal à la paroi qui le suspend. Le diaphragme au-dessus, le transverse et le plancher pelvien autour, l’œsophage, l’estomac, le foie et la rate au centre. Le péritoine et les mésentères sont nommés dans le parcours ; ils n’ont pas de maillage distinct ici. Ce n’est pas une ligne de membre : c’est la participation des organes à la forme du tronc.",
      en: "Diaphragm, abdominal wall and suspended organs as one trunk chain.",
    },
    tint: "#a67c52",
  },
];

export function isChainSchool(value: string | null | undefined): value is ChainSchoolId {
  return CHAIN_SCHOOLS.some((school) => school.id === value);
}

export function getChainSchool(id: ChainSchoolId): ChainSchool {
  return CHAIN_SCHOOLS.find((school) => school.id === id) ?? CHAIN_SCHOOLS[0];
}

export function loadChainSchool(): ChainSchoolId {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (isChainSchool(value)) return value;
  } catch {
    /* private browsing */
  }
  return "myers";
}

export function saveChainSchool(value: ChainSchoolId) {
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {
    /* ignore quota / private mode */
  }
}
