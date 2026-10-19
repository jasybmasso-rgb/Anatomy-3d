import { useEffect, useMemo, useRef, useState } from "react";
import type * as THREE from "three";
import { disposeGroup, loadSystem } from "./loadModels";
import { OriginalScene } from "./OriginalScene";
import { asFrame, type CameraFrame, type OriginalManifest } from "./types";

const FALLBACK_HOME: CameraFrame = {
  eye: [0.35, 1.05, 2.85],
  target: [0, 0.9, 0.02],
};

function initialEnabled(manifest: OriginalManifest): Record<string, boolean> {
  const forced = new URLSearchParams(window.location.search).get("systemes");
  const allow = forced
    ? new Set(
        forced
          .split(",")
          .map((id) => id.trim())
          .filter(Boolean),
      )
    : null;
  const enabled: Record<string, boolean> = {};
  for (const system of manifest.systems) {
    enabled[system.id] = allow ? allow.has(system.id) : system.defaultOn;
  }
  return enabled;
}

function formatMio(bytes: number): string {
  return `${(bytes / (1024 * 1024)).toLocaleString("fr-CA", { maximumFractionDigits: 1 })} Mo`;
}

export function OriginalApp() {
  const [manifest, setManifest] = useState<OriginalManifest | null>(null);
  const [enabled, setEnabled] = useState<Record<string, boolean>>({});
  const [groups, setGroups] = useState<Record<string, THREE.Group>>({});
  const [progress, setProgress] = useState<string | null>("Lecture du manifeste…");
  const [error, setError] = useState<string | null>(null);
  const [picked, setPicked] = useState<string | null>(null);
  const [fps, setFps] = useState(0);
  const [triangles, setTriangles] = useState(0);
  const [contextLost, setContextLost] = useState(false);
  const groupsRef = useRef<Record<string, THREE.Group>>({});
  const enabledRef = useRef(enabled);
  const generation = useRef(0);
  enabledRef.current = enabled;

  useEffect(() => {
    let cancel = false;
    fetch("/models/zanatomy-original/manifest.json")
      .then(async (response) => {
        if (!response.ok) throw new Error(String(response.status));
        return (await response.json()) as OriginalManifest;
      })
      .then((data) => {
        if (cancel) return;
        setManifest(data);
        setEnabled(initialEnabled(data));
        setProgress(null);
      })
      .catch(() => {
        if (cancel) return;
        setProgress(null);
        setError("Le manifeste Z-Anatomy est introuvable.");
      });
    return () => {
      cancel = true;
    };
  }, []);

  useEffect(() => {
    if (!manifest) return;
    const token = ++generation.current;
    const wanted = new Set(
      manifest.systems.filter((system) => enabled[system.id]).map((system) => system.id),
    );
    let dropped = false;
    for (const id of Object.keys(groupsRef.current)) {
      if (wanted.has(id)) continue;
      disposeGroup(groupsRef.current[id]);
      delete groupsRef.current[id];
      dropped = true;
    }
    if (dropped) setGroups({ ...groupsRef.current });

    const missing = manifest.systems.filter(
      (system) => wanted.has(system.id) && !groupsRef.current[system.id],
    );
    if (missing.length === 0) {
      setProgress(null);
      return;
    }

    void (async () => {
      for (const system of missing) {
        if (token !== generation.current || !enabledRef.current[system.id]) return;
        setProgress(`Chargement : ${system.label}…`);
        try {
          const group = await loadSystem(system, (loaded, total) => {
            if (token !== generation.current) return;
            const pct = total > 0 ? Math.min(100, Math.round((loaded / total) * 100)) : 0;
            setProgress(`Chargement : ${system.label}… ${pct} %`);
          });
          if (token !== generation.current || !enabledRef.current[system.id]) {
            disposeGroup(group);
            return;
          }
          groupsRef.current[system.id] = group;
          setGroups({ ...groupsRef.current });
        } catch (err) {
          console.error(err);
          if (token === generation.current) {
            setError(`Échec du chargement (${system.label}).`);
            setProgress(null);
          }
          return;
        }
      }
      if (token === generation.current) setProgress(null);
    })();
  }, [manifest, enabled]);

  useEffect(() => {
    return () => {
      generation.current += 1;
      for (const group of Object.values(groupsRef.current)) disposeGroup(group);
    };
  }, []);

  const home = useMemo(() => {
    if (!manifest) return FALLBACK_HOME;
    const cadre = new URLSearchParams(window.location.search).get("cadre");
    return (
      asFrame(cadre ? manifest.frames[cadre] : undefined) ??
      asFrame(manifest.frames["corps-face"]) ??
      FALLBACK_HOME
    );
  }, [manifest]);

  const visibleGroups = useMemo(
    () =>
      manifest
        ? manifest.systems.flatMap((system) => {
            const group = enabled[system.id] ? groups[system.id] : undefined;
            return group ? [group] : [];
          })
        : [],
    [manifest, enabled, groups],
  );

  const waiting = Boolean(
    manifest && manifest.systems.some((system) => enabled[system.id] && !groups[system.id]),
  );
  const ready = Boolean(manifest) && !error && !waiting && !progress && triangles > 0;

  useEffect(() => {
    document.body.dataset.zaReady = ready ? "1" : "0";
    document.body.dataset.zaTriangles = String(triangles);
    document.body.dataset.zaFps = String(fps);
    document.body.dataset.zaName = picked ?? "";
  }, [ready, triangles, fps, picked]);

  return (
    <div className="za-app" data-za-ready={ready ? "1" : "0"}>
      <header className="za-bar">
        <div className="za-brand">
          <p className="za-title">Z-Anatomy original</p>
          <p className="za-sub">Corps entier, géométrie d’origine, sans décimation</p>
          <a className="za-back" href="/">
            Retour à l’étude
          </a>
        </div>
        <fieldset className="za-systems">
          <legend>Systèmes</legend>
          {manifest ? (
            manifest.systems.map((system) => (
              <label key={system.id} className="za-check">
                <input
                  type="checkbox"
                  checked={Boolean(enabled[system.id])}
                  onChange={(event) =>
                    setEnabled((prev) => ({ ...prev, [system.id]: event.target.checked }))
                  }
                />
                <span>{system.label}</span>
                <span className="za-count">
                  {system.triangles.toLocaleString("fr-CA")} tri. ·{" "}
                  {formatMio(system.files.reduce((sum, file) => sum + file.bytes, 0))}
                </span>
              </label>
            ))
          ) : (
            <p className="za-wait">Chargement de la liste…</p>
          )}
        </fieldset>
        <div className="za-side">
          <p className="za-readout" data-za-readout>
            {triangles.toLocaleString("fr-CA")} triangles · {fps} FPS
          </p>
          <p className="za-name" data-za-structure>
            {picked ? picked : "Cliquez une structure pour son nom"}
          </p>
          {progress ? (
            <p className="za-progress" role="status">
              {progress}
            </p>
          ) : null}
          {error ? (
            <p className="za-error" role="alert">
              {error}
            </p>
          ) : null}
        </div>
      </header>
      <div className="za-viewport" aria-label="Z-Anatomy original">
        {contextLost ? (
          <p className="za-lost" role="alert">
            Le contexte graphique a été perdu. Rechargez la page si la scène ne revient pas.
          </p>
        ) : null}
        <OriginalScene
          groups={visibleGroups}
          home={home}
          onFrame={(nextFps, nextTriangles) => {
            setFps(nextFps);
            setTriangles(nextTriangles);
          }}
          onPick={setPicked}
          onLost={() => setContextLost(true)}
          onRestored={() => setContextLost(false)}
        />
        <p className="za-hint">
          Clic : nom de la structure · Molette / pincement : zoom · Un doigt : orbite · Deux doigts
          : panoramique
        </p>
      </div>
      <footer className="za-credits">
        <p>
          Z-Anatomy — Gauthier Kervyn et Marcin Zielinski, CC BY-SA 4.0, dérivé de BodyParts3D, CC
          BY-SA 2.1 Japon. Compression Draco (positions 16 bits), sans décimation.
          {manifest
            ? ` Total ${manifest.totalTriangles.toLocaleString("fr-CA")} triangles, ${formatMio(manifest.totalBytes)}.`
            : ""}
        </p>
        <p className="za-warn">
          Maillage d’origine, très lourd. Sur un Chromebook, le débit d’images et la mémoire peuvent
          être insuffisants : laissez décochés les systèmes dont vous n’avez pas besoin.
        </p>
      </footer>
    </div>
  );
}
