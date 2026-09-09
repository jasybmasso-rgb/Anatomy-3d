export type Landmark = {
  id: string;
  name: string;
  nameLatin: string;
  region: string;
  position: [number, number, number];
  source?: {
    fmaId?: string;
    partName?: string;
    mode?: string;
    precision?: string;
  };
};

export type LandmarksFile = {
  version: number;
  space: {
    up: string;
    units: string;
    figureHeight: number;
    origin: string;
    facing: string;
  };
  precision: string;
  count: number;
  landmarks: Landmark[];
};
