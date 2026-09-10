import { useState } from "react";
import { LayerMenu, DEFAULT_LAYERS, type LayerId, type LayerState } from "./components/LayerMenu";
import { SceneErrorBoundary } from "./components/SceneErrorBoundary";
import { SearchBar } from "./components/SearchBar";
import { SidePanel } from "./components/SidePanel";
import { muscles, getMuscleById } from "./data/loadMuscles";
import { AnatomyScene } from "./scene/AnatomyScene";
import type { SelectionState } from "./types/muscle";
import "./App.css";

export function App() {
  const [selection, setSelection] = useState<SelectionState>({ selectedMuscleId: null });
  const [resetToken, setResetToken] = useState(0);
  const [layers, setLayers] = useState<LayerState>(DEFAULT_LAYERS);
  const selected = getMuscleById(selection.selectedMuscleId);

  function reset() {
    setSelection({ selectedMuscleId: null });
    setResetToken((token) => token + 1);
  }

  function setLayer(id: LayerId, value: boolean) {
    setLayers((prev) => ({ ...prev, [id]: value }));
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <p className="brand-mark">Anatomy-3d</p>
          <p className="brand-sub">Phase 1 — squelette et couches</p>
        </div>
        <SearchBar
          muscles={muscles}
          selectedId={selection.selectedMuscleId}
          resetToken={resetToken}
          onSelect={(id) => setSelection({ selectedMuscleId: id })}
        />
        <LayerMenu layers={layers} onChange={setLayer} />
        <button type="button" className="reset-btn" onClick={reset}>
          Réinitialiser
        </button>
      </header>
      <div className="workspace">
        <div className="viewport" aria-label="Scène anatomique 3D">
          <SceneErrorBoundary>
            <AnatomyScene
              muscle={selected}
              showMuscles={layers.muscles}
              showLandmarks={layers.landmarks}
              showLigaments={layers.ligaments}
              showFascia={layers.fascias}
              resetToken={resetToken}
            />
          </SceneErrorBoundary>
          {!selected ? (
            <p className="viewport-hint">
              Molette : zoom fluide vers le curseur · Clic droit : panoramique · Double-clic : recentrer
            </p>
          ) : null}
        </div>
        <SidePanel muscle={selected} />
      </div>
    </div>
  );
}
