import { chains, type ChainSide, type MyofascialChain } from "../data/chains";
import {
  CHAIN_MODELS_NOTE,
  CHAIN_SCHOOLS,
  getChainSchool,
  type ChainSchoolId,
} from "../data/chainSchools";
import type { ModelSource } from "../scene/modelSource";
import {
  STATION_ROLE_LABEL,
  STATION_SIDE_LABEL,
  stationSide,
  stationTarget,
  trackFor,
  type ChainStation,
} from "../data/chainTracks";
import { getFasciaById } from "../data/loadConnective";
import { getMuscleById } from "../data/loadMuscles";
import type { StructureKind } from "../types/structure";
import { applyImmediateHighlight, clearImmediateHighlight } from "../scene/selectionHighlight";

const SIDE_LABEL: { id: ChainSide; label: string }[] = [
  { id: "both", label: "Bilatéral" },
  { id: "left", label: "Gauche seulement" },
  { id: "right", label: "Droite seulement" },
];

type ChainPickerProps = {
  school: ChainSchoolId;
  onSchoolChange: (school: ChainSchoolId) => void;
  activeChainIds: string[];
  onChange: (ids: string[]) => void;
  chainSide: ChainSide;
  onSideChange: (side: ChainSide) => void;
  compact?: boolean;
};

function lateralityNote(activeChainIds: string[], chainSide: ChainSide): string | null {
  if (chainSide === "both" || activeChainIds.length === 0) return null;
  if (activeChainIds.includes("spl")) {
    return "SPL unilatérale : latéralité croisée (hélice de Myers), pas un filtre gauche/droite simple.";
  }
  if (activeChainIds.includes("ffl") || activeChainIds.includes("bfl")) {
    return "FFL et BFL unilatérales : le segment inférieur est controlatéral (X de Myers). L’IFL ne croise pas.";
  }
  const crosses = activeChainIds.some((id) => trackFor(id)?.stations.some((station) => station.crosses));
  if (!crosses) return null;
  return "Latéralité simple : les stations marquées « croise » sont dessinées du côté opposé, là où la chaîne traverse la ligne médiane.";
}

export function ChainSchoolControl({
  school,
  onSchoolChange,
  compact = false,
}: {
  school: ChainSchoolId;
  onSchoolChange: (school: ChainSchoolId) => void;
  compact?: boolean;
}) {
  const current = getChainSchool(school);
  return (
    <fieldset className={compact ? "chain-school chain-school-compact" : "chain-school"}>
      <legend className="chain-school-label">Modèle de chaînes</legend>
      {CHAIN_SCHOOLS.map((item) => (
        <label key={item.id} className={school === item.id ? "chain-school-opt chain-school-opt-on" : "chain-school-opt"}>
          <input
            type="radio"
            name={compact ? "chain-school-compact" : "chain-school"}
            checked={school === item.id}
            onChange={() => onSchoolChange(item.id)}
          />
          <span>{item.label}</span>
        </label>
      ))}
      <p className="chain-school-blurb">{current.summary}</p>
    </fieldset>
  );
}

export function ChainSideControl({
  chainSide,
  onSideChange,
  compact = false,
}: {
  chainSide: ChainSide;
  onSideChange: (side: ChainSide) => void;
  compact?: boolean;
}) {
  return (
    <fieldset className={compact ? "chain-side chain-side-compact" : "chain-side"}>
      <legend>Latéralité</legend>
      {SIDE_LABEL.map((opt) => (
        <label key={opt.id} className={chainSide === opt.id ? "chain-side-opt chain-side-opt-on" : "chain-side-opt"}>
          <input
            type="radio"
            name={compact ? "chain-side-compact" : "chain-side"}
            checked={chainSide === opt.id}
            onChange={() => onSideChange(opt.id)}
          />
          {opt.label}
        </label>
      ))}
    </fieldset>
  );
}

export function ChainPicker({
  school,
  onSchoolChange,
  activeChainIds,
  onChange,
  chainSide,
  onSideChange,
  compact = false,
}: ChainPickerProps) {
  const active = new Set(activeChainIds);
  const model = getChainSchool(school);
  const visible = chains.filter((chain) => chain.school === school);
  const note = lateralityNote(activeChainIds, chainSide);

  function toggle(id: string, value: boolean) {
    const next = new Set(active);
    if (value) next.add(id);
    else next.delete(id);
    onChange([...visible.filter((chain) => next.has(chain.id)).map((chain) => chain.id)]);
  }

  return (
    <div className={compact ? "chain-picker chain-picker-compact" : "chain-picker"} data-chain-school={school}>
      <ChainSchoolControl school={school} onSchoolChange={onSchoolChange} compact={compact} />
      {activeChainIds.length > 0 ? (
        <ChainSideControl chainSide={chainSide} onSideChange={onSideChange} compact={compact} />
      ) : null}
      {note ? <p className="chain-disclaimer">{note}</p> : null}
      {model.groups.map((group) => (
        <div key={group.id} className="chain-group">
          <p className="chain-group-label">{group.label}</p>
          <ul className="chain-list">
            {visible
              .filter((chain) => chain.group === group.id)
              .map((chain) => {
                const on = active.has(chain.id);
                return (
                  <li key={chain.id}>
                    <label className={on ? "chain-item chain-item-on" : "chain-item"}>
                      <input
                        type="checkbox"
                        checked={on}
                        onChange={(event) => toggle(chain.id, event.target.checked)}
                      />
                      <span className="chain-dot" style={{ background: chain.tint }} />
                      <span className="chain-sigle">{chain.sigle}</span>
                      <span className="chain-name">{chain.name.fr}</span>
                    </label>
                  </li>
                );
              })}
          </ul>
        </div>
      ))}
    </div>
  );
}

function displayName(station: ChainStation): string {
  if (station.role === "muscle" && station.id) {
    return getMuscleById(station.id)?.name ?? station.label;
  }
  const fasciaId = station.id ?? station.leftId ?? station.rightId;
  if (fasciaId && station.pickKind === "fascia") {
    const name = getFasciaById(fasciaId)?.name;
    if (name) return name.replace(/ (droit|droite|gauche)$/i, "");
  }
  return station.label;
}

function ChainStationList({
  chain,
  chainSide,
  modelSource,
  selectedKind,
  selectedId,
  onSelect,
}: {
  chain: MyofascialChain;
  chainSide: ChainSide;
  modelSource: ModelSource;
  selectedKind: StructureKind | null;
  selectedId: string | null;
  onSelect: (kind: StructureKind, id: string) => void;
}) {
  const track = trackFor(chain.id);
  if (!track) return null;
  return (
    <div className="chain-track-wrap">
      <p className="chain-track-dir">{track.direction}</p>
      <ol className="chain-track" aria-label={`Parcours ${chain.sigle}`}>
        {track.stations.map((station, index) => {
          const target = stationTarget(station, chainSide, modelSource);
          const side = stationSide(station, chainSide);
          const on = Boolean(target && selectedKind === target.kind && selectedId === target.id);
          const name = displayName(station);
          const meta = (
            <span className="chain-station-meta">
              <span>{STATION_ROLE_LABEL[station.role]}</span>
              <span>{STATION_SIDE_LABEL[side]}</span>
              {station.crosses ? <span>croise</span> : null}
              {target ? null : <span className="chain-station-note">pas encore modélisé</span>}
            </span>
          );
          if (!target) {
            return (
              <li key={`${station.label}-${index}`}>
                <div className="chain-station chain-station-missing">
                  <span className="chain-station-index">{index + 1}</span>
                  <span>
                    <span className="chain-station-name">{name}</span>
                    {meta}
                  </span>
                </div>
              </li>
            );
          }
          return (
            <li key={`${target.kind}-${target.id}-${index}`}>
              <button
                type="button"
                className={on ? "chain-station chain-station-on" : "chain-station"}
                aria-pressed={on}
                onPointerEnter={(event) => {
                  if (event.pointerType !== "mouse") return;
                  applyImmediateHighlight(target.kind, target.id);
                }}
                onPointerLeave={(event) => {
                  if (event.pointerType !== "mouse") return;
                  if (selectedKind && selectedId) applyImmediateHighlight(selectedKind, selectedId);
                  else clearImmediateHighlight();
                }}
                onClick={() => onSelect(target.kind, target.id)}
              >
                <span className="chain-station-index">{index + 1}</span>
                <span>
                  <span className="chain-station-name">{name}</span>
                  {meta}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export function ChainDetails({
  school,
  activeChainIds,
  chainSide,
  modelSource,
  onSideChange,
  selectedKind,
  selectedId,
  onSelect,
}: {
  school: ChainSchoolId;
  activeChainIds: string[];
  chainSide: ChainSide;
  modelSource: ModelSource;
  onSideChange: (side: ChainSide) => void;
  selectedKind: StructureKind | null;
  selectedId: string | null;
  onSelect: (kind: StructureKind, id: string) => void;
}) {
  const model = getChainSchool(school);
  const selected = chains.filter((chain) => chain.school === school && activeChainIds.includes(chain.id));
  const note = lateralityNote(activeChainIds, chainSide);
  return (
    <section className="chain-details" aria-label="Chaînes myofasciales">
      <p className="panel-kicker">Chaînes myofasciales</p>
      <p className="chain-detail-title">{model.label}</p>
      <p className="chain-detail-body">{model.explanation}</p>
      <p className="chain-disclaimer">{CHAIN_MODELS_NOTE}</p>
      {selected.length === 0 ? (
        <p className="panel-empty-body">Cochez une ou plusieurs chaînes dans Couches. Un seul modèle est affiché à la fois.</p>
      ) : (
        <>
      <ChainSideControl chainSide={chainSide} onSideChange={onSideChange} />
      {note ? <p className="chain-disclaimer">{note}</p> : null}
      <ul className="chain-detail-list">
        {selected.map((chain) => (
          <li key={chain.id}>
            <p className="chain-detail-title">
              <span className="chain-dot" style={{ background: chain.tint }} />
              {chain.sigle} — {chain.name.fr}
            </p>
            <p className="chain-detail-en">{chain.name.en}</p>
            <p className="chain-detail-body">{chain.description.fr}</p>
            <ChainStationList
              chain={chain}
              chainSide={chainSide}
              modelSource={modelSource}
              selectedKind={selectedKind}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          </li>
        ))}
      </ul>
        </>
      )}
    </section>
  );
}

export function ChainLegend({ activeChainIds }: { activeChainIds: string[] }) {
  const selected = chains.filter((chain) => activeChainIds.includes(chain.id));
  if (selected.length === 0) return null;
  return (
    <ul className="chain-legend" aria-label="Légende des chaînes">
      {selected.map((chain) => (
        <li key={chain.id}>
          <span className="chain-dot" style={{ background: chain.tint }} />
          {chain.sigle}
        </li>
      ))}
    </ul>
  );
}
