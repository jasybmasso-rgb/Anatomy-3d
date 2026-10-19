import type { ConnectivePart } from "../types/structure";
import { focusFromCentroid } from "../types/structure";
import type { FasciaPart } from "./fascia";
import rawFascia from "./fascia.json";
import type { Ligament } from "./ligaments";
import rawLigaments from "./ligaments.json";

function aliasesFor(name: string, latin: string, extra: string[]): string[] {
  return [...new Set([name, latin, ...extra].filter(Boolean))];
}

export const ligaments: ConnectivePart[] = (rawLigaments.ligaments as Ligament[]).map((part) => ({
  id: part.id,
  name: part.name,
  nameLatin: part.nameLatin,
  aliases: aliasesFor(part.name, part.nameLatin, [part.sourceName, part.joint, part.id]),
  region: part.region,
  notes: part.notes,
  source: part.source,
  kind: "ligament",
  joint: part.joint,
  centroid: part.centroid,
  focus: focusFromCentroid(part.centroid, 0.7),
}));

export const fascias: ConnectivePart[] = (rawFascia.fascia as FasciaPart[]).map((part) => ({
  id: part.id,
  name: part.name,
  nameLatin: part.nameLatin,
  aliases: aliasesFor(part.name, part.nameLatin, [part.sourceName, part.id]),
  region: part.region,
  notes: part.notes,
  source: part.source,
  kind: "fascia",
  centroid: part.centroid,
  focus: focusFromCentroid(part.centroid, 0.85),
}));

export const connective: ConnectivePart[] = [...ligaments, ...fascias];

export function getLigamentById(id: string | null): ConnectivePart | null {
  if (!id) return null;
  return ligaments.find((part) => part.id === id) ?? null;
}

export function getFasciaById(id: string | null): ConnectivePart | null {
  if (!id) return null;
  return fascias.find((part) => part.id === id) ?? null;
}

export function getConnectiveById(
  kind: "ligament" | "fascia",
  id: string | null,
): ConnectivePart | null {
  return kind === "ligament" ? getLigamentById(id) : getFasciaById(id);
}
