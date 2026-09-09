import { useState } from "react";
import { SearchBar } from "./components/SearchBar";
import { SidePanel } from "./components/SidePanel";
import { muscles, getMuscleById } from "./data/loadMuscles";
import { AnatomyScene } from "./scene/AnatomyScene";
import type { SelectionState } from "./types/muscle";
import "./App.css";

export function App() {
  const [selection, setSelection] = useState<SelectionState>({ selectedMuscleId: null });
  const [resetToken, setResetToken] = useState(0);
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
        <button type="button" className="reset-btn" onClick={reset}>
          Réinitialiser
        </button>
      </header>
      <div className="workspace">
        <div className="viewport" aria-label="Scène anatomique 3D">
          <AnatomyScene muscle={selected} />
          {!selected ? (
            <p className="viewport-hint">Squelette humain simplifié — recherchez un muscle pour l’afficher</p>
          ) : null}
        </div>
        <SidePanel muscle={selected} />
      </div>
    </div>
  );
}
