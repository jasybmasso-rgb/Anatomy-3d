import type { VisceraPart } from "../types/structure";
import rawNerves from "./nerves.json";
import rawOrgans from "./organs.json";
import rawVessels from "./vessels.json";

type RawPart = Omit<VisceraPart, "sourceNames" | "aliases" | "fmaIds"> & {
  sourceNames?: string[];
  sourceName?: string;
  aliases?: string[];
  fmaIds?: string[];
  fmaId?: string;
};

function normalize(part: RawPart, kind: VisceraPart["kind"]): VisceraPart {
  const sourceNames = part.sourceNames ?? (part.sourceName ? [part.sourceName] : []);
  const fmaIds = part.fmaIds ?? (part.fmaId ? [part.fmaId] : []);
  return {
    ...part,
    kind,
    aliases: part.aliases ?? [],
    sourceNames,
    fmaIds,
  };
}

export const nerves: VisceraPart[] = ((rawNerves.nerves ?? []) as RawPart[]).map((p) =>
  normalize(p, "nerve"),
);
export const organs: VisceraPart[] = ((rawOrgans.organs ?? []) as RawPart[]).map((p) =>
  normalize(p, "organ"),
);
export const vessels: VisceraPart[] = ((rawVessels.vessels ?? []) as RawPart[]).map((p) =>
  normalize(p, "vessel"),
);

export function getNerveById(id: string | null): VisceraPart | null {
  if (!id) return null;
  return nerves.find((part) => part.id === id) ?? null;
}

export function getOrganById(id: string | null): VisceraPart | null {
  if (!id) return null;
  return organs.find((part) => part.id === id) ?? null;
}

export function getVesselById(id: string | null): VisceraPart | null {
  if (!id) return null;
  return vessels.find((part) => part.id === id) ?? null;
}

export function getVisceraById(
  kind: "nerve" | "organ" | "vessel",
  id: string | null,
): VisceraPart | null {
  if (kind === "nerve") return getNerveById(id);
  if (kind === "organ") return getOrganById(id);
  return getVesselById(id);
}
