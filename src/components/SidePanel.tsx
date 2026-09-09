import type { Muscle, MuscleRegion } from "../types/muscle";

const REGION_LABEL: Record<MuscleRegion, string> = {
  "membre-supérieur": "Membre supérieur",
  "membre-inférieur": "Membre inférieur",
  tronc: "Tronc",
  cou: "Cou",
  épaule: "Épaule",
};

type SidePanelProps = {
  muscle: Muscle | null;
};

export function SidePanel({ muscle }: SidePanelProps) {
  if (!muscle) {
    return (
      <aside className="panel" aria-label="Fiche du muscle">
        <p className="panel-empty-kicker">Aucun muscle sélectionné</p>
        <h2 className="panel-empty-title">Squelette seulement</h2>
        <p className="panel-empty-body">
          Recherchez un muscle par son nom français, son nom latin, un alias ou son identifiant.
          Le maillage stylisé s’affichera sur le squelette, et la caméra se rapprochera du foyer
          anatomique.
        </p>
      </aside>
    );
  }

  return (
    <aside className="panel" aria-label={`Fiche : ${muscle.name}`}>
      <p className="panel-kicker">{REGION_LABEL[muscle.region]}</p>
      <h2 className="panel-title">{muscle.name}</h2>
      <p className="panel-latin">{muscle.nameLatin}</p>
      <dl className="panel-dl">
        <div>
          <dt>Origine</dt>
          <dd>{muscle.origin}</dd>
        </div>
        <div>
          <dt>Insertion</dt>
          <dd>{muscle.insertion}</dd>
        </div>
        <div>
          <dt>Mouvements</dt>
          <dd>
            <ul className="panel-actions">
              {muscle.actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </dd>
        </div>
      </dl>
    </aside>
  );
}
