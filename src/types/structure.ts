export type StructureKind = "muscle" | "ligament" | "fascia" | "nerve" | "organ" | "vessel";

export type FocusTarget = {
  id: string;
  region?: string;
  focus: {
    position: [number, number, number];
    distance: number;
  };
};

export type VisceraPart = {
  id: string;
  name: string;
  nameLatin: string;
  aliases: string[];
  region: string;
  notes: string;
  source: "bodyparts3d" | "synthetic-v2";
  sourceNames: string[];
  fmaIds: string[];
  fileIds: string[];
  centroid: [number, number, number];
  focus: {
    position: [number, number, number];
    distance: number;
  };
  vertexCount?: number;
  faceCount?: number;
  kind: "nerve" | "organ" | "vessel";
  organTone?: string;
  vesselKind?: "artery" | "vein";
};

export type ConnectivePart = {
  id: string;
  name: string;
  nameLatin: string;
  aliases: string[];
  region: string;
  notes: string;
  source: string;
  kind: "ligament" | "fascia";
  joint?: string;
  centroid: [number, number, number];
  focus: {
    position: [number, number, number];
    distance: number;
  };
};

export type VisceraFile = {
  version: number;
  defaultVisible: boolean;
  inclusionRules: string;
  syntheticDisclaimer?: string;
  count: number;
  countBodyparts3d: number;
  countSynthetic: number;
  nerves?: VisceraPart[];
  organs?: VisceraPart[];
  vessels?: VisceraPart[];
};

export type HiddenMap = Record<StructureKind, string[]>;

export const EMPTY_HIDDEN: HiddenMap = {
  muscle: [],
  ligament: [],
  fascia: [],
  nerve: [],
  organ: [],
  vessel: [],
};

export const STRUCTURE_KIND_LABEL: Record<StructureKind, string> = {
  muscle: "Muscle",
  ligament: "Ligament",
  fascia: "Fascia",
  nerve: "Nerf",
  organ: "Organe",
  vessel: "Vaisseau sanguin",
};

export type SelectionState = {
  kind: StructureKind;
  id: string;
} | null;

export function focusFromCentroid(
  centroid: [number, number, number],
  distance = 0.72,
): FocusTarget["focus"] {
  return { position: centroid, distance };
}
