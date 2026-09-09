import { ContactShadows } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import type { Muscle } from "../types/muscle";
import { CameraRig, DEFAULT_EYE } from "./CameraRig";
import { FLOOR_Y } from "./landmarks";
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
      <ambientLight intensity={0.62} />
      <hemisphereLight args={["#d7e4f5", "#4a3b30", 1.05]} />
      <directionalLight
        position={[2.4, 3.2, 2.2]}
        intensity={1.55}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <directionalLight position={[-2.2, 1.4, -1.2]} intensity={0.45} />
    </>
  );
}

export function AnatomyScene({ muscle }: { muscle: Muscle | null }) {
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
      <Skeleton />
      {muscle ? <MuscleMesh muscle={muscle} /> : null}
      <ContactShadows position={[0, FLOOR_Y + 0.002, 0]} opacity={0.38} scale={4} blur={2.2} far={2} />
      <CameraRig muscle={muscle} />
    </Canvas>
  );
}