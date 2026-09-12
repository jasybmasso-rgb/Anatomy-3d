import { useState } from "react";
import { LayerMenu, DEFAULT_LAYERS, type LayerId, type LayerState } from "./components/LayerMenu";
import { ChainLegend } from "./components/ChainPicker";
import { SceneErrorBoundary } from "./components/SceneErrorBoundary";
import { SearchBar } from "./components/SearchBar";
import { SidePanel } from "./components/SidePanel";
import { muscleIdsForChains, type ChainSide } from "./data/chains";
import { connective, getConnectiveById } from "./data/loadConnective";
import { muscles, getMuscleById } from "./data/loadMuscles";
import { nerves, organs, vessels, getVisceraById } from "./data/loadViscera";
import { AnatomyScene } from "./scene/AnatomyScene";
import { applyImmediateHighlight, clearImmediateHighlight } from "./scene/selectionHighlight";
import type { StructureKind, SelectionState, HiddenMap } from "./types/structure";
import { EMPTY_HIDDEN } from "./types/structure";
import "./App.css";

const ALL_VISCERA = [...nerves, ...organs, ...vessels];

function toggleHidden(prev: HiddenMap, kind: StructureKind, id: string, hide: boolean): HiddenMap {
  const next = new Set(prev[kind]);
  if (hide) next.add(id);
  else next.delete(id);
  return { ...prev, [kind]: [...next] };
}

export function App() {
  const [selection, setSelection] = useState<SelectionState>(null);
  const [resetToken, setResetToken] = useState(0);
  const [layers, setLayers] = useState<LayerState>(DEFAULT_LAYERS);
  const [showAllMuscles, setShowAllMuscles] = useState(false);
  const [hiddenIds, setHiddenIds] = useState<HiddenMap>(EMPTY_HIDDEN);
  const [activeChainIds, setActiveChainIds] = useState<string[]>([]);
  const [chainSide, setChainSide] = useState<ChainSide>("both");
  const [pinnedMuscleId, setPinnedMuscleId] = useState<string | null>(null);

  const selectedMuscle =
    selection?.kind === "muscle" ? getMuscleById(selection.id) : null;
  const selectedViscera =
    selection && (selection.kind === "nerve" || selection.kind === "organ" || selection.kind === "vessel")
      ? getVisceraById(selection.kind, selection.id)
      : null;
  const selectedConnective =
    selection && (selection.kind === "ligament" || selection.kind === "fascia")
      ? getConnectiveById(selection.kind, selection.id)
      : null;
  const focus = selectedMuscle ?? selectedViscera ?? selectedConnective;

  function reset() {
    clearImmediateHighlight();
    setSelection(null);
    setResetToken((token) => token + 1);
    setShowAllMuscles(false);
    setHiddenIds(EMPTY_HIDDEN);
    setActiveChainIds([]);
    setChainSide("both");
    setLayers(DEFAULT_LAYERS);
    setPinnedMuscleId(null);
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
    applyImmediateHighlight(kind, id);
    setSelection({ kind, id });
    if (kind === "muscle") {
      setPinnedMuscleId(id);
      setLayers((prev) => ({ ...prev, muscles: true }));
    }
    if (kind === "nerve") setLayers((prev) => ({ ...prev, nerves: true }));
    if (kind === "organ") setLayers((prev) => ({ ...prev, organs: true }));
    if (kind === "vessel") setLayers((prev) => ({ ...prev, vessels: true }));
    if (kind === "ligament") setLayers((prev) => ({ ...prev, ligaments: true }));
    if (kind === "fascia") setLayers((prev) => ({ ...prev, fascias: true }));
  }

  function onActiveChainsChange(ids: string[]) {
    setActiveChainIds(ids);
    if (ids.length > 0) {
      setLayers((prev) => ({ ...prev, chains: true }));
      const ensure = new Set(muscleIdsForChains(ids));
      setHiddenIds((prev) => ({
        ...prev,
        muscle: prev.muscle.filter((id) => !ensure.has(id)),
      }));
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
          connective={connective}
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
              pinnedMuscleId={pinnedMuscleId}
              hiddenIds={hiddenIds}
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
          connective={selectedConnective}
          kind={selection?.kind ?? null}
          showAllMuscles={showAllMuscles}
          hiddenIds={hiddenIds}
          onShowAllMuscles={onShowAllMuscles}
          onHiddenChange={(kind, id, hide) => setHiddenIds((prev) => toggleHidden(prev, kind, id, hide))}
          showChains={layers.chains}
          activeChainIds={activeChainIds}
          chainSide={chainSide}
          onChainSideChange={setChainSide}
        />
      </div>
    </div>
  );
}
