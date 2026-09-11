import { useState } from "react";
import { LayerMenu, DEFAULT_LAYERS, type LayerId, type LayerState } from "./components/LayerMenu";
import { ChainLegend } from "./components/ChainPicker";
import { SceneErrorBoundary } from "./components/SceneErrorBoundary";
import { SearchBar } from "./components/SearchBar";
import { SidePanel } from "./components/SidePanel";
import { muscleIdsForChains, type ChainSide } from "./data/chains";
import { muscles, getMuscleById } from "./data/loadMuscles";
import { nerves, organs, vessels, getVisceraById } from "./data/loadViscera";
import { AnatomyScene } from "./scene/AnatomyScene";
import type { SelectionState } from "./types/muscle";
import type { StructureKind } from "./types/structure";
import "./App.css";

const ALL_VISCERA = [...nerves, ...organs, ...vessels];

export function App() {
  const [selection, setSelection] = useState<SelectionState>(null);
  const [resetToken, setResetToken] = useState(0);
  const [layers, setLayers] = useState<LayerState>(DEFAULT_LAYERS);
  const [showAllMuscles, setShowAllMuscles] = useState(false);
  const [hiddenMuscleIds, setHiddenMuscleIds] = useState<string[]>([]);
  const [activeChainIds, setActiveChainIds] = useState<string[]>([]);
  const [chainSide, setChainSide] = useState<ChainSide>("both");

  const selectedMuscle =
    selection?.kind === "muscle" ? getMuscleById(selection.id) : null;
  const selectedViscera =
    selection && selection.kind !== "muscle"
      ? getVisceraById(selection.kind, selection.id)
      : null;
  const focus = selectedMuscle ?? selectedViscera;

  function reset() {
    setSelection(null);
    setResetToken((token) => token + 1);
    setShowAllMuscles(false);
    setHiddenMuscleIds([]);
    setActiveChainIds([]);
    setChainSide("both");
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

  function onSelectStructure(kind: StructureKind, id: string) {
    setSelection({ kind, id });
    if (kind === "muscle") setLayers((prev) => ({ ...prev, muscles: true }));
    if (kind === "nerve") setLayers((prev) => ({ ...prev, nerves: true }));
    if (kind === "organ") setLayers((prev) => ({ ...prev, organs: true }));
    if (kind === "vessel") setLayers((prev) => ({ ...prev, vessels: true }));
  }

  function onActiveChainsChange(ids: string[]) {
    setActiveChainIds(ids);
    if (ids.length > 0) {
      setLayers((prev) => ({ ...prev, chains: true }));
      const ensure = new Set(muscleIdsForChains(ids));
      setHiddenMuscleIds((prev) => prev.filter((id) => !ensure.has(id)));
    } else {
      setChainSide("both");
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <p className="brand-mark">Anatomy-3d</p>
          <p className="brand-sub">Squelette, muscles, nerfs, organes et circulation</p>
        </div>
        <SearchBar
          muscles={muscles}
          viscera={ALL_VISCERA}
          selectedId={selection?.id ?? null}
          selectedKind={selection?.kind ?? null}
          resetToken={resetToken}
          onSelect={onSelectStructure}
        />
        <LayerMenu
          layers={layers}
          onChange={setLayer}
          showAllMuscles={showAllMuscles}
          onShowAllMuscles={onShowAllMuscles}
          activeChainIds={activeChainIds}
          onActiveChainsChange={onActiveChainsChange}
          chainSide={chainSide}
          onChainSideChange={setChainSide}
        />
        <button type="button" className="reset-btn" onClick={reset}>
          Réinitialiser
        </button>
      </header>
      <div className="workspace">
        <div className="viewport" aria-label="Scène anatomique 3D">
          <SceneErrorBoundary>
            <AnatomyScene
              muscle={selectedMuscle}
              focus={focus}
              selectedKind={selection?.kind ?? null}
              selectedId={selection?.id ?? null}
              showMuscles={layers.muscles}
              showAllMuscles={showAllMuscles}
              hiddenMuscleIds={hiddenMuscleIds}
              showLandmarks={layers.landmarks}
              showLigaments={layers.ligaments}
              showFascia={layers.fascias}
              showNerves={layers.nerves}
              showOrgans={layers.organs}
              showVessels={layers.vessels}
              showChains={layers.chains}
              activeChainIds={activeChainIds}
              chainSide={chainSide}
              resetToken={resetToken}
              onSelectStructure={onSelectStructure}
            />
          </SceneErrorBoundary>
          <ChainLegend activeChainIds={layers.chains ? activeChainIds : []} />
          {!focus ? (
            <p className="viewport-hint">
              Clic : sélectionner · Molette / pincement : zoom · Un doigt : orbite · Deux doigts :
              panoramique
            </p>
          ) : null}
        </div>
        <SidePanel
          muscle={selectedMuscle}
          viscera={selectedViscera}
          kind={selection?.kind ?? null}
          showAllMuscles={showAllMuscles}
          hiddenMuscleIds={hiddenMuscleIds}
          onShowAllMuscles={onShowAllMuscles}
          onHiddenChange={setHiddenMuscleIds}
          showChains={layers.chains}
          activeChainIds={activeChainIds}
          chainSide={chainSide}
          onChainSideChange={setChainSide}
        />
      </div>
    </div>
  );
}
