import { ContactShadows } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { ChainSide } from "../data/chains";
import type { Muscle } from "../types/muscle";
import type { FocusTarget, HiddenMap, StructureKind } from "../types/structure";
import { LandmarkLayer } from "./LandmarkLayer";
import { CameraRig, DEFAULT_EYE } from "./CameraRig";
import { getDeviceProfile } from "./deviceProfile";
import { FLOOR_Y } from "./landmarks";
import type { ModelSource } from "./modelSource";
import { StructurePick } from "./structurePick";
import { attachWebglGuard } from "./webglGuard";

const ZAnatomyBody = lazy(() => import("./ZAnatomyBody"));
const ProceduralBody = lazy(() => import("./ProceduralBody"));

const SCENE_BG = "#121a24";

function gpuReadoutEnabled(): boolean {
  if (typeof window === "undefined") return false;
  if (new URLSearchParams(window.location.search).get("gpu") === "1") return true;
  try {
    return localStorage.getItem("anatomy3d.gpu") === "1";
  } catch {
    return false;
  }
}

function useGpuToggle() {
  const [on, setOn] = useState(gpuReadoutEnabled);
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (!event.altKey || !event.shiftKey || event.code !== "KeyG") return;
      event.preventDefault();
      setOn((value) => {
        const next = !value;
        try {
          localStorage.setItem("anatomy3d.gpu", next ? "1" : "0");
        } catch {
          /* ignore */
        }
        return next;
      });
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  return on;
}

/** renderer.info plus a CPU-side buffer estimate. Hidden unless ?gpu=1 or Alt+Shift+G. */
function GpuReadout({ enabled }: { enabled: boolean }) {
  const gl = useThree((state) => state.gl);
  const scene = useThree((state) => state.scene);
  const acc = useRef(0);
  useFrame((_, dt) => {
    if (!enabled) return;
    acc.current += dt;
    if (acc.current < 0.5) return;
    acc.current = 0;
    const el = document.getElementById("gpu-readout");
    if (!el) return;
    const info = gl.info;
    let bytes = 0;
    const seen = new Set<THREE.BufferGeometry>();
    scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh || !mesh.geometry || seen.has(mesh.geometry)) return;
      seen.add(mesh.geometry);
      const geo = mesh.geometry;
      for (const attr of Object.values(geo.attributes)) {
        const array = (attr as THREE.BufferAttribute).array;
        if (array) bytes += array.byteLength;
      }
      if (geo.index?.array) bytes += geo.index.array.byteLength;
    });
    const px = gl.getPixelRatio();
    el.textContent = [
      `triangles ${info.render.triangles.toLocaleString("fr-CA")}`,
      `appels ${info.render.calls.toLocaleString("fr-CA")}`,
      `géométries ${info.memory.geometries.toLocaleString("fr-CA")}`,
      `textures ${info.memory.textures.toLocaleString("fr-CA")}`,
      `tampons ${(bytes / 1e6).toFixed(1)} Mo`,
      `pixels ${px.toFixed(2)}×`,
    ].join("\n");
  });
  return null;
}

function FpsProbe() {
  const on = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("fps") === "1";
  const acc = useRef({ n: 0, t: 0 });
  useFrame((_, dt) => {
    if (!on) return;
    acc.current.n += 1;
    acc.current.t += dt;
    if (acc.current.t < 0.5) return;
    const fps = acc.current.n / acc.current.t;
    acc.current.n = 0;
    acc.current.t = 0;
    const el = document.getElementById("fps-probe");
    if (el) el.dataset.fps = fps.toFixed(1);
  });
  return null;
}

function supportsWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

function Lights({ shadows, shadowMap }: { shadows: boolean; shadowMap: number }) {
  return (
    <>
      <ambientLight intensity={0.58} />
      <hemisphereLight args={["#e8f0fa", "#5a4a3c", 0.92]} />
      <directionalLight
        position={[2.4, 3.2, 2.2]}
        intensity={1.32}
        castShadow={shadows}
        shadow-mapSize-width={shadowMap}
        shadow-mapSize-height={shadowMap}
      />
      <directionalLight position={[-2.2, 1.4, -1.2]} intensity={0.36} />
    </>
  );
}

type AnatomySceneProps = {
  muscle: Muscle | null;
  focus: FocusTarget | null;
  selectedKind: StructureKind | null;
  selectedId: string | null;
  showMuscles: boolean;
  showAllMuscles: boolean;
  pinnedMuscleId: string | null;
  hiddenIds: HiddenMap;
  showLandmarks: boolean;
  showLigaments: boolean;
  showFascia: boolean;
  showNerves: boolean;
  showOrgans: boolean;
  showVessels: boolean;
  showChains: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
  modelSource: ModelSource;
  resetToken: number;
  onSelectStructure: (kind: StructureKind, id: string) => void;
};

export function AnatomyScene({
  muscle,
  focus,
  selectedKind,
  selectedId,
  showMuscles,
  showAllMuscles,
  pinnedMuscleId,
  hiddenIds,
  showLandmarks,
  showLigaments,
  showFascia,
  showNerves,
  showOrgans,
  showVessels,
  showChains,
  activeChainIds,
  chainSide,
  modelSource,
  resetToken,
  onSelectStructure,
}: AnatomySceneProps) {
  const profile = useMemo(() => getDeviceProfile(), []);
  const gpu = useGpuToggle();
  const [canvasEpoch, setCanvasEpoch] = useState(0);
  const [contextLost, setContextLost] = useState(false);
  const onLost = useCallback(() => setContextLost(true), []);
  const onRestored = useCallback(() => setContextLost(false), []);
  const retryContext = useCallback(() => {
    setContextLost(false);
    setCanvasEpoch((n) => n + 1);
  }, []);

  if (typeof window !== "undefined" && !supportsWebGL()) {
    return (
      <div className="scene-error" role="alert">
        <p className="scene-error-kicker">WebGL indisponible</p>
        <h2>Impossible d’afficher la scène 3D</h2>
        <p>
          Ce navigateur n’expose pas WebGL. Activez l’accélération graphique ou ouvrez l’application
          dans un autre navigateur, puis rechargez la page.
        </p>
      </div>
    );
  }

  const pixelCap = profile.dpr[1];

  return (
    <div className="anatomy-stage">
    {contextLost ? (
      <div className="scene-error scene-error-overlay" role="alert">
        <p className="scene-error-kicker">WebGL interrompu</p>
        <h2>Le contexte graphique a été perdu</h2>
        <p>
          L’affichage 3D s’est interrompu, souvent parce que la mémoire graphique est pleine.
          La scène se rétablit automatiquement, sans recharger la page.
        </p>
        <button type="button" className="reset-btn" onClick={retryContext}>
          Réessayer
        </button>
      </div>
    ) : null}
    {gpu ? (
      <pre id="gpu-readout" className="gpu-readout" aria-label="Mémoire graphique" />
    ) : null}
    <Canvas
      key={canvasEpoch}
      className="anatomy-canvas"
      shadows={profile.shadows}
      style={{ width: "100%", height: "100%", display: "block", touchAction: "none" }}
      camera={{ position: DEFAULT_EYE, fov: 38, near: 0.04, far: 24 }}
      gl={{
        antialias: profile.antialias,
        alpha: false,
        localClippingEnabled: true,
        powerPreference: profile.lowEnd ? "default" : "high-performance",
        failIfMajorPerformanceCaveat: false,
      }}
      dpr={profile.dpr}
      onCreated={({ gl }) => {
        gl.setPixelRatio(Math.min(window.devicePixelRatio || 1, pixelCap));
        attachWebglGuard(gl.domElement, onLost, onRestored);
      }}
    >
      <color attach="background" args={[SCENE_BG]} />
      <fog attach="fog" args={[SCENE_BG, 8, 18]} />
      <Lights shadows={profile.shadows} shadowMap={profile.shadowMap} />
      <Suspense fallback={null}>
        {modelSource === "zanatomy" ? (
          <ZAnatomyBody
            showMuscles={showMuscles}
            showAllMuscles={showAllMuscles}
            pinnedMuscleId={pinnedMuscleId}
            hiddenMuscleIds={hiddenIds.muscle}
            hiddenFasciaIds={hiddenIds.fascia}
            hiddenLigamentIds={hiddenIds.ligament}
            hiddenNerveIds={hiddenIds.nerve}
            hiddenOrganIds={hiddenIds.organ}
            hiddenVesselIds={hiddenIds.vessel}
            hiddenBoneIds={hiddenIds.bone}
            showLigaments={showLigaments}
            showFascia={showFascia}
            showNerves={showNerves}
            showOrgans={showOrgans}
            showVessels={showVessels}
            showChains={showChains}
            activeChainIds={activeChainIds}
            chainSide={chainSide}
            selectedId={selectedId}
          />
        ) : (
          <ProceduralBody
            showMuscles={showMuscles}
            showAllMuscles={showAllMuscles}
            pinnedMuscleId={pinnedMuscleId}
            selectedMuscleId={muscle?.id ?? null}
            hiddenMuscleIds={hiddenIds.muscle}
            hiddenFasciaIds={hiddenIds.fascia}
            hiddenLigamentIds={hiddenIds.ligament}
            hiddenNerveIds={hiddenIds.nerve}
            hiddenOrganIds={hiddenIds.organ}
            hiddenVesselIds={hiddenIds.vessel}
            showLigaments={showLigaments}
            showFascia={showFascia}
            showNerves={showNerves}
            showOrgans={showOrgans}
            showVessels={showVessels}
            showChains={showChains}
            activeChainIds={activeChainIds}
            chainSide={chainSide}
            selectedKind={selectedKind}
            selectedId={selectedId}
          />
        )}
        <LandmarkLayer visible={showLandmarks} />
        <StructurePick onSelect={onSelectStructure} />
      </Suspense>
      {profile.contactShadows ? (
        <ContactShadows position={[0, FLOOR_Y + 0.002, 0]} opacity={0.38} scale={4} blur={2.2} far={2} />
      ) : null}
      <FpsProbe />
      <GpuReadout enabled={gpu} />
      <CameraRig focus={focus} resetToken={resetToken} />
    </Canvas>
    </div>
  );
}
