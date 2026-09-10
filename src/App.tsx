import { useState } from "react";
import { LayerMenu, DEFAULT_LAYERS, type LayerId, type LayerState } from "./components/LayerMenu";
import { ChainLegend } from "./components/ChainPicker";
import { SceneErrorBoundary } from "./components/SceneErrorBoundary";
import { SearchBar } from "./components/SearchBar";
import { SidePanel } from "./components/SidePanel";
import { muscleIdsForChains } from "./data/chains";
import { muscles, getMuscleById } from "./data/loadMuscles";
import { AnatomyScene } from "./scene/AnatomyScene";
import type { SelectionState } from "./types/muscle";
import "./App.css";

export function App() {
  const [selection, setSelection] = useState<SelectionState>({ selectedMuscleId: null });
  const [resetToken, setResetToken] = useState(0);
  const [layers, setLayers] = useState<LayerState>(DEFAULT_LAYERS);
  const [showAllMuscles, setShowAllMuscles] = useState(false);
  const [hiddenMuscleIds, setHiddenMuscleIds] = useState<string[]>([]);
  const [activeChainIds, setActiveChainIds] = useState<string[]>([]);
  const selected = getMuscleById(selection.selectedMuscleId);

  function reset() {
    setSelection({ selectedMuscleId: null });
    setResetToken((token) => token + 1);
    setShowAllMuscles(false);
    setHiddenMuscleIds([]);
    setActiveChainIds([]);
    setLayers(DEFAULT_LAYERS);
  }

  function setLayer(id: LayerId, value: boolean) {
    setLayers((prev) => ({ ...prev, [id]: value }));
    if (id === "muscles" && value === false) setShowAllMuscles(false);
  }

  function onShowAllMuscles(value: boolean) {
    setShowAllMuscles(value);
    if (value) setLayers((prev) => ({ ...prev, muscles: true }));
  }

  function onActiveChainsChange(ids: string[]) {
    setActiveChainIds(ids);
    if (ids.length > 0) {
      setLayers((prev) => ({ ...prev, chains: true }));
      const ensure = new Set(muscleIdsForChains(ids));
      setHiddenMuscleIds((prev) => prev.filter((id) => !ensure.has(id)));
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <p className="brand-mark">Anatomy-3d</p>
          <p className="brand-sub">Squelette, muscles et chaînes myofaciales</p>
        </div>
        <SearchBar
          muscles={muscles}
          selectedId={selection.selectedMuscleId}
          resetToken={resetToken}
          onSelect={(id) => setSelection({ selectedMuscleId: id })}
        />
        <LayerMenu
          layers={layers}
          onChange={setLayer}
          showAllMuscles={showAllMuscles}
          onShowAllMuscles={onShowAllMuscles}
          activeChainIds={activeChainIds}
          onActiveChainsChange={onActiveChainsChange}
        />
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
              showAllMuscles={showAllMuscles}
              hiddenMuscleIds={hiddenMuscleIds}
              showLandmarks={layers.landmarks}
              showLigaments={layers.ligaments}
              showFascia={layers.fascias}
              showChains={layers.chains}
              activeChainIds={activeChainIds}
              resetToken={resetToken}
            />
          </SceneErrorBoundary>
          <ChainLegend activeChainIds={layers.chains ? activeChainIds : []} />
          {!selected ? (
            <p className="viewport-hint">
              Molette : zoom fluide vers le curseur · Clic droit : panoramique · Double-clic : recentrer
            </p>
          ) : null}
        </div>
        <SidePanel
          muscle={selected}
          showAllMuscles={showAllMuscles}
          hiddenMuscleIds={hiddenMuscleIds}
          onShowAllMuscles={onShowAllMuscles}
          onHiddenChange={setHiddenMuscleIds}
          showChains={layers.chains}
          activeChainIds={activeChainIds}
        />
      </div>
    </div>
  );
}
