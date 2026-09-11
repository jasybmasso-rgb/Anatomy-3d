import type { ChainSide } from "../data/chains";
import type { Muscle, MuscleRegion } from "../types/muscle";
import { ChainDetails } from "./ChainPicker";
import { MuscleVisibilityPanel } from "./MuscleVisibilityPanel";
import { muscles as allMuscles } from "../data/loadMuscles";

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
  tête: "Tête",
};

type SidePanelProps = {
  muscle: Muscle | null;
  showAllMuscles: boolean;
  hiddenMuscleIds: string[];
  onShowAllMuscles: (value: boolean) => void;
  onHiddenChange: (ids: string[]) => void;
  showChains: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
  onChainSideChange: (side: ChainSide) => void;
};

export function SidePanel({
  muscle,
  showAllMuscles,
  hiddenMuscleIds,
  onShowAllMuscles,
  onHiddenChange,
  showChains,
  activeChainIds,
  chainSide,
  onChainSideChange,
}: SidePanelProps) {
  return (
    <aside className="panel" aria-label={muscle ? `Fiche : ${muscle.name}` : "Fiche du muscle"}>
      <MuscleVisibilityPanel
        muscles={allMuscles}
        selected={muscle}
        showAllMuscles={showAllMuscles}
        hiddenMuscleIds={hiddenMuscleIds}
        onShowAll={onShowAllMuscles}
        onHiddenChange={onHiddenChange}
      />
      {showChains ? (
        <ChainDetails
          activeChainIds={activeChainIds}
          chainSide={chainSide}
          onSideChange={onChainSideChange}
        />
      ) : null}
      {muscle ? (
        <>
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
        </>
      ) : (
        <>
          <p className="panel-empty-kicker">Aucun muscle sélectionné</p>
          <h2 className="panel-empty-title">
            {showAllMuscles ? "Tous les muscles" : "Squelette seulement"}
          </h2>
          <p className="panel-empty-body">
            Cliquez un muscle dans la scène, ou recherchez-le, pour la fiche (origines,
            insertions, mouvements). Cochez « Afficher tous les muscles » pour le jeu complet.
          </p>
        </>
      )}
    </aside>
  );
}
