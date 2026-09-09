export type MuscleRegion =
  | "membre-supérieur"
  | "membre-inférieur"
  | "tronc"
  | "cou"
  | "épaule";

export type Muscle = {
  id: string;
  name: string;
  nameLatin: string;
  aliases: string[];
  region: MuscleRegion;
  origin: string;
  insertion: string;
  actions: string[];
  focus: {
    position: [number, number, number];
    distance: number;
  };
  meshHint: string;
};

export type SelectionState = {
  /** Phase 1 : un muscle à la fois. Phase 4 pourra élargir (listes, calques). */
  selectedMuscleId: string | null;
};
