/** Which abdominal-wall mesh is shown. Persisted so the choice survives reload. */
export type AbdoSource = "zanatomy" | "procedural";

const STORAGE_KEY = "anatomy3d.abdoSource";

export function loadAbdoSource(): AbdoSource {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value === "procedural" || value === "zanatomy") return value;
  } catch {
    /* private browsing */
  }
  return "zanatomy";
}

export function saveAbdoSource(value: AbdoSource) {
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {
    /* ignore quota / private mode */
  }
}
