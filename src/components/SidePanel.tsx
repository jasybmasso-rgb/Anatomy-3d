import type { Muscle, MuscleRegion } from "../types/muscle";

const REGION_LABEL: Record<MuscleRegion, string> = {
  "membre-supérieur": "Membre supérieur",
  "membre-inférieur": "Membre inférieur",
  tronc: "Tronc",
  cou: "Cou",
  épaule: "Épaule",
  dos: "Dos",
  main: "Main",
  pied: "Pied",
  périnée: "Périnée",
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
          Recherchez un muscle, puis activez la couche Muscles dans le menu Couches. La fiche
          affiche origines, insertions (tous les chefs) et mouvements. Sélection fine : à venir.
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
        {muscle.heads && muscle.heads.length > 0 ? (
          <div>
            <dt>Chefs</dt>
            <dd>
              <ul className="panel-head">
                {muscle.heads.map((head) => (
                  <li key={head.name}>
                    <strong>{head.name}</strong>
                    <span>
                      O : {head.origin}
                      <br />
                      I : {head.insertion}
                    </span>
                  </li>
                ))}
              </ul>
            </dd>
          </div>
        ) : null}
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
        {muscle.secondaryActions && muscle.secondaryActions.length > 0 ? (
          <div>
            <dt>Mouvements secondaires</dt>
            <dd>
              <ul className="panel-actions">
                {muscle.secondaryActions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </dd>
          </div>
        ) : null}
      </dl>
      {muscle.meshSource === "synthetic" ? (
        <p className="panel-mesh-note">Maillage schématique : absent de BodyParts3D 4.0.</p>
      ) : null}
    </aside>
  );
}
