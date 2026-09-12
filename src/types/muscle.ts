export type MuscleRegion =
  | "membre-supérieur"
  | "membre-inférieur"
  | "tronc"
  | "cou"
  | "épaule"
  | "dos"
  | "main"
  | "pied"
  | "périnée"
  | "tête";

export type MuscleHead = {
  name: string;
  origin: string;
  insertion: string;
};

export type Muscle = {
  id: string;
  name: string;
  nameLatin: string;
  aliases: string[];
  region: MuscleRegion;
  origin: string;
  insertion: string;
  actions: string[];
  secondaryActions?: string[];
  heads?: MuscleHead[];
  focus: {
    position: [number, number, number];
    distance: number;
  };
  fiberAxis?: [number, number, number];
  meshHint?: string;
  meshSource?: "bodyparts3d" | "synthetic";
};

export type { SelectionState } from "./structure";
