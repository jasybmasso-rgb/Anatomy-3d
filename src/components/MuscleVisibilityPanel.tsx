import { useMemo, useState } from "react";
import type { Muscle } from "../types/muscle";
import { searchMuscles } from "../lib/searchMuscles";

type MuscleVisibilityPanelProps = {
  muscles: Muscle[];
  showAllMuscles: boolean;
  hiddenMuscleIds: string[];
  onShowAll: (value: boolean) => void;
  onHiddenChange: (ids: string[]) => void;
};

export function MuscleVisibilityPanel({
  muscles,
  showAllMuscles,
  hiddenMuscleIds,
  onShowAll,
  onHiddenChange,
}: MuscleVisibilityPanelProps) {
  const [query, setQuery] = useState("");
  const hidden = useMemo(() => new Set(hiddenMuscleIds), [hiddenMuscleIds]);
  const hiddenMuscles = useMemo(
    () => muscles.filter((muscle) => hidden.has(muscle.id)),
    [muscles, hidden],
  );
  const listed = useMemo(() => {
    const q = query.trim();
    const base = q ? searchMuscles(muscles, q) : [...muscles].sort((a, b) =>
      a.name.localeCompare(b.name, "fr-CA"),
    );
    return base.slice(0, q ? 40 : muscles.length);
  }, [muscles, query]);

  function setHidden(id: string, hide: boolean) {
    const next = new Set(hidden);
    if (hide) next.add(id);
    else next.delete(id);
    onHiddenChange([...next]);
  }

  return (
    <section className="muscle-tools" aria-label="Affichage des muscles">
      <label className="muscle-tools-toggle">
        <input
          type="checkbox"
          checked={showAllMuscles}
          onChange={(event) => onShowAll(event.target.checked)}
        />
        <span>Afficher tous les muscles</span>
      </label>
      <p className="muscle-tools-hint">
        Légère transparence pour la profondeur. Le muscle sélectionné reste plus
        opaque. Masquez-en pour voir les couches profondes.
      </p>
      <div className="muscle-tools-toolbar">
        <button
          type="button"
          className="muscle-tools-mini"
          onClick={() => onHiddenChange([])}
        >
          Tous
        </button>
        <button
          type="button"
          className="muscle-tools-mini"
          onClick={() => onHiddenChange(muscles.map((muscle) => muscle.id))}
        >
          Aucun
        </button>
        <span className="muscle-tools-count">
          {hidden.size === 0
            ? "Aucun masqué"
            : `${hidden.size} masqué${hidden.size > 1 ? "s" : ""}`}
        </span>
      </div>
      {hiddenMuscles.length > 0 ? (
        <ul className="hidden-chips" aria-label="Muscles masqués">
          {hiddenMuscles.slice(0, 12).map((muscle) => (
            <li key={muscle.id}>
              <button
                type="button"
                className="hidden-chip"
                onClick={() => setHidden(muscle.id, false)}
                title="Réafficher"
              >
                {muscle.name}
                <span aria-hidden="true">×</span>
              </button>
            </li>
          ))}
          {hiddenMuscles.length > 12 ? (
            <li className="hidden-chip-more">+{hiddenMuscles.length - 12}</li>
          ) : null}
        </ul>
      ) : null}
      <label className="muscle-tools-search-label" htmlFor="muscle-hide-search">
        Masquer / afficher
      </label>
      <input
        id="muscle-hide-search"
        className="search-input muscle-tools-search"
        type="search"
        placeholder="Rechercher dans la liste…"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      <ul className="muscle-hide-list">
        {listed.map((muscle) => {
          const checked = !hidden.has(muscle.id);
          return (
            <li key={muscle.id}>
              <label className="muscle-hide-item">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(event) => setHidden(muscle.id, !event.target.checked)}
                />
                <span>{muscle.name}</span>
              </label>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
