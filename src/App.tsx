import { useState } from "react";
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
  const [showLandmarks, setShowLandmarks] = useState(false);
  const [showLigaments, setShowLigaments] = useState(false);
  const [showFascia, setShowFascia] = useState(false);
  const selected = getMuscleById(selection.selectedMuscleId);

  function reset() {
    setSelection({ selectedMuscleId: null });
    setResetToken((token) => token + 1);
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <p className="brand-mark">Anatomy-3d</p>
          <p className="brand-sub">Phase 1 — squelette et muscles</p>
        </div>
        <SearchBar
          muscles={muscles}
          selectedId={selection.selectedMuscleId}
          resetToken={resetToken}
          onSelect={(id) => setSelection({ selectedMuscleId: id })}
        />
        <label className="landmarks-toggle ligaments-toggle">
          <input
            type="checkbox"
            checked={showLigaments}
            onChange={(event) => setShowLigaments(event.target.checked)}
          />
          Afficher les ligaments
        </label>
        <label className="landmarks-toggle fascia-toggle">
          <input
            type="checkbox"
            checked={showFascia}
            onChange={(event) => setShowFascia(event.target.checked)}
          />
          Afficher les fascias
        </label>
        <label className="landmarks-toggle">
          <input
            type="checkbox"
            checked={showLandmarks}
            onChange={(event) => setShowLandmarks(event.target.checked)}
          />
          Afficher les repères
        </label>
        <button type="button" className="reset-btn" onClick={reset}>
          Réinitialiser
        </button>
      </header>
      <div className="workspace">
        <div className="viewport" aria-label="Scène anatomique 3D">
          <SceneErrorBoundary>
            <AnatomyScene
              muscle={selected}
              showLandmarks={showLandmarks}
              showLigaments={showLigaments}
              showFascia={showFascia}
              resetToken={resetToken}
            />
          </SceneErrorBoundary>
          {!selected ? (
            <p className="viewport-hint">
              Molette : zoom vers le curseur · Clic droit : panoramique · Double-clic : recentrer
            </p>
          ) : null}
        </div>
        <SidePanel muscle={selected} />
      </div>
    </div>
  );
}
