import { useState } from "react";
import { CreditsDialog } from "./components/CreditsDialog";
import { IosInstallHint } from "./components/IosInstallHint";
import { FullscreenToggle } from "./components/FullscreenToggle";
import { LayerMenu, DEFAULT_LAYERS, type LayerId, type LayerState } from "./components/LayerMenu";
import { loadModelSource, saveModelSource, type ModelSource } from "./scene/modelSource";
import { getZaById, zaExtraParts } from "./data/zanatomy";
import { ChainLegend } from "./components/ChainPicker";
import { SceneErrorBoundary } from "./components/SceneErrorBoundary";
import { SearchBar } from "./components/SearchBar";
import { SidePanel } from "./components/SidePanel";
import { getChainById, muscleIdsForChains, type ChainSide } from "./data/chains";
import {
  isChainSchool,
  loadChainSchool,
  saveChainSchool,
  type ChainSchoolId,
} from "./data/chainSchools";
import { connective, getConnectiveById } from "./data/loadConnective";
import { muscles, getMuscleById } from "./data/loadMuscles";
import { nerves, organs, vessels, getVisceraById } from "./data/loadViscera";
import { useCompactLayout, useLayoutMode } from "./lib/useLayoutMode";
import { AnatomyScene } from "./scene/AnatomyScene";
import { applyImmediateHighlight, clearImmediateHighlight } from "./scene/selectionHighlight";
import type { StructureKind, SelectionState, HiddenMap } from "./types/structure";
import { EMPTY_HIDDEN } from "./types/structure";
import "./App.css";

const ALL_VISCERA = [...nerves, ...organs, ...vessels];

function initialLayers(): LayerState {
  if (typeof window === "undefined") return DEFAULT_LAYERS;
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("layers");
  const next: LayerState = raw ? { ...DEFAULT_LAYERS, muscles: false } : { ...DEFAULT_LAYERS };
  if (raw) {
    for (const id of raw.split(",")) {
      if (id in next) next[id as LayerId] = true;
    }
  }
  if (params.get("chain")) next.chains = true;
  return next;
}

function initialSchool(): ChainSchoolId {
  if (typeof window === "undefined") return "myers";
  const query = new URLSearchParams(window.location.search).get("school");
  if (isChainSchool(query)) return query;
  return loadChainSchool();
}

function initialChains(school: ChainSchoolId): string[] {
  if (typeof window === "undefined") return [];
  const raw = new URLSearchParams(window.location.search).get("chain");
  if (!raw) return [];
  return raw.split(",").filter((id) => getChainById(id)?.school === school);
}

function initialShowAll(): boolean {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).get("all") === "1";
}

function toggleHidden(prev: HiddenMap, kind: StructureKind, id: string, hide: boolean): HiddenMap {
  const next = new Set(prev[kind]);
  if (hide) next.add(id);
  else next.delete(id);
  return { ...prev, [kind]: [...next] };
}

export function App() {
  const [selection, setSelection] = useState<SelectionState>(null);
  const [resetToken, setResetToken] = useState(0);
  const [layers, setLayers] = useState<LayerState>(initialLayers);
  const [showAllMuscles, setShowAllMuscles] = useState(initialShowAll);
  const [hiddenIds, setHiddenIds] = useState<HiddenMap>(EMPTY_HIDDEN);
  const [chainSchool, setChainSchool] = useState<ChainSchoolId>(initialSchool);
  const [activeChainIds, setActiveChainIds] = useState<string[]>(() => initialChains(initialSchool()));
  const [chainSide, setChainSide] = useState<ChainSide>("both");
  const [pinnedMuscleId, setPinnedMuscleId] = useState<string | null>(null);
  const [modelSource, setModelSource] = useState<ModelSource>(loadModelSource);
  const [creditsOpen, setCreditsOpen] = useState(false);
  const compact = useCompactLayout();
  const { mode: layoutMode, exit: exitLayout, toggle: toggleLayout } = useLayoutMode();
  const showFicheFullscreen = compact || layoutMode === "fiche";

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
  const selectedZa =
    modelSource === "zanatomy" && selection ? getZaById(selection.id) : null;
  const catalogFocus = selectedMuscle ?? selectedViscera ?? selectedConnective ?? selectedZa;
  const focus =
    selectedZa && catalogFocus
      ? { ...catalogFocus, id: selectedZa.id, region: selectedZa.region, focus: selectedZa.focus }
      : catalogFocus;

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
    exitLayout();
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

  function onModelSourceChange(source: ModelSource) {
    setModelSource(source);
    saveModelSource(source);
    clearImmediateHighlight();
    setSelection(null);
  }

  function onChainSchoolChange(school: ChainSchoolId) {
    setChainSchool(school);
    saveChainSchool(school);
    setActiveChainIds([]);
    setChainSide("both");
    clearImmediateHighlight();
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
    <div className="app" data-layout={layoutMode}>
      <header className="topbar">
        <div className="brand">
          <p className="brand-mark">Anatomy-3d</p>
          <p className="brand-sub">Squelette, muscles, nerfs, organes et circulation</p>
          <button type="button" className="credits-link" onClick={() => setCreditsOpen(true)}>
            Crédits
          </button>
        </div>
        <SearchBar
          muscles={muscles}
          viscera={modelSource === "zanatomy" ? [] : ALL_VISCERA}
          connective={modelSource === "zanatomy" ? [] : connective}
          extra={modelSource === "zanatomy" ? zaExtraParts : []}
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
          chainSchool={chainSchool}
          onChainSchoolChange={onChainSchoolChange}
          activeChainIds={activeChainIds}
          onActiveChainsChange={onActiveChainsChange}
          chainSide={chainSide}
          onChainSideChange={setChainSide}
          modelSource={modelSource}
          onModelSourceChange={onModelSourceChange}
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
              modelSource={modelSource}
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
          <FullscreenToggle
            className="fs-btn-viewport"
            active={layoutMode === "viewport"}
            onToggle={() => toggleLayout("viewport")}
          />
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
          chainSchool={chainSchool}
          activeChainIds={activeChainIds}
          chainSide={chainSide}
          onChainSideChange={setChainSide}
          ficheFullscreen={layoutMode === "fiche"}
          showFicheFullscreen={showFicheFullscreen}
          onToggleFicheFullscreen={() => toggleLayout("fiche")}
          modelSource={modelSource}
          zaPart={selectedZa}
          onSelectStructure={onSelectStructure}
        />
      </div>
      <IosInstallHint />
      <CreditsDialog open={creditsOpen} onClose={() => setCreditsOpen(false)} />
      {typeof window !== "undefined" && new URLSearchParams(window.location.search).get("fps") === "1" ? (
        <div id="fps-probe" data-fps="" hidden />
      ) : null}
    </div>
  );
}
