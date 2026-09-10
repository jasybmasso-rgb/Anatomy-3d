import { useMemo } from "react";
import * as THREE from "three";
import type { Muscle } from "../types/muscle";
import { primitivesForMuscle, type CapsulePrim, type MusclePrim } from "./muscleMeshes";
import type { Vec3 } from "./landmarks";

const MUSCLE_COLOR = "#c44536";

function CapsuleMesh({ prim }: { prim: CapsulePrim }) {
  const { mid, quat, cyl, radius } = useMemo(() => {
    const start = new THREE.Vector3(...prim.from);
    const end = new THREE.Vector3(...prim.to);
    const dir = end.clone().sub(start);
    const length = dir.length();
    const mid = start.clone().add(end).multiplyScalar(0.5);
    const quat = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      dir.clone().normalize(),
    );
    return {
      mid,
      quat,
      cyl: Math.max(0.002, length - prim.radius * 2),
      radius: prim.radius,
    };
  }, [prim]);

  return (
    <mesh position={mid} quaternion={quat} castShadow userData={{ pick: "muscle" }}>
      <capsuleGeometry args={[radius, cyl, 6, 12]} />
      <meshPhysicalMaterial
        color={MUSCLE_COLOR}
        roughness={0.38}
        metalness={0.04}
        transparent
        opacity={0.9}
        clearcoat={0.15}
      />
    </mesh>
  );
}

function BoxMesh({
  position,
  rotation,
  size,
}: {
  position: Vec3;
  rotation: Vec3;
  size: Vec3;
}) {
  return (
    <mesh position={position} rotation={rotation} castShadow userData={{ pick: "muscle" }}>
      <boxGeometry args={size} />
      <meshPhysicalMaterial
        color={MUSCLE_COLOR}
        roughness={0.38}
        metalness={0.04}
        transparent
        opacity={0.9}
        clearcoat={0.15}
      />
    </mesh>
  );
}

function Primitive({ prim }: { prim: MusclePrim }) {
  if (prim.kind === "capsule") return <CapsuleMesh prim={prim} />;
  return <BoxMesh position={prim.position} rotation={prim.rotation} size={prim.size} />;
}

export function MuscleMesh({ muscle }: { muscle: Muscle }) {
  const prims = useMemo(() => primitivesForMuscle(muscle), [muscle]);
  return (
    <group>
      {prims.map((prim, index) => (
        <Primitive key={`${muscle.id}-${index}`} prim={prim} />
      ))}
    </group>
  );
}
