import { OrbitControls } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import type { Muscle } from "../types/muscle";
import { toLandmarkFocus } from "./landmarks";
import { registerOrbitFocus } from "./orbitFocus";

export const DEFAULT_EYE: [number, number, number] = [1.55, 0.22, 2.35];
export const DEFAULT_TARGET: [number, number, number] = [0, -0.05, 0];

const MIN_DISTANCE = 0.08;
const MAX_DISTANCE = 8;
const ZOOM_STEP = 0.18;
const PICK_LAYERS = new Set(["bone", "ligament", "landmark", "muscle"]);

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

function isPickableMesh(obj: THREE.Object3D): obj is THREE.Mesh {
  return obj instanceof THREE.Mesh && PICK_LAYERS.has(String(obj.userData.pick ?? ""));
}

function pickPoint(
  raycaster: THREE.Raycaster,
  pointer: THREE.Vector2,
  camera: THREE.Camera,
  scene: THREE.Scene,
): THREE.Vector3 | null {
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(scene.children, true);
  for (const hit of hits) {
    if (isPickableMesh(hit.object) && hit.point) {
      return hit.point.clone();
    }
  }
  return null;
}

function pointerFromEvent(event: MouseEvent, element: HTMLElement, out: THREE.Vector2) {
  const rect = element.getBoundingClientRect();
  const w = Math.max(rect.width, 1);
  const h = Math.max(rect.height, 1);
  out.set(((event.clientX - rect.left) / w) * 2 - 1, -((event.clientY - rect.top) / h) * 2 + 1);
}

export function CameraRig({
  muscle,
  resetToken,
}: {
  muscle: Muscle | null;
  resetToken: number;
}) {
  const controls = useRef<OrbitControlsImpl>(null);
  const { camera, gl, scene } = useThree();
  const goalEye = useRef(new THREE.Vector3(...DEFAULT_EYE));
  const goalTarget = useRef(new THREE.Vector3(...DEFAULT_TARGET));
  const animating = useRef(true);
  const raycaster = useRef(new THREE.Raycaster());
  const pointer = useRef(new THREE.Vector2());

  function stopAnimation() {
    animating.current = false;
  }

  function applyFocus(point: THREE.Vector3, smooth = true) {
    const orbit = controls.current;
    if (!orbit) return;
    const currentTarget = orbit.target.clone();
    const offset = camera.position.clone().sub(currentTarget);
    const dist = THREE.MathUtils.clamp(offset.length(), MIN_DISTANCE, MAX_DISTANCE);
    const dir = offset.lengthSq() > 1e-8 ? offset.normalize() : new THREE.Vector3(0.42, 0.18, 0.88).normalize();
    goalTarget.current.copy(point);
    goalEye.current.copy(point).addScaledVector(dir, dist);
    if (smooth) {
      animating.current = true;
    } else {
      camera.position.copy(goalEye.current);
      orbit.target.copy(point);
      orbit.update();
      animating.current = false;
    }
  }

  useEffect(() => {
    registerOrbitFocus((point, options) => {
      applyFocus(point, options?.smooth !== false);
    });
    return () => registerOrbitFocus(null);
  });

  useEffect(() => {
    const next = goalsFor(muscle);
    goalEye.current.copy(next.eye);
    goalTarget.current.copy(next.target);
    animating.current = true;
  }, [muscle, resetToken]);

  useEffect(() => {
    const element = gl.domElement;

    const onWheel = (event: WheelEvent) => {
      const orbit = controls.current;
      if (!orbit || !orbit.enabled) return;
      event.preventDefault();
      stopAnimation();

      pointerFromEvent(event, element, pointer.current);
      const hit = pickPoint(raycaster.current, pointer.current, camera, scene);
      const factor = Math.exp(Math.sign(event.deltaY) * ZOOM_STEP);
      let pivot: THREE.Vector3;
      if (hit) {
        pivot = hit;
      } else {
        raycaster.current.setFromCamera(pointer.current, camera);
        const depth = Math.max(camera.position.distanceTo(orbit.target), MIN_DISTANCE);
        pivot = raycaster.current.ray.origin
          .clone()
          .addScaledVector(raycaster.current.ray.direction, depth);
      }
      const offset = camera.position.clone().sub(pivot);
      const nextDist = THREE.MathUtils.clamp(offset.length() * factor, MIN_DISTANCE, MAX_DISTANCE);
      if (offset.lengthSq() < 1e-10) return;
      camera.position.copy(pivot).addScaledVector(offset.normalize(), nextDist);
      orbit.target.copy(pivot);
      orbit.update();
    };

    const onDblClick = (event: MouseEvent) => {
      const orbit = controls.current;
      if (!orbit) return;
      pointerFromEvent(event, element, pointer.current);
      const hit = pickPoint(raycaster.current, pointer.current, camera, scene);
      if (hit) applyFocus(hit, true);
    };

    element.addEventListener("wheel", onWheel, { passive: false });
    element.addEventListener("dblclick", onDblClick);
    return () => {
      element.removeEventListener("wheel", onWheel);
      element.removeEventListener("dblclick", onDblClick);
    };
  }, [camera, gl, scene]);

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
      enableZoom={false}
      screenSpacePanning
      minDistance={MIN_DISTANCE}
      maxDistance={MAX_DISTANCE}
      onStart={stopAnimation}
    />
  );
}
