import { useEffect, useId, useRef, useState } from "react";

export type LayerId =
  | "muscles"
  | "fascias"
  | "ligaments"
  | "landmarks"
  | "nerves"
  | "chains"
  | "vessels";

export type LayerState = Record<LayerId, boolean>;

export const DEFAULT_LAYERS: LayerState = {
  muscles: true,
  fascias: false,
  ligaments: false,
  landmarks: false,
  nerves: false,
  chains: false,
  vessels: false,
};

type LayerMeta = {
  id: LayerId;
  label: string;
  ready: boolean;
  hint?: string;
};

const LAYERS: LayerMeta[] = [
  { id: "muscles", label: "Muscles", ready: true },
  { id: "fascias", label: "Fascias", ready: true },
  { id: "ligaments", label: "Ligaments", ready: true },
  { id: "landmarks", label: "Repères osseux", ready: true },
  { id: "nerves", label: "Nerfs", ready: false, hint: "bientôt" },
  { id: "chains", label: "Chaînes myofaciales", ready: false, hint: "bientôt" },
  { id: "vessels", label: "Vaisseaux / organes", ready: false, hint: "bientôt" },
];

type LayerMenuProps = {
  layers: LayerState;
  onChange: (id: LayerId, value: boolean) => void;
};

export function LayerMenu({ layers, onChange }: LayerMenuProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  useEffect(() => {
    function onDoc(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  const active = LAYERS.filter((layer) => layer.ready && layers[layer.id]).length;

  return (
    <div className="layer-menu" ref={rootRef}>
      <button
        type="button"
        className="layer-menu-btn"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((value) => !value)}
      >
        Couches
        <span className="layer-menu-count">{active}</span>
      </button>
      {open ? (
        <div className="layer-menu-panel" id={menuId} role="group" aria-label="Couches anatomiques">
          <p className="layer-menu-note">Le squelette reste toujours visible. Sélection fine : à venir.</p>
          <ul className="layer-menu-list">
            {LAYERS.map((layer) => (
              <li key={layer.id}>
                <label className={layer.ready ? "layer-menu-item" : "layer-menu-item layer-menu-item-soon"}>
                  <input
                    type="checkbox"
                    checked={layer.ready ? layers[layer.id] : false}
                    disabled={!layer.ready}
                    onChange={(event) => onChange(layer.id, event.target.checked)}
                  />
                  <span>{layer.label}</span>
                  {layer.hint ? <em>{layer.hint}</em> : null}
                </label>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
