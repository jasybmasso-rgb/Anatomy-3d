import type { ChainSide } from "../data/chains";
import type { Muscle } from "../types/muscle";
import type { StructureKind, VisceraPart } from "../types/structure";
import { ChainDetails } from "./ChainPicker";
import { MuscleVisibilityPanel } from "./MuscleVisibilityPanel";
import { muscles as allMuscles } from "../data/loadMuscles";

const REGION_LABEL: Record<string, string> = {
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

const KIND_KICKER: Record<Exclude<StructureKind, "muscle">, string> = {
  nerve: "Nerf",
  organ: "Organe",
  vessel: "Vaisseau sanguin",
};

type SidePanelProps = {
  muscle: Muscle | null;
  viscera: VisceraPart | null;
  kind: StructureKind | null;
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
  viscera,
  kind,
  showAllMuscles,
  hiddenMuscleIds,
  onShowAllMuscles,
  onHiddenChange,
  showChains,
  activeChainIds,
  chainSide,
  onChainSideChange,
}: SidePanelProps) {
  const title = muscle?.name ?? viscera?.name;
  return (
    <aside className="panel" aria-label={title ? `Fiche : ${title}` : "Fiche anatomique"}>
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
      ) : viscera && kind && kind !== "muscle" ? (
        <>
          <p className="panel-kicker">
            {KIND_KICKER[kind]}
            {viscera.region ? ` · ${REGION_LABEL[viscera.region] ?? viscera.region}` : null}
          </p>
          <h2 className="panel-title">{viscera.name}</h2>
          <p className="panel-latin">{viscera.nameLatin}</p>
          <dl className="panel-dl">
            {viscera.vesselKind ? (
              <div>
                <dt>Type</dt>
                <dd>{viscera.vesselKind === "vein" ? "Veine" : "Artère"}</dd>
              </div>
            ) : null}
            <div>
              <dt>Notes</dt>
              <dd>{viscera.notes}</dd>
            </div>
          </dl>
          {viscera.source.startsWith("synthetic") ? (
            <p className="panel-mesh-note">
              Schéma pédagogique : BodyParts3D 4.0 n’a pas ce maillage.
            </p>
          ) : (
            <p className="panel-mesh-note">Maillage BodyParts3D, CC BY-SA 2.1 Japon.</p>
          )}
        </>
      ) : (
        <>
          <p className="panel-empty-kicker">Aucune structure sélectionnée</p>
          <h2 className="panel-empty-title">
            {showAllMuscles ? "Tous les muscles" : "Squelette seulement"}
          </h2>
          <p className="panel-empty-body">
            Cliquez une structure dans la scène, ou recherchez-la (muscle, nerf, organe, vaisseau).
            Activez les couches Nerfs, Organes ou Vaisseaux sanguins dans Couches.
          </p>
        </>
      )}
    </aside>
  );
}
