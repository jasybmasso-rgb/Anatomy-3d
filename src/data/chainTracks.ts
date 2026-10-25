import type { ModelSource } from "../scene/modelSource";

export type StationRole = "muscle" | "fascia" | "ligament";
export type PickKind = "muscle" | "fascia" | "ligament" | "organ";

/** One stop on a Myers track, distal-to-cranial or as noted by the chain direction. */
export type ChainStation = {
  role: StationRole;
  label: string;
  /** Bilateral muscle, or a midline fascia/ligament mesh. */
  id?: string;
  leftId?: string;
  rightId?: string;
  /** Mesh catalog when it differs from the anatomical role (procedural meshes). */
  pickKind?: PickKind;
  /** Z-Anatomy file kind when it differs from pickKind (sacrotuberous ligament lives with ligaments). */
  zaKind?: PickKind;
  /** Present only on the Z-Anatomy meshes. Procedural mode keeps the station as a gap. */
  zaOnly?: boolean;
  /** Present on the procedural meshes, absent from Z-Anatomy. */
  missingInZa?: boolean;
  /** Drawn on the opposite side when a single side is chosen (SPL, FFL, BFL). */
  crosses?: boolean;
  /** No left/right half (thoracolumbar fascia, pubic symphysis, galea). */
  midline?: boolean;
};

export type ChainTrack = {
  direction: string;
  stations: ChainStation[];
};

function muscle(id: string, label: string, crosses = false, missingInZa = false): ChainStation {
  return {
    role: "muscle",
    label,
    id,
    pickKind: "muscle",
    crosses,
    missingInZa: missingInZa || undefined,
  };
}

function fasciaPair(leftId: string, rightId: string, label: string, crosses = false): ChainStation {
  return { role: "fascia", label, leftId, rightId, pickKind: "fascia", crosses };
}

function fasciaMid(id: string, label: string): ChainStation {
  return { role: "fascia", label, id, pickKind: "fascia", midline: true };
}

function ligamentPair(leftId: string, rightId: string, label: string, crosses = false): ChainStation {
  return { role: "ligament", label, leftId, rightId, pickKind: "fascia", zaKind: "ligament", crosses };
}

function ligamentMid(id: string, label: string): ChainStation {
  return { role: "ligament", label, id, pickKind: "fascia", zaKind: "ligament", midline: true };
}

function zaFascia(leftId: string, rightId: string, label: string): ChainStation {
  return { role: "fascia", label, leftId, rightId, pickKind: "fascia", zaOnly: true };
}

function gap(role: StationRole, label: string, opts?: { crosses?: boolean; midline?: boolean }): ChainStation {
  return { role, label, crosses: opts?.crosses, midline: opts?.midline };
}

export const CHAIN_TRACKS: Record<string, ChainTrack> = {
  sbl: {
    direction: "De la voûte plantaire vers le front",
    stations: [
      zaFascia("aponévrose-plantaire-g", "aponévrose-plantaire-d", "Aponévrose plantaire"),
      muscle("court-flechisseur-des-orteils", "Court fléchisseur des orteils"),
      muscle("abducteur-de-l-hallux", "Abducteur de l’hallux"),
      muscle("abducteur-du-petit-orteil", "Abducteur du petit orteil"),
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
      muscle("plantaire", "Plantaire"),
      muscle("biceps-femoral", "Biceps fémoral"),
      muscle("semi-tendineux", "Semi-tendineux"),
      muscle("semi-membraneux", "Semi-membraneux"),
      ligamentPair("sacro-tubereux-g", "sacro-tubereux-d", "Ligament sacro-tubéreux"),
      fasciaMid("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
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
      zaFascia("fascia-epicranien-g", "fascia-epicranien-d", "Fascia épicrânien"),
    ],
  },
  sfl: {
    direction: "Du dos du pied vers la mastoïde",
    stations: [
      muscle("extenseur-long-des-orteils", "Extenseur long des orteils"),
      muscle("extenseur-long-de-l-hallux", "Extenseur long de l’hallux"),
      muscle("tibial-anterieur", "Tibial antérieur"),
      gap("ligament", "Tendon rotulien"),
      muscle("droit-femoral", "Droit fémoral"),
      muscle("vaste-intermediaire", "Vaste intermédiaire"),
      muscle("vaste-lateral", "Vaste latéral"),
      muscle("vaste-medial", "Vaste médial"),
      muscle("droit-abdomen", "Droit de l’abdomen", false),
      gap("fascia", "Fascia sternal", { midline: true }),
      muscle("sterno-cleido-mastoidien", "Sterno-cléido-mastoïdien"),
      zaFascia("fascia-epicranien-g", "fascia-epicranien-d", "Fascia du cuir chevelu"),
    ],
  },
  ll: {
    direction: "De la malléole externe vers le crâne",
    stations: [
      muscle("long-fibulaire", "Long fibulaire"),
      muscle("court-fibulaire", "Court fibulaire"),
      muscle("troisieme-fibulaire", "Troisième fibulaire"),
      fasciaPair("fascia-crural-g", "fascia-crural-d", "Fascia crural"),
      {
        role: "ligament",
        label: "Ligament antérieur de la tête de la fibula",
        leftId: "ligament-tete-fibula-g",
        rightId: "ligament-tete-fibula-d",
        pickKind: "ligament",
        zaOnly: true,
      },
      fasciaPair("tractus-ilio-tibial-g", "tractus-ilio-tibial-d", "Tractus ilio-tibial"),
      fasciaPair("fascia-lata-g", "fascia-lata-d", "Fascia lata"),
      muscle("tenseur-du-fascia-lata", "Tenseur du fascia lata"),
      muscle("moyen-fessier", "Moyen fessier"),
      muscle("petit-fessier", "Petit fessier"),
      muscle("grand-fessier", "Grand fessier"),
      muscle("oblique-externe", "Oblique externe"),
      muscle("oblique-interne", "Oblique interne"),
      muscle("intercostaux-externes", "Intercostaux externes"),
      muscle("intercostaux-internes", "Intercostaux internes"),
      muscle("splenius-de-la-tete", "Splénius de la tête"),
      muscle("splenius-du-cou", "Splénius du cou"),
      muscle("sterno-cleido-mastoidien", "Sterno-cléido-mastoïdien"),
    ],
  },
  spl: {
    direction: "Du splénius, en hélice, jusqu’au retour par les érecteurs",
    stations: [
      muscle("splenius-de-la-tete", "Splénius de la tête"),
      muscle("splenius-du-cou", "Splénius du cou"),
      muscle("grand-rhomboide", "Grand rhomboïde", true),
      muscle("petit-rhomboide", "Petit rhomboïde", true),
      muscle("dentele-anterieur", "Dentelé antérieur", true),
      muscle("oblique-externe", "Oblique externe", true),
      muscle("oblique-interne", "Oblique interne"),
      muscle("tenseur-du-fascia-lata", "Tenseur du fascia lata"),
      fasciaPair("tractus-ilio-tibial-g", "tractus-ilio-tibial-d", "Tractus ilio-tibial"),
      muscle("tibial-anterieur", "Tibial antérieur"),
      muscle("long-fibulaire", "Long fibulaire"),
      muscle("biceps-femoral", "Biceps fémoral"),
      ligamentPair("sacro-tubereux-g", "sacro-tubereux-d", "Ligament sacro-tubéreux"),
      fasciaMid("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
      muscle("iliocostal-lombaire", "Iliocostal lombaire"),
      muscle("iliocostal-thoracique", "Iliocostal thoracique"),
      muscle("longissimus-du-thorax", "Longissimus du thorax"),
      muscle("epineux-du-thorax", "Épineux du thorax"),
      muscle("semi-epineux-de-la-tete", "Semi-épineux de la tête"),
      ligamentMid("fascia-nuchal", "Ligament nuchal"),
    ],
  },
  dfl: {
    direction: "De la voûte plantaire profonde vers le plancher buccal",
    stations: [
      muscle("tibial-posterieur", "Tibial postérieur"),
      muscle("flechisseur-long-des-orteils", "Fléchisseur long des orteils"),
      muscle("flechisseur-long-de-l-hallux", "Fléchisseur long de l’hallux"),
      muscle("poplite", "Poplité"),
      gap("fascia", "Septum intermusculaire postérieur de la cuisse"),
      muscle("grand-adducteur", "Grand adducteur"),
      muscle("long-adducteur", "Long adducteur"),
      muscle("court-adducteur", "Court adducteur"),
      muscle("petit-adducteur", "Petit adducteur"),
      muscle("gracile", "Gracile"),
      muscle("pectine", "Pectiné"),
      muscle("pubo-coccygien", "Pubo-coccygien"),
      muscle("ilio-coccygien", "Ilio-coccygien"),
      muscle("pubo-rectal", "Pubo-rectal", false, true),
      muscle("coccygien", "Coccygien"),
      muscle("iliopsoas", "Iliopsoas"),
      muscle("diaphragme", "Diaphragme"),
      gap("fascia", "Fascia endothoracique et péricarde", { midline: true }),
      muscle("transverse-du-thorax", "Transverse du thorax"),
      muscle("intercostaux-internes", "Intercostaux internes"),
      muscle("intercostaux-intimes", "Intercostaux intimes"),
      muscle("scalene-anterieur", "Scalène antérieur"),
      muscle("scalene-moyen", "Scalène moyen"),
      muscle("scalene-posterieur", "Scalène postérieur"),
      muscle("long-du-cou", "Long du cou"),
      muscle("long-de-la-tete", "Long de la tête"),
      muscle("droit-anterieur-de-la-tete", "Droit antérieur de la tête"),
      muscle("droit-lateral-de-la-tete", "Droit latéral de la tête"),
      muscle("sterno-hyoidien", "Sterno-hyoïdien"),
      muscle("sterno-thyroidien", "Sterno-thyroïdien"),
      muscle("omo-hyoidien", "Omo-hyoïdien"),
      muscle("thyro-hyoidien", "Thyro-hyoïdien"),
      muscle("genio-hyoidien", "Génio-hyoïdien"),
      muscle("mylo-hyoidien", "Mylo-hyoïdien"),
      {
        role: "muscle",
        label: "Langue",
        id: "langue",
        pickKind: "organ",
        midline: true,
        zaOnly: true,
      },
    ],
  },
  sfal: {
    direction: "Du torse vers la paume",
    stations: [
      muscle("grand-pectoral", "Grand pectoral"),
      muscle("grand-dorsal", "Grand dorsal"),
      zaFascia("septum-medial-bras-g", "septum-medial-bras-d", "Septum intermusculaire médial"),
      muscle("long-palmaire", "Long palmaire"),
      muscle("flechisseur-radial-du-carpe", "Fléchisseur radial du carpe"),
      muscle("flechisseur-ulnaire-du-carpe", "Fléchisseur ulnaire du carpe"),
      muscle("flechisseur-superficiel-des-doigts", "Fléchisseur superficiel des doigts"),
      {
        role: "ligament",
        label: "Rétinaculum des fléchisseurs",
        leftId: "retinaculum-flechisseurs-g",
        rightId: "retinaculum-flechisseurs-d",
        pickKind: "fascia",
        zaOnly: true,
      },
      zaFascia("aponévrose-palmaire-g", "aponévrose-palmaire-d", "Aponévrose palmaire"),
    ],
  },
  dfal: {
    direction: "Du petit pectoral vers le pouce",
    stations: [
      muscle("petit-pectoral", "Petit pectoral"),
      zaFascia("fascia-clavipectoral-g", "fascia-clavipectoral-d", "Fascia clavipectoral"),
      muscle("subclavier", "Subclavier"),
      muscle("biceps-brachial", "Biceps brachial"),
      muscle("coraco-brachial", "Coraco-brachial"),
      muscle("brachial", "Brachial"),
      gap("ligament", "Périoste du radius"),
      muscle("flechisseur-profond-des-doigts", "Fléchisseur profond des doigts"),
      muscle("long-flechisseur-du-pouce", "Long fléchisseur du pouce"),
      muscle("court-abducteur-du-pouce", "Court abducteur du pouce"),
      muscle("opposant-du-pouce", "Opposant du pouce"),
      muscle("court-flechisseur-du-pouce", "Court fléchisseur du pouce"),
    ],
  },
  sbal: {
    direction: "Du trapèze vers le dos de la main",
    stations: [
      muscle("trapeze", "Trapèze"),
      muscle("deltoide", "Deltoïde"),
      zaFascia("septum-lateral-bras-g", "septum-lateral-bras-d", "Septum intermusculaire latéral"),
      muscle("ancone", "Anconé"),
      muscle("long-extenseur-radial-du-carpe", "Long extenseur radial du carpe"),
      muscle("court-extenseur-radial-du-carpe", "Court extenseur radial du carpe"),
      muscle("extenseur-des-doigts", "Extenseur des doigts"),
      muscle("extenseur-ulnaire-du-carpe", "Extenseur ulnaire du carpe"),
      muscle("extenseur-du-petit-doigt", "Extenseur du petit doigt"),
      muscle("extenseur-de-l-index", "Extenseur de l’index"),
      {
        role: "ligament",
        label: "Rétinaculum des extenseurs",
        leftId: "retinaculum-extenseurs-g",
        rightId: "retinaculum-extenseurs-d",
        pickKind: "fascia",
        zaOnly: true,
      },
    ],
  },
  dbal: {
    direction: "Des rhomboïdes vers l’auriculaire",
    stations: [
      muscle("grand-rhomboide", "Grand rhomboïde"),
      muscle("petit-rhomboide", "Petit rhomboïde"),
      muscle("elevateur-de-la-scapula", "Élévateur de la scapula"),
      muscle("supra-epineux", "Supra-épineux"),
      muscle("infra-epineux", "Infra-épineux"),
      muscle("petit-rond", "Petit rond"),
      muscle("subscapulaire", "Subscapulaire"),
      muscle("grand-rond", "Grand rond"),
      muscle("triceps-brachial", "Triceps brachial"),
      gap("ligament", "Périoste de l’ulna"),
      muscle("abducteur-du-petit-doigt", "Abducteur du petit doigt"),
      muscle("opposant-du-petit-doigt", "Opposant du petit doigt"),
      muscle("court-flechisseur-du-petit-doigt", "Court fléchisseur du petit doigt"),
    ],
  },
  ffl: {
    direction: "Du grand pectoral vers le long adducteur opposé",
    stations: [
      muscle("grand-pectoral", "Grand pectoral"),
      muscle("droit-abdomen", "Droit de l’abdomen"),
      {
        role: "ligament",
        label: "Symphyse pubienne",
        id: "symphyse-pubienne",
        pickKind: "ligament",
        midline: true,
        zaOnly: true,
      },
      muscle("long-adducteur", "Long adducteur", true),
    ],
  },
  bfl: {
    direction: "Du grand dorsal vers le vaste latéral opposé",
    stations: [
      muscle("grand-dorsal", "Grand dorsal"),
      fasciaMid("fascia-thoracolombaire", "Fascia thoraco-lombaire"),
      muscle("grand-fessier", "Grand fessier", true),
      muscle("vaste-lateral", "Vaste latéral", true),
    ],
  },
  ifl: {
    direction: "Du grand dorsal vers le sartorius du même côté",
    stations: [
      muscle("grand-dorsal", "Grand dorsal"),
      muscle("oblique-externe", "Oblique externe"),
      muscle("sartorius", "Sartorius"),
    ],
  },
};

export function trackFor(chainId: string): ChainTrack | null {
  return CHAIN_TRACKS[chainId] ?? null;
}

export type StationSide = "left" | "right" | "both" | "mid";
type Laterality = "both" | "left" | "right";

export function stationSide(station: ChainStation, side: Laterality): StationSide {
  if (station.midline) return "mid";
  if (side === "both") return "both";
  if (station.crosses) return side === "left" ? "right" : "left";
  return side;
}

export const STATION_SIDE_LABEL: Record<StationSide, string> = {
  left: "Gauche",
  right: "Droite",
  both: "Gauche et droite",
  mid: "Médian",
};

export const STATION_ROLE_LABEL: Record<StationRole, string> = {
  muscle: "Muscle",
  fascia: "Fascia",
  ligament: "Ligament",
};

export type StationTarget = { kind: PickKind; id: string };

/** Mesh to select for the active laterality, or null when the station has no model. */
export function stationTarget(
  station: ChainStation,
  side: Laterality,
  modelSource: ModelSource = "zanatomy",
): StationTarget | null {
  if (station.zaOnly && modelSource !== "zanatomy") return null;
  if (station.missingInZa && modelSource === "zanatomy") return null;
  const kind =
    (modelSource === "zanatomy" ? station.zaKind : undefined) ??
    station.pickKind ??
    (station.role === "ligament" ? "fascia" : station.role);
  if (station.leftId || station.rightId) {
    const which = stationSide(station, side);
    const id =
      which === "right"
        ? station.rightId
        : which === "left"
          ? station.leftId
          : (station.leftId ?? station.rightId);
    if (!id) return null;
    return { kind, id };
  }
  if (!station.id) return null;
  return { kind, id: station.id };
}

export function muscleIdsOf(chainId: string): string[] {
  const track = trackFor(chainId);
  if (!track) return [];
  const ids: string[] = [];
  for (const station of track.stations) {
    if (station.zaOnly) continue;
    if (station.role === "muscle" && station.id) ids.push(station.id);
  }
  return ids;
}

export function contraMuscleIdsOf(chainId: string): string[] {
  const track = trackFor(chainId);
  if (!track) return [];
  return track.stations
    .filter((station) => station.role === "muscle" && station.crosses && station.id)
    .map((station) => station.id as string);
}

export function fasciaIdsOf(chainId: string): string[] {
  const track = trackFor(chainId);
  if (!track) return [];
  const ids: string[] = [];
  for (const station of track.stations) {
    if (station.zaOnly) continue;
    const kind = station.pickKind ?? (station.role === "ligament" ? "fascia" : station.role);
    if (kind !== "fascia") continue;
    for (const id of [station.id, station.leftId, station.rightId]) {
      if (id) ids.push(id);
    }
  }
  return ids;
}
