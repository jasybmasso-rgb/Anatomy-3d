/** Whole-model source. Persisted so the choice survives reload. */
export type ModelSource = "zanatomy" | "procedural";

const STORAGE_KEY = "anatomy3d.modelSource";
const LEGACY_ABDO_KEY = "anatomy3d.abdoSource";

export const MODEL_SOURCE_LABEL = "Modèles : Z-Anatomy / Anciens (procéduraux)";

export function loadModelSource(): ModelSource {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === "procedural" || value === "zanatomy") return value;
    // The old abdominal-only switch folds into this global choice.
    const legacy = localStorage.getItem(LEGACY_ABDO_KEY);
    if (legacy === "procedural") return "procedural";
  } catch {
    /* private browsing */
  }
  return "zanatomy";
}

export function saveModelSource(value: ModelSource) {
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {
    /* ignore quota / private mode */
  }
}
