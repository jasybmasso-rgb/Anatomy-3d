import type { StructureKind } from "../types/structure";
import { muscles } from "./loadMuscles";
import raw from "./zanatomyParts.json";

export type ZaPart = {
  id: string;
  name: string;
  nameLatin: string;
  aliases: string[];
  region: string;
  notes: string;
  source: "zanatomy";
  kind: StructureKind;
  file: string;
  nodes: string[];
  centroid: [number, number, number];
  focus: { position: [number, number, number]; distance: number };
  triangles: number;
  vesselKind?: "artery" | "vein";
  tissue?: "cartilage";
  bilateral?: boolean;
};

type Catalog = { version: number; parts: ZaPart[] };

export const zaParts: ZaPart[] = (raw as Catalog).parts;

const byId = new Map(zaParts.map((part) => [part.id, part]));

export function getZaById(id: string | null | undefined): ZaPart | null {
  if (!id) return null;
  return byId.get(id) ?? null;
}

const muscleIds = new Set(muscles.map((muscle) => muscle.id));

/** Parts that are not already listed by the muscle fiches. */
export const zaExtraParts: ZaPart[] = zaParts.filter(
  (part) => !(part.kind === "muscle" && muscleIds.has(part.id)),
);

const nodesByFile = new Map<string, ZaPart[]>();
for (const part of zaParts) {
  const list = nodesByFile.get(part.file);
  if (list) list.push(part);
  else nodesByFile.set(part.file, [part]);
}

export function zaPartsForFile(file: string): ZaPart[] {
  return nodesByFile.get(file) ?? [];
}
