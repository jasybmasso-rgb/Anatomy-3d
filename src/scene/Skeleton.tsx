import { useMemo } from "react";
import * as THREE from "three";
import { FLOOR_Y, LANDMARKS, type Vec3 } from "./landmarks";

const BONE = "#e4d6c0";
const BONE_DEEP = "#c9b7a0";

function Bone({
  a,
  b,
  radius = 0.026,
  color = BONE,
}: {
  a: Vec3;
  b: Vec3;
  radius?: number;
  color?: string;
}) {
  const { mid, quat, cyl } = useMemo(() => {
    const start = new THREE.Vector3(...a);
    const end = new THREE.Vector3(...b);
    const dir = end.clone().sub(start);
    const length = dir.length();
    const mid = start.clone().add(end).multiplyScalar(0.5);
    const quat = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      dir.clone().normalize(),
    );
    return { mid, quat, cyl: Math.max(0.002, length - radius * 2) };
  }, [a, b, radius]);

  return (
    <mesh position={mid} quaternion={quat} castShadow>
      <capsuleGeometry args={[radius, cyl, 5, 10]} />
      <meshStandardMaterial color={color} roughness={0.48} metalness={0.06} />
    </mesh>
  );
}

function Joint({ at, radius = 0.03 }: { at: Vec3; radius?: number }) {
  return (
    <mesh position={at} castShadow>
      <sphereGeometry args={[radius, 16, 12]} />
      <meshStandardMaterial color={BONE} roughness={0.5} metalness={0.05} />
    </mesh>
  );
}

export function Skeleton() {
  const L = LANDMARKS;

  return (
    <group>
      {/* Crâne */}
      <mesh position={L.skull} scale={[0.9, 1.08, 1.05]} castShadow>
        <sphereGeometry args={[0.105, 24, 18]} />
        <meshStandardMaterial color={BONE} roughness={0.5} metalness={0.04} />
      </mesh>
      <mesh position={[0, 0.56, 0.04]} scale={[0.72, 0.35, 0.55]} castShadow>
        <sphereGeometry args={[0.08, 16, 12]} />
        <meshStandardMaterial color={BONE_DEEP} roughness={0.55} metalness={0.04} />
      </mesh>

      {/* Colonne */}
      <Bone a={[0, -0.02, -0.02]} b={L.c7} radius={0.028} color={BONE_DEEP} />
      <Bone a={L.c7} b={[0, 0.6, 0.0]} radius={0.02} />

      {/* Cage thoracique */}
      <mesh position={[0, 0.3, 0.02]} rotation={[0.12, 0, 0]} scale={[1.15, 1.28, 0.72]} castShadow>
        <sphereGeometry args={[0.155, 22, 16]} />
        <meshStandardMaterial
          color={BONE}
          roughness={0.46}
          metalness={0.05}
          transparent
          opacity={0.92}
        />
      </mesh>
      <Bone a={[0, 0.46, 0.06]} b={L.xiphoid} radius={0.016} />

      {/* Clavicules */}
      <Bone a={[-0.02, 0.47, 0.06]} b={L.rAcromion} radius={0.016} />
      <Bone a={[0.02, 0.47, 0.06]} b={L.lAcromion} radius={0.016} />

      {/* Scapulas */}
      <mesh position={L.rScapula} rotation={[0.4, 0.5, -0.2]} castShadow>
        <boxGeometry args={[0.1, 0.14, 0.018]} />
        <meshStandardMaterial color={BONE} roughness={0.5} metalness={0.05} />
      </mesh>
      <mesh position={L.lScapula} rotation={[0.4, -0.5, 0.2]} castShadow>
        <boxGeometry args={[0.1, 0.14, 0.018]} />
        <meshStandardMaterial color={BONE} roughness={0.5} metalness={0.05} />
      </mesh>

      {/* Bassin */}
      <mesh position={[0, -0.02, 0]} rotation={[Math.PI / 2, 0, 0]} scale={[1, 0.72, 1]} castShadow>
        <torusGeometry args={[0.1, 0.032, 10, 22]} />
        <meshStandardMaterial color={BONE} roughness={0.48} metalness={0.05} />
      </mesh>
      <Bone a={[-0.08, -0.01, 0.02]} b={[0.08, -0.01, 0.02]} radius={0.02} />
      <mesh position={[0, -0.08, 0.03]} castShadow>
        <boxGeometry args={[0.08, 0.04, 0.05]} />
        <meshStandardMaterial color={BONE_DEEP} roughness={0.5} metalness={0.04} />
      </mesh>

      {/* Membres supérieurs */}
      <Bone a={L.rAcromion} b={L.rElbow} radius={0.024} />
      <Bone a={L.lAcromion} b={L.lElbow} radius={0.024} />
      <Bone a={L.rElbow} b={L.rWrist} radius={0.018} />
      <Bone a={L.lElbow} b={L.lWrist} radius={0.018} />
      <mesh position={[-0.22, -0.16, 0.04]} castShadow>
        <boxGeometry args={[0.05, 0.09, 0.03]} />
        <meshStandardMaterial color={BONE} roughness={0.5} metalness={0.04} />
      </mesh>
      <mesh position={[0.22, -0.16, 0.04]} castShadow>
        <boxGeometry args={[0.05, 0.09, 0.03]} />
        <meshStandardMaterial color={BONE} roughness={0.5} metalness={0.04} />
      </mesh>

      {/* Membres inférieurs */}
      <Bone a={L.rHip} b={L.rKnee} radius={0.03} />
      <Bone a={L.lHip} b={L.lKnee} radius={0.03} />
      <Bone a={L.rKnee} b={L.rAnkle} radius={0.022} />
      <Bone a={L.lKnee} b={L.lAnkle} radius={0.022} />
      <mesh position={L.rFoot} rotation={[0.15, 0, 0]} castShadow>
        <boxGeometry args={[0.055, 0.04, 0.16]} />
        <meshStandardMaterial color={BONE} roughness={0.5} metalness={0.04} />
      </mesh>
      <mesh position={L.lFoot} rotation={[0.15, 0, 0]} castShadow>
        <boxGeometry args={[0.055, 0.04, 0.16]} />
        <meshStandardMaterial color={BONE} roughness={0.5} metalness={0.04} />
      </mesh>

      <Joint at={L.rAcromion} radius={0.032} />
      <Joint at={L.lAcromion} radius={0.032} />
      <Joint at={L.rElbow} radius={0.026} />
      <Joint at={L.lElbow} radius={0.026} />
      <Joint at={L.rHip} radius={0.036} />
      <Joint at={L.lHip} radius={0.036} />
      <Joint at={L.rKnee} radius={0.032} />
      <Joint at={L.lKnee} radius={0.032} />
      <Joint at={L.rAnkle} radius={0.022} />
      <Joint at={L.lAnkle} radius={0.022} />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, FLOOR_Y, 0]} receiveShadow>
        <circleGeometry args={[1.8, 48]} />
        <meshStandardMaterial color="#151c27" roughness={1} metalness={0} />
      </mesh>
    </group>
  );
}
