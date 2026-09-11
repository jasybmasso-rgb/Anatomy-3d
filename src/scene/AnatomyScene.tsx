import { ContactShadows } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Suspense } from "react";
import type { ChainSide } from "../data/chains";
import { nerves, organs, vessels } from "../data/loadViscera";
import type { Muscle } from "../types/muscle";
import type { FocusTarget, HiddenMap, StructureKind } from "../types/structure";
import { LandmarkLayer } from "./LandmarkLayer";
import { CameraRig, DEFAULT_EYE } from "./CameraRig";
import { Fascia } from "./Fascia";
import { FLOOR_Y } from "./landmarks";
import { Ligaments } from "./Ligaments";
import { MuscleLayer } from "./MuscleLayer";
import { Skeleton } from "./Skeleton";
import { StructurePick } from "./structurePick";
import { VisceraLayer } from "./VisceraLayer";

const SCENE_BG = "#121a24";

function supportsWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

function Lights() {
  return (
    <>
      <ambientLight intensity={0.78} />
      <hemisphereLight args={["#e8f0fa", "#5a4a3c", 1.15]} />
      <directionalLight
        position={[2.4, 3.2, 2.2]}
        intensity={1.75}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <directionalLight position={[-2.2, 1.4, -1.2]} intensity={0.45} />
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
  resetToken,
  onSelectStructure,
}: AnatomySceneProps) {
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

  return (
    <Canvas
      className="anatomy-canvas"
      shadows
      style={{ width: "100%", height: "100%", display: "block", touchAction: "none" }}
      camera={{ position: DEFAULT_EYE, fov: 38, near: 0.05, far: 40 }}
      gl={{ antialias: true, alpha: false, localClippingEnabled: true }}
      dpr={[1, 2]}
    >
      <color attach="background" args={[SCENE_BG]} />
      <fog attach="fog" args={[SCENE_BG, 8, 18]} />
      <Lights />
      <Suspense fallback={null}>
        <Skeleton />
        <Fascia
          layerVisible={showFascia}
          selectedId={selectedKind === "fascia" ? selectedId : null}
          hiddenIds={hiddenIds.fascia}
          chainLayerOn={showChains}
          activeChainIds={activeChainIds}
          chainSide={chainSide}
        />
        <Ligaments
          visible={showLigaments}
          selectedId={selectedKind === "ligament" ? selectedId : null}
          hiddenIds={hiddenIds.ligament}
        />
        <VisceraLayer
          url="/models/organs.glb"
          parts={organs}
          kind="organ"
          visible={showOrgans}
          selectedId={selectedKind === "organ" ? selectedId : null}
          hiddenIds={hiddenIds.organ}
        />
        <VisceraLayer
          url="/models/vessels.glb"
          parts={vessels}
          kind="vessel"
          visible={showVessels}
          selectedId={selectedKind === "vessel" ? selectedId : null}
          hiddenIds={hiddenIds.vessel}
        />
        <VisceraLayer
          url="/models/nerves.glb"
          parts={nerves}
          kind="nerve"
          visible={showNerves}
          selectedId={selectedKind === "nerve" ? selectedId : null}
          hiddenIds={hiddenIds.nerve}
        />
        <MuscleLayer
          selectedMuscleId={muscle?.id ?? null}
          showMuscles={showMuscles}
          showAllMuscles={showAllMuscles}
          hiddenMuscleIds={hiddenIds.muscle}
          chainLayerOn={showChains}
          activeChainIds={activeChainIds}
          chainSide={chainSide}
        />
        <LandmarkLayer visible={showLandmarks} />
        <StructurePick onSelect={onSelectStructure} />
      </Suspense>
      <ContactShadows position={[0, FLOOR_Y + 0.002, 0]} opacity={0.38} scale={4} blur={2.2} far={2} />
      <CameraRig focus={focus} resetToken={resetToken} />
    </Canvas>
  );
}
