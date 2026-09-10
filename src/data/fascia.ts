export type FasciaSource = "bodyparts3d" | "synthetic-v2";

export type FasciaPart = {
  id: string;
  name: string;
  nameLatin: string;
  region: string;
  notes: string;
  source: FasciaSource;
  sourceName: string;
  fmaId: string;
  fileIds: string[];
  centroid: [number, number, number];
};

export type FasciaFile = {
  version: number;
  defaultVisible: boolean;
  inclusionRules: string;
  gaps?: string[];
  syntheticDisclaimer?: string;
  count: number;
  countBodyparts3d?: number;
  countSynthetic?: number;
  fascia: FasciaPart[];
};
