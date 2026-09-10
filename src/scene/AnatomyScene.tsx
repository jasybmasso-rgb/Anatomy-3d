import { ContactShadows } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Suspense } from "react";
import type { Muscle } from "../types/muscle";
import { LandmarkLayer } from "./LandmarkLayer";
import { CameraRig, DEFAULT_EYE } from "./CameraRig";
import { FLOOR_Y } from "./landmarks";
import { Ligaments } from "./Ligaments";
import { MuscleMesh } from "./MuscleMesh";
import { Skeleton } from "./Skeleton";

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
  showLandmarks: boolean;
  showLigaments: boolean;
  resetToken: number;
};

export function AnatomyScene({
  muscle,
  showLandmarks,
  showLigaments,
  resetToken,
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
      style={{ width: "100%", height: "100%", display: "block" }}
      camera={{ position: DEFAULT_EYE, fov: 38, near: 0.05, far: 40 }}
      gl={{ antialias: true, alpha: false }}
      dpr={[1, 2]}
    >
      <color attach="background" args={[SCENE_BG]} />
      <fog attach="fog" args={[SCENE_BG, 8, 18]} />
      <Lights />
      <Suspense fallback={null}>
        <Skeleton />
        <Ligaments visible={showLigaments} />
        {muscle ? <MuscleMesh muscle={muscle} /> : null}
        <LandmarkLayer visible={showLandmarks} />
      </Suspense>
      <ContactShadows position={[0, FLOOR_Y + 0.002, 0]} opacity={0.38} scale={4} blur={2.2} far={2} />
      <CameraRig muscle={muscle} resetToken={resetToken} />
    </Canvas>
  );
}
