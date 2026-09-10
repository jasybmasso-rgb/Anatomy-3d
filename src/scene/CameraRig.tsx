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
const ZOOM_PIXEL_SCALE = 0.00135;
const ZOOM_DAMP = 11;
const TARGET_DAMP = 8;
const FOCUS_DAMP = 5;
const GESTURE_MS = 160;
const SKIP_PICK = new Set(["ignore", "floor", "shadow"]);
const SAMPLE_RINGS = [0, 0.07, 0.16, 0.28, 0.42, 0.58];
const SAMPLE_DIRS = 8;
const _ndc = new THREE.Vector2();
const _viewDir = new THREE.Vector3();
const _plane = new THREE.Plane();
const _planeHit = new THREE.Vector3();
const _offset = new THREE.Vector3();

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
  if (!(obj instanceof THREE.Mesh) || !obj.visible) return false;
  if (SKIP_PICK.has(String(obj.userData.pick ?? ""))) return false;
  if (obj.material instanceof THREE.ShadowMaterial) return false;
  return true;
}

function pickNearby(
  raycaster: THREE.Raycaster,
  pointer: THREE.Vector2,
  camera: THREE.Camera,
  scene: THREE.Scene,
): THREE.Vector3 | null {
  let bestPoint: THREE.Vector3 | null = null;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const radius of SAMPLE_RINGS) {
    const count = radius === 0 ? 1 : SAMPLE_DIRS;
    for (let i = 0; i < count; i += 1) {
      const angle = (i / count) * Math.PI * 2;
      _ndc.set(pointer.x + Math.cos(angle) * radius, pointer.y + Math.sin(angle) * radius);
      if (Math.abs(_ndc.x) > 1.15 || Math.abs(_ndc.y) > 1.15) continue;
      raycaster.setFromCamera(_ndc, camera);
      const hits = raycaster.intersectObjects(scene.children, true);
      for (const hit of hits) {
        if (!isPickableMesh(hit.object)) continue;
        if (hit.distance < bestDistance) {
          bestDistance = hit.distance;
          bestPoint = hit.point.clone();
        }
        break;
      }
    }
  }
  return bestPoint;
}

function pointerFromEvent(event: MouseEvent, element: HTMLElement, out: THREE.Vector2) {
  const rect = element.getBoundingClientRect();
  const w = Math.max(rect.width, 1);
  const h = Math.max(rect.height, 1);
  out.set(((event.clientX - rect.left) / w) * 2 - 1, -((event.clientY - rect.top) / h) * 2 + 1);
}

function ease(dt: number, rate: number) {
  return 1 - Math.exp(-rate * dt);
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
  const zooming = useRef(false);
  const zoomDistance = useRef(camera.position.distanceTo(new THREE.Vector3(...DEFAULT_TARGET)));
  const zoomPivot = useRef(new THREE.Vector3(...DEFAULT_TARGET));
  const gestureUntil = useRef(0);
  const raycaster = useRef(new THREE.Raycaster());
  const pointer = useRef(new THREE.Vector2());
  const applyFocusRef = useRef<(point: THREE.Vector3, smooth?: boolean) => void>(() => undefined);

  function stopScriptedMotion() {
    animating.current = false;
  }

  function syncZoomFromCamera(orbit: OrbitControlsImpl) {
    zoomDistance.current = THREE.MathUtils.clamp(
      camera.position.distanceTo(orbit.target),
      MIN_DISTANCE,
      MAX_DISTANCE,
    );
    zoomPivot.current.copy(orbit.target);
  }

  function applyFocus(point: THREE.Vector3, smooth = true) {
    const orbit = controls.current;
    if (!orbit) return;
    zooming.current = false;
    const offset = camera.position.clone().sub(orbit.target);
    const dist = THREE.MathUtils.clamp(offset.length(), MIN_DISTANCE, MAX_DISTANCE);
    const dir =
      offset.lengthSq() > 1e-8 ? offset.normalize() : new THREE.Vector3(0.42, 0.18, 0.88).normalize();
    goalTarget.current.copy(point);
    goalEye.current.copy(point).addScaledVector(dir, dist);
    zoomDistance.current = dist;
    zoomPivot.current.copy(point);
    if (smooth) {
      animating.current = true;
      return;
    }
    camera.position.copy(goalEye.current);
    orbit.target.copy(point);
    orbit.update();
    animating.current = false;
  }

  applyFocusRef.current = applyFocus;

  useEffect(() => {
    registerOrbitFocus((point, options) => {
      applyFocusRef.current(point, options?.smooth !== false);
    });
    return () => registerOrbitFocus(null);
  }, []);

  useEffect(() => {
    const next = goalsFor(muscle);
    goalEye.current.copy(next.eye);
    goalTarget.current.copy(next.target);
    zoomDistance.current = next.eye.distanceTo(next.target);
    zoomPivot.current.copy(next.target);
    animating.current = true;
    zooming.current = false;
  }, [muscle, resetToken]);

  useEffect(() => {
    const element = gl.domElement;

    const onWheel = (event: WheelEvent) => {
      const orbit = controls.current;
      if (!orbit || !orbit.enabled) return;
      event.preventDefault();
      event.stopPropagation();
      animating.current = false;

      const now = performance.now();
      const freshGesture = now > gestureUntil.current;
      gestureUntil.current = now + GESTURE_MS;

      if (freshGesture) {
        pointerFromEvent(event, element, pointer.current);
        const hit = pickNearby(raycaster.current, pointer.current, camera, scene);
        if (hit) {
          zoomPivot.current.copy(hit);
        } else {
          camera.getWorldDirection(_viewDir);
          _plane.setFromNormalAndCoplanarPoint(_viewDir, orbit.target);
          raycaster.current.setFromCamera(pointer.current, camera);
          const planePoint = raycaster.current.ray.intersectPlane(_plane, _planeHit);
          zoomPivot.current.copy(planePoint ?? orbit.target);
        }
        zoomDistance.current = THREE.MathUtils.clamp(
          camera.position.distanceTo(zoomPivot.current),
          MIN_DISTANCE,
          MAX_DISTANCE,
        );
      }

      const factor = Math.exp(event.deltaY * ZOOM_PIXEL_SCALE);
      zoomDistance.current = THREE.MathUtils.clamp(
        zoomDistance.current * factor,
        MIN_DISTANCE,
        MAX_DISTANCE,
      );
      zooming.current = true;
    };

    const onDblClick = (event: MouseEvent) => {
      pointerFromEvent(event, element, pointer.current);
      const hit = pickNearby(raycaster.current, pointer.current, camera, scene);
      if (hit) applyFocusRef.current(hit, true);
    };

    element.addEventListener("wheel", onWheel, { passive: false, capture: true });
    element.addEventListener("dblclick", onDblClick);
    return () => {
      element.removeEventListener("wheel", onWheel, true);
      element.removeEventListener("dblclick", onDblClick);
    };
  }, [camera, gl, scene]);

  useFrame((_, dt) => {
    const orbit = controls.current;
    if (!orbit) return;
    const dtClamped = Math.min(dt, 0.05);

    if (animating.current) {
      const k = ease(dtClamped, FOCUS_DAMP);
      camera.position.lerp(goalEye.current, k);
      orbit.target.lerp(goalTarget.current, k);
      orbit.update();
      if (
        camera.position.distanceTo(goalEye.current) < 0.012 &&
        orbit.target.distanceTo(goalTarget.current) < 0.012
      ) {
        animating.current = false;
        syncZoomFromCamera(orbit);
      }
      return;
    }

    if (!zooming.current) return;

    orbit.target.lerp(zoomPivot.current, ease(dtClamped, TARGET_DAMP));
    _offset.copy(camera.position).sub(orbit.target);
    const current = _offset.length();
    if (current < 1e-6) {
      zooming.current = false;
      return;
    }
    const next = THREE.MathUtils.damp(current, zoomDistance.current, ZOOM_DAMP, dtClamped);
    camera.position.copy(orbit.target).addScaledVector(_offset.multiplyScalar(1 / current), next);
    orbit.update();

    if (
      Math.abs(next - zoomDistance.current) < 0.0015 &&
      orbit.target.distanceTo(zoomPivot.current) < 0.004 &&
      performance.now() > gestureUntil.current
    ) {
      zooming.current = false;
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
      onStart={() => {
        stopScriptedMotion();
        zooming.current = false;
        if (controls.current) syncZoomFromCamera(controls.current);
      }}
    />
  );
}
