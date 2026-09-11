import type { Muscle } from "../types/muscle";
import type { StructureKind, VisceraPart } from "../types/structure";
import { normalizeSearch } from "./search";

export type SearchHit = {
  kind: StructureKind;
  id: string;
  name: string;
  nameLatin: string;
};

function haystack(id: string, name: string, latin: string, aliases: string[]): string {
  return [id, name, latin, ...aliases].join(" ");
}

function rankRow(id: string, name: string, latin: string, aliases: string[], needle: string) {
  const hay = normalizeSearch(haystack(id, name, latin, aliases));
  const index = hay.indexOf(needle);
  if (index < 0) return null;
  const nameMatch = normalizeSearch(name).startsWith(needle);
  const idMatch = normalizeSearch(id).startsWith(needle);
  const rank = nameMatch || idMatch ? 0 : index;
  return rank;
}

const KIND_ORDER: Record<StructureKind, number> = {
  muscle: 0,
  nerve: 1,
  organ: 2,
  vessel: 3,
};

export function searchStructures(
  muscles: Muscle[],
  viscera: VisceraPart[],
  query: string,
): SearchHit[] {
  const needle = normalizeSearch(query);
  if (!needle) return [];

  const rows: { hit: SearchHit; rank: number }[] = [];
  for (const muscle of muscles) {
    const rank = rankRow(muscle.id, muscle.name, muscle.nameLatin, muscle.aliases, needle);
    if (rank === null) continue;
    rows.push({
      rank,
      hit: {
        kind: "muscle",
        id: muscle.id,
        name: muscle.name,
        nameLatin: muscle.nameLatin,
      },
    });
  }
  for (const part of viscera) {
    const rank = rankRow(part.id, part.name, part.nameLatin, part.aliases, needle);
    if (rank === null) continue;
    rows.push({
      rank,
      hit: {
        kind: part.kind,
        id: part.id,
        name: part.name,
        nameLatin: part.nameLatin,
      },
    });
  }

  return rows
    .sort(
      (a, b) =>
        a.rank - b.rank ||
        KIND_ORDER[a.hit.kind] - KIND_ORDER[b.hit.kind] ||
        a.hit.name.localeCompare(b.hit.name, "fr-CA"),
    )
    .map((row) => row.hit);
}
