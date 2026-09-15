import type { Muscle } from "../types/muscle";
import { muscles } from "./loadMuscles";
import raw from "./chains.json";

export type ChainNames = {
  fr: string;
  en: string;
};

export type ChainSide = "both" | "left" | "right";

export type MyofascialChain = {
  id: string;
  sigle: string;
  group: "principal" | "bras" | "fonctionnelle";
  name: ChainNames;
  description: ChainNames;
  tint: string;
  muscleIds: string[];
  fasciaIds?: string[];
  /** SPL only: stations on the opposite side of the named spiral (Myers helix). */
  contraMuscleIds?: string[];
};

export type ChainsFile = {
  version: number;
  model: string;
  disclaimer: ChainNames;
  chains: MyofascialChain[];
};

const catalogIds = new Set(muscles.map((muscle) => muscle.id));

function filterKnown(ids: string[], sigle: string, kind = "muscle"): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const id of ids) {
    if (!catalogIds.has(id) || seen.has(id)) continue;
    seen.add(id);
    out.push(id);
  }
  if (kind === "muscle" && out.length !== ids.length) {
    const missing = ids.filter((id) => !catalogIds.has(id));
    if (missing.length > 0) {
      console.warn(`[chains] ${sigle}: identifiants inconnus`, missing);
    }
  }
  return out;
}

const FASCIA_IDS = new Set([
  "tractus-ilio-tibial-d",
  "tractus-ilio-tibial-g",
  "fascia-lata-d",
  "fascia-lata-g",
  "fascia-crural-d",
  "fascia-crural-g",
  "fascia-thoracolombaire",
  "sacro-tubereux-d",
  "sacro-tubereux-g",
  "fascia-nuchal",
]);

function filterFascia(ids: string[] | undefined, sigle: string): string[] {
  if (!ids) return [];
  const out: string[] = [];
  const seen = new Set<string>();
  for (const id of ids) {
    if (!FASCIA_IDS.has(id) || seen.has(id)) continue;
    seen.add(id);
    out.push(id);
  }
  const missing = ids.filter((id) => !FASCIA_IDS.has(id));
  if (missing.length > 0) {
    console.warn(`[chains] ${sigle}: fascias inconnus`, missing);
  }
  return out;
}

export function fasciaSideOf(id: string): ChainSide | "mid" {
  if (id.endsWith("-g")) return "left";
  if (id.endsWith("-d")) return "right";
  return "mid";
}

export function matchesChainSide(id: string, side: ChainSide): boolean {
  if (side === "both") return true;
  const part = fasciaSideOf(id);
  return part === "mid" || part === side;
}

const file = raw as ChainsFile;

export const chainsDisclaimer: ChainNames = file.disclaimer;

export const chains: MyofascialChain[] = file.chains.map((chain) => ({
  ...chain,
  muscleIds: filterKnown(chain.muscleIds, chain.sigle),
  fasciaIds: filterFascia(chain.fasciaIds, chain.sigle),
  contraMuscleIds: chain.contraMuscleIds
    ? filterKnown(chain.contraMuscleIds, `${chain.sigle}-contra`)
    : undefined,
}));

export function getChainById(id: string | null | undefined): MyofascialChain | null {
  if (!id) return null;
  return chains.find((chain) => chain.id === id) ?? null;
}

/** Opposite-side SPL stations when a unilateral spiral is selected. */
export function contraMuscleIdsForChains(activeIds: string[]): Set<string> {
  const ids = new Set<string>();
  for (const chain of chains) {
    if (!activeIds.includes(chain.id)) continue;
    for (const id of chain.contraMuscleIds ?? []) ids.add(id);
  }
  return ids;
}

/** Clip side for a muscle. SPL uses Myers crossed laterality; other chains stay ipsilateral. */
export function chainClipSide(muscleId: string, side: ChainSide, activeIds: string[]): ChainSide {
  if (side === "both") return "both";
  if (contraMuscleIdsForChains(activeIds).has(muscleId)) {
    return side === "right" ? "left" : "right";
  }
  return side;
}

export function chainsForMuscle(muscleId: string, activeIds: string[]): MyofascialChain[] {
  const active = new Set(activeIds);
  return chains.filter((chain) => active.has(chain.id) && chain.muscleIds.includes(muscleId));
}

/** Average tints when a muscle belongs to several selected chains. */
export function tintForMuscle(muscleId: string, activeIds: string[]): string | null {
  const matched = chainsForMuscle(muscleId, activeIds);
  if (matched.length === 0) return null;
  if (matched.length === 1) return matched[0].tint;
  let r = 0;
  let g = 0;
  let b = 0;
  for (const chain of matched) {
    const n = parseInt(chain.tint.replace("#", ""), 16);
    r += (n >> 16) & 255;
    g += (n >> 8) & 255;
    b += n & 255;
  }
  const k = matched.length;
  const hex = (v: number) =>
    Math.round(v / k)
      .toString(16)
      .padStart(2, "0");
  return `#${hex(r)}${hex(g)}${hex(b)}`;
}

export function muscleIdsForChains(activeIds: string[]): string[] {
  const ids = new Set<string>();
  for (const chain of chains) {
    if (!activeIds.includes(chain.id)) continue;
    for (const id of chain.muscleIds) ids.add(id);
  }
  return [...ids];
}

export function musclesInChains(list: Muscle[], activeIds: string[]): Muscle[] {
  const ids = new Set(muscleIdsForChains(activeIds));
  return list.filter((muscle) => ids.has(muscle.id));
}

export function fasciaIdsForChains(activeIds: string[]): string[] {
  const ids = new Set<string>();
  for (const chain of chains) {
    if (!activeIds.includes(chain.id)) continue;
    for (const id of chain.fasciaIds ?? []) ids.add(id);
  }
  return [...ids];
}

export function tintForFascia(fasciaId: string, activeIds: string[]): string | null {
  const matched = chains.filter(
    (chain) => activeIds.includes(chain.id) && (chain.fasciaIds ?? []).includes(fasciaId),
  );
  if (matched.length === 0) return null;
  if (matched.length === 1) return matched[0].tint;
  let r = 0;
  let g = 0;
  let b = 0;
  for (const chain of matched) {
    const n = parseInt(chain.tint.replace("#", ""), 16);
    r += (n >> 16) & 255;
    g += (n >> 8) & 255;
    b += n & 255;
  }
  const k = matched.length;
  const hex = (v: number) =>
    Math.round(v / k)
      .toString(16)
      .padStart(2, "0");
  return `#${hex(r)}${hex(g)}${hex(b)}`;
}
