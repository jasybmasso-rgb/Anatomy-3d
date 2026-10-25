import { ContactShadows } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { lazy, Suspense, useCallback, useMemo, useRef, useState } from "react";
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
  const [canvasEpoch, setCanvasEpoch] = useState(0);
  const [contextLost, setContextLost] = useState(false);
  const onLost = useCallback(() => setContextLost(true), []);
  const onRestored = useCallback(() => {
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

  if (contextLost) {
    return (
      <div className="scene-error" role="alert">
        <p className="scene-error-kicker">WebGL interrompu</p>
        <h2>Le contexte graphique a été perdu</h2>
        <p>
          L’affichage 3D s’est interrompu (souvent sur Chromebook ou Android). La scène se
          rétablira automatiquement ; sinon rechargez la page.
        </p>
      </div>
    );
  }

  return (
    <Canvas
      key={canvasEpoch}
      className="anatomy-canvas"
      shadows={profile.shadows}
      style={{ width: "100%", height: "100%", display: "block", touchAction: "none" }}
      camera={{ position: DEFAULT_EYE, fov: 38, near: 0.05, far: 40 }}
      gl={{
        antialias: profile.antialias,
        alpha: false,
        localClippingEnabled: true,
        powerPreference: profile.lowEnd ? "default" : "high-performance",
        failIfMajorPerformanceCaveat: false,
      }}
      dpr={profile.dpr}
      onCreated={({ gl }) => {
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
      <CameraRig focus={focus} resetToken={resetToken} />
    </Canvas>
  );
}
