import { useMemo } from "react";
import type { Muscle } from "../types/muscle";

type MuscleVisibilityPanelProps = {
  muscles: Muscle[];
  selected: Muscle | null;
  showAllMuscles: boolean;
  hiddenMuscleIds: string[];
  onShowAll: (value: boolean) => void;
  onHiddenChange: (ids: string[]) => void;
};

export function MuscleVisibilityPanel({
  muscles,
  selected,
  showAllMuscles,
  hiddenMuscleIds,
  onShowAll,
  onHiddenChange,
}: MuscleVisibilityPanelProps) {
  const hidden = useMemo(() => new Set(hiddenMuscleIds), [hiddenMuscleIds]);
  const hiddenMuscles = useMemo(
    () => muscles.filter((muscle) => hidden.has(muscle.id)),
    [muscles, hidden],
  );
  const selectedHidden = selected ? hidden.has(selected.id) : false;

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
        Cliquez un muscle dans la scène pour le sélectionner. Une fois choisi, masquez-le ici pour
        lire les couches profondes.
      </p>
      {selected ? (
        <label className="muscle-tools-toggle muscle-tools-hide-selected">
          <input
            type="checkbox"
            checked={selectedHidden}
            onChange={(event) => setHidden(selected.id, event.target.checked)}
          />
          <span>Masquer ce muscle</span>
        </label>
      ) : null}
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
    </section>
  );
}
