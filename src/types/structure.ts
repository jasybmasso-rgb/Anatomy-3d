export type StructureKind = "muscle" | "nerve" | "organ" | "vessel";

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
