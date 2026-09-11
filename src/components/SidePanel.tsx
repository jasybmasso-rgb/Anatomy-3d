import type { ChainSide } from "../data/chains";
import { connective as allConnective } from "../data/loadConnective";
import { muscles as allMuscles } from "../data/loadMuscles";
import { nerves, organs, vessels } from "../data/loadViscera";
import type { Muscle } from "../types/muscle";
import type {
  ConnectivePart,
  HiddenMap,
  StructureKind,
  VisceraPart,
} from "../types/structure";
import { STRUCTURE_KIND_LABEL } from "../types/structure";
import { ChainDetails } from "./ChainPicker";
import { MuscleVisibilityPanel } from "./MuscleVisibilityPanel";

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
  cuisse: "Cuisse",
  bassin: "Bassin",
  rachis: "Rachis",
  crâne: "Crâne",
  "ceinture-scapulaire": "Ceinture scapulaire",
  thorax: "Thorax",
};

type SidePanelProps = {
  muscle: Muscle | null;
  viscera: VisceraPart | null;
  connective: ConnectivePart | null;
  kind: StructureKind | null;
  showAllMuscles: boolean;
  hiddenIds: HiddenMap;
  onShowAllMuscles: (value: boolean) => void;
  onHiddenChange: (kind: StructureKind, id: string, hide: boolean) => void;
  showChains: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
  onChainSideChange: (side: ChainSide) => void;
};

export function SidePanel({
  muscle,
  viscera,
  connective,
  kind,
  showAllMuscles,
  hiddenIds,
  onShowAllMuscles,
  onHiddenChange,
  showChains,
  activeChainIds,
  chainSide,
  onChainSideChange,
}: SidePanelProps) {
  const title = muscle?.name ?? viscera?.name ?? connective?.name;
  const selectedId = muscle?.id ?? viscera?.id ?? connective?.id ?? null;
  return (
    <aside className="panel" aria-label={title ? `Fiche : ${title}` : "Fiche anatomique"}>
      <MuscleVisibilityPanel
        muscles={allMuscles}
        viscera={[...nerves, ...organs, ...vessels]}
        connective={allConnective}
        selectedKind={kind}
        selectedId={selectedId}
        selectedName={title ?? null}
        showAllMuscles={showAllMuscles}
        hiddenIds={hiddenIds}
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
      ) : viscera && kind && (kind === "nerve" || kind === "organ" || kind === "vessel") ? (
        <>
          <p className="panel-kicker">
            {STRUCTURE_KIND_LABEL[kind]}
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
      ) : connective && kind && (kind === "ligament" || kind === "fascia") ? (
        <>
          <p className="panel-kicker">
            {STRUCTURE_KIND_LABEL[kind]}
            {connective.region ? ` · ${REGION_LABEL[connective.region] ?? connective.region}` : null}
          </p>
          <h2 className="panel-title">{connective.name}</h2>
          <p className="panel-latin">{connective.nameLatin}</p>
          <dl className="panel-dl">
            {connective.joint ? (
              <div>
                <dt>Articulation</dt>
                <dd>{connective.joint}</dd>
              </div>
            ) : null}
            <div>
              <dt>Notes</dt>
              <dd>{connective.notes}</dd>
            </div>
          </dl>
          {connective.source.startsWith("synthetic") ? (
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
            Cliquez une structure dans la scène, ou recherchez-la (muscle, ligament, fascia, nerf,
            organe, vaisseau). Activez la couche correspondante dans Couches. Un second clic au même
            endroit cycle les pièces superposées.
          </p>
        </>
      )}
    </aside>
  );
}
