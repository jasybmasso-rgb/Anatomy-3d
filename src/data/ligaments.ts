export type LigamentSource = "bodyparts3d" | "synthetic-v2";

export type Ligament = {
  id: string;
  name: string;
  nameLatin: string;
  region: string;
  joint: string;
  notes: string;
  source: LigamentSource;
  sourceName: string;
  fmaId: string;
  fileIds: string[];
  centroid: [number, number, number];
};

export type LigamentsFile = {
  version: number;
  defaultVisible: boolean;
  inclusionRules: string;
  syntheticDisclaimer?: string;
  count: number;
  countBodyparts3d?: number;
  countSynthetic?: number;
  ligaments: Ligament[];
};
