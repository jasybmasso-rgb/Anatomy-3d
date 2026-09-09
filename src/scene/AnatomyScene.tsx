import { ContactShadows } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import type { Muscle } from "../types/muscle";
import { CameraRig, DEFAULT_EYE } from "./CameraRig";
import { FLOOR_Y } from "./landmarks";
import { MuscleMesh } from "./MuscleMesh";
import { Skeleton } from "./Skeleton";

function Lights() {
  return (
    <>
      <ambientLight intensity={0.35} />
      <hemisphereLight args={["#c5d4e8", "#3a2c22", 0.7]} />
      <directionalLight
        position={[2.4, 3.2, 2.2]}
        intensity={1.35}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <directionalLight position={[-2.2, 1.4, -1.2]} intensity={0.28} />
    </>
  );
}

export function AnatomyScene({ muscle }: { muscle: Muscle | null }) {
  return (
    <Canvas
      shadows
      camera={{ position: DEFAULT_EYE, fov: 38, near: 0.05, far: 40 }}
      gl={{ antialias: true }}
    >
      <color attach="background" args={["#0c1118"]} />
      <fog attach="fog" args={["#0c1118", 7, 16]} />
      <Lights />
      <Skeleton />
      {muscle ? <MuscleMesh muscle={muscle} /> : null}
      <ContactShadows position={[0, FLOOR_Y + 0.002, 0]} opacity={0.45} scale={4} blur={2.2} far={2} />
      <CameraRig muscle={muscle} />
    </Canvas>
  );
}
