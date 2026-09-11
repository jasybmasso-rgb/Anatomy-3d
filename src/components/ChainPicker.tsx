import { chains, chainsDisclaimer, type ChainSide, type MyofascialChain } from "../data/chains";

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

export function ChainDetails({
  activeChainIds,
  chainSide,
  onSideChange,
}: {
  activeChainIds: string[];
  chainSide: ChainSide;
  onSideChange: (side: ChainSide) => void;
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
      <ul className="chain-detail-list">
        {selected.map((chain) => (
          <li key={chain.id}>
            <p className="chain-detail-title">
              <span className="chain-dot" style={{ background: chain.tint }} />
              {chain.sigle} — {chain.name.fr}
            </p>
            <p className="chain-detail-en">{chain.name.en}</p>
            <p className="chain-detail-body">{chain.description.fr}</p>
            {(chain.fasciaIds?.length ?? 0) > 0 ? (
              <p className="chain-detail-fascia">
                Fascias : {chain.fasciaIds!.length} structure{chain.fasciaIds!.length > 1 ? "s" : ""}{" "}
                (approximation pédagogique Myers).
              </p>
            ) : null}
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
