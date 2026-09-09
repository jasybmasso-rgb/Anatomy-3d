import type { Muscle } from "../types/muscle";
import rawMuscles from "./muscles.json";

export const muscles: Muscle[] = rawMuscles as Muscle[];

export function getMuscleById(id: string | null): Muscle | null {
  if (!id) return null;
  return muscles.find((muscle) => muscle.id === id) ?? null;
}
