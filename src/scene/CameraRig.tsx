import { OrbitControls } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import type { Muscle } from "../types/muscle";
import { toLandmarkFocus } from "./landmarks";

export const DEFAULT_EYE: [number, number, number] = [1.55, 0.22, 2.35];
export const DEFAULT_TARGET: [number, number, number] = [0, -0.05, 0];

function goalsFor(muscle: Muscle | null): { eye: THREE.Vector3; target: THREE.Vector3 } {
  if (!muscle) {
    return {
      eye: new THREE.Vector3(...DEFAULT_EYE),
      target: new THREE.Vector3(...DEFAULT_TARGET),
    };
  }
  const [tx, ty, tz] = toLandmarkFocus(muscle.focus.position);
  const d = THREE.MathUtils.clamp(muscle.focus.distance, 0.45, 2.4);
  return {
    target: new THREE.Vector3(tx, ty, tz),
    eye: new THREE.Vector3(tx + d * 0.42, ty + d * 0.18, tz + d * 0.88),
  };
}

export function CameraRig({ muscle }: { muscle: Muscle | null }) {
  const controls = useRef<OrbitControlsImpl>(null);
  const { camera } = useThree();
  const goalEye = useRef(new THREE.Vector3(...DEFAULT_EYE));
  const goalTarget = useRef(new THREE.Vector3(...DEFAULT_TARGET));
  const animating = useRef(true);

  useEffect(() => {
    const next = goalsFor(muscle);
    goalEye.current.copy(next.eye);
    goalTarget.current.copy(next.target);
    animating.current = true;
  }, [muscle]);

  useFrame((_, dt) => {
    const orbit = controls.current;
    if (!orbit || !animating.current) return;
    const k = 1 - Math.exp(-5 * dt);
    camera.position.lerp(goalEye.current, k);
    orbit.target.lerp(goalTarget.current, k);
    orbit.update();
    if (
      camera.position.distanceTo(goalEye.current) < 0.012 &&
      orbit.target.distanceTo(goalTarget.current) < 0.012
    ) {
      animating.current = false;
    }
  });

  return (
    <OrbitControls
      ref={controls}
      makeDefault
      enableDamping
      dampingFactor={0.08}
      minDistance={0.35}
      maxDistance={6}
      target={DEFAULT_TARGET}
      onStart={() => {
        animating.current = false;
      }}
    />
  );
}