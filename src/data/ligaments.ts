export type Ligament = {
  id: string;
  name: string;
  nameLatin: string;
  region: string;
  joint: string;
  notes: string;
  sourceName: string;
  fmaId: string;
  fileIds: string[];
  centroid: [number, number, number];
};

export type LigamentsFile = {
  version: number;
  defaultVisible: boolean;
  inclusionRules: string;
  count: number;
  ligaments: Ligament[];
};
