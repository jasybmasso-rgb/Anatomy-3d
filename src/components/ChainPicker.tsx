import { chains, chainsDisclaimer, type ChainSide, type MyofascialChain } from "../data/chains";
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

const GROUP_LABEL: Record<MyofascialChain["group"], string> = {
  principal: "Lignes principales",
  bras: "Lignes du bras",
  fonctionnelle: "Lignes fonctionnelles",
};

const SIDE_LABEL: { id: ChainSide; label: string }[] = [
  { id: "both", label: "Bilatéral" },
  { id: "left", label: "Gauche seulement" },
  { id: "right", label: "Droite seulement" },
];

type ChainPickerProps = {
  activeChainIds: string[];
  onChange: (ids: string[]) => void;
  chainSide: ChainSide;
  onSideChange: (side: ChainSide) => void;
  compact?: boolean;
};

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
  activeChainIds,
  onChange,
  chainSide,
  onSideChange,
  compact = false,
}: ChainPickerProps) {
  const active = new Set(activeChainIds);
  const groups: MyofascialChain["group"][] = ["principal", "bras", "fonctionnelle"];

  function toggle(id: string, value: boolean) {
    const next = new Set(active);
    if (value) next.add(id);
    else next.delete(id);
    onChange([...next]);
  }

  return (
    <div className={compact ? "chain-picker chain-picker-compact" : "chain-picker"}>
      {activeChainIds.length > 0 ? (
        <ChainSideControl chainSide={chainSide} onSideChange={onSideChange} compact={compact} />
      ) : null}
      {activeChainIds.includes("spl") && chainSide !== "both" ? (
        <p className="chain-disclaimer">
          SPL unilatérale : latéralité croisée (hélice de Myers), pas un filtre gauche/droite
          simple.
        </p>
      ) : null}
      {(activeChainIds.includes("ffl") || activeChainIds.includes("bfl")) && chainSide !== "both" ? (
        <p className="chain-disclaimer">
          FFL et BFL unilatérales : le segment inférieur est controlatéral (X de Myers). L’IFL ne
          croise pas.
        </p>
      ) : null}
      {groups.map((group) => (
        <div key={group} className="chain-group">
          {compact ? null : <p className="chain-group-label">{GROUP_LABEL[group]}</p>}
          <ul className="chain-list">
            {chains
              .filter((chain) => chain.group === group)
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
                      {compact ? null : <span className="chain-name">{chain.name.fr}</span>}
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
  selectedKind,
  selectedId,
  onSelect,
}: {
  chain: MyofascialChain;
  chainSide: ChainSide;
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
          const target = stationTarget(station, chainSide);
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
  activeChainIds,
  chainSide,
  onSideChange,
  selectedKind,
  selectedId,
  onSelect,
}: {
  activeChainIds: string[];
  chainSide: ChainSide;
  onSideChange: (side: ChainSide) => void;
  selectedKind: StructureKind | null;
  selectedId: string | null;
  onSelect: (kind: StructureKind, id: string) => void;
}) {
  const selected = chains.filter((chain) => activeChainIds.includes(chain.id));
  if (selected.length === 0) {
    return (
      <section className="chain-details" aria-label="Chaînes myofaciales">
        <p className="panel-kicker">Chaînes myofaciales</p>
        <p className="chain-disclaimer">{chainsDisclaimer.fr}</p>
        <p className="panel-empty-body">Cochez une ou plusieurs lignes dans Couches.</p>
      </section>
    );
  }
  return (
    <section className="chain-details" aria-label="Chaînes actives">
      <p className="panel-kicker">Chaînes myofaciales</p>
      <p className="chain-disclaimer">{chainsDisclaimer.fr}</p>
      <ChainSideControl chainSide={chainSide} onSideChange={onSideChange} />
      {activeChainIds.includes("spl") && chainSide !== "both" ? (
        <p className="chain-disclaimer">
          SPL unilatérale : latéralité croisée (hélice de Myers), pas un filtre gauche/droite
          simple.
        </p>
      ) : null}
      {(activeChainIds.includes("ffl") || activeChainIds.includes("bfl")) && chainSide !== "both" ? (
        <p className="chain-disclaimer">
          FFL et BFL unilatérales : le segment inférieur est controlatéral (X de Myers). L’IFL ne
          croise pas.
        </p>
      ) : null}
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
              selectedKind={selectedKind}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          </li>
        ))}
      </ul>
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
