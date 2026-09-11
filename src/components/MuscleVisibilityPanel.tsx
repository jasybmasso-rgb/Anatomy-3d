import { useMemo } from "react";
import type { Muscle } from "../types/muscle";
import type { ConnectivePart, HiddenMap, StructureKind, VisceraPart } from "../types/structure";
import { STRUCTURE_KIND_LABEL } from "../types/structure";

type Named = { kind: StructureKind; id: string; name: string };

type MuscleVisibilityPanelProps = {
  muscles: Muscle[];
  viscera: VisceraPart[];
  connective: ConnectivePart[];
  selectedKind: StructureKind | null;
  selectedId: string | null;
  selectedName: string | null;
  showAllMuscles: boolean;
  hiddenIds: HiddenMap;
  onShowAll: (value: boolean) => void;
  onHiddenChange: (kind: StructureKind, id: string, hide: boolean) => void;
};

function hideLabel(kind: StructureKind | null): string {
  if (kind === "muscle") return "Masquer ce muscle";
  if (kind === "ligament") return "Masquer ce ligament";
  if (kind === "fascia") return "Masquer ce fascia";
  if (kind === "nerve") return "Masquer ce nerf";
  if (kind === "organ") return "Masquer cet organe";
  if (kind === "vessel") return "Masquer ce vaisseau";
  return "Masquer cette structure";
}

export function MuscleVisibilityPanel({
  muscles,
  viscera,
  connective,
  selectedKind,
  selectedId,
  selectedName,
  showAllMuscles,
  hiddenIds,
  onShowAll,
  onHiddenChange,
}: MuscleVisibilityPanelProps) {
  const lookup = useMemo(() => {
    const map = new Map<string, Named>();
    for (const muscle of muscles) map.set(`muscle:${muscle.id}`, { kind: "muscle", id: muscle.id, name: muscle.name });
    for (const part of viscera) map.set(`${part.kind}:${part.id}`, { kind: part.kind, id: part.id, name: part.name });
    for (const part of connective) map.set(`${part.kind}:${part.id}`, { kind: part.kind, id: part.id, name: part.name });
    return map;
  }, [muscles, viscera, connective]);

  const hiddenRows = useMemo(() => {
    const rows: Named[] = [];
    (Object.keys(hiddenIds) as StructureKind[]).forEach((kind) => {
      for (const id of hiddenIds[kind]) {
        rows.push(lookup.get(`${kind}:${id}`) ?? { kind, id, name: id });
      }
    });
    return rows;
  }, [hiddenIds, lookup]);

  const selectedHidden =
    selectedKind && selectedId ? hiddenIds[selectedKind].includes(selectedId) : false;

  return (
    <section className="muscle-tools" aria-label="Affichage des structures">
      <label className="muscle-tools-toggle">
        <input
          type="checkbox"
          checked={showAllMuscles}
          onChange={(event) => onShowAll(event.target.checked)}
        />
        <span>Afficher tous les muscles</span>
      </label>
      <p className="muscle-tools-hint">
        Cliquez une structure dans la scène pour la sélectionner. Une fois choisie, masquez-la ici
        pour lire les couches profondes. Un second clic au même endroit cycle les pièces
        superposées (fascia, ligament, muscle…).
      </p>
      {selectedKind && selectedId && selectedName ? (
        <label className="muscle-tools-toggle muscle-tools-hide-selected">
          <input
            type="checkbox"
            checked={selectedHidden}
            onChange={(event) => onHiddenChange(selectedKind, selectedId, event.target.checked)}
          />
          <span>{hideLabel(selectedKind)}</span>
        </label>
      ) : null}
      {hiddenRows.length > 0 ? (
        <ul className="hidden-chips" aria-label="Structures masquées">
          {hiddenRows.slice(0, 12).map((row) => (
            <li key={`${row.kind}:${row.id}`}>
              <button
                type="button"
                className="hidden-chip"
                onClick={() => onHiddenChange(row.kind, row.id, false)}
                title="Réafficher"
              >
                {row.name}
                <em className="hidden-chip-kind">{STRUCTURE_KIND_LABEL[row.kind]}</em>
                <span aria-hidden="true">×</span>
              </button>
            </li>
          ))}
          {hiddenRows.length > 12 ? (
            <li className="hidden-chip-more">+{hiddenRows.length - 12}</li>
          ) : null}
        </ul>
      ) : null}
    </section>
  );
}
