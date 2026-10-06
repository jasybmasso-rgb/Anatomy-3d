import type { Muscle } from "../types/muscle";
import { normalizeSearch } from "./search";

function haystack(muscle: Muscle): string {
  return [muscle.id, muscle.name, muscle.nameLatin, ...muscle.aliases].join(" ");
}

export function searchMuscles(muscles: Muscle[], query: string): Muscle[] {
  const needle = normalizeSearch(query);
  if (!needle) return [];

  return muscles
    .map((muscle) => {
      const hay = normalizeSearch(haystack(muscle));
      const nameMatch = normalizeSearch(muscle.name).startsWith(needle);
      const idMatch = normalizeSearch(muscle.id).startsWith(needle);
      const index = hay.indexOf(needle);
      if (index < 0) return null;
      const rank = nameMatch || idMatch ? 0 : index;
      return { muscle, rank };
    })
    .filter((row): row is { muscle: Muscle; rank: number } => row !== null)
    .sort((a, b) => a.rank - b.rank || a.muscle.name.localeCompare(b.muscle.name, "fr-CA"))
    .map((row) => row.muscle);
}
