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
const DAMPING = 0.08;
const ZOOM_PIXEL_SCALE = 0.0044;
const FOCUS_DAMP = 8;
const SKIP_PICK = new Set(["ignore", "floor", "shadow"]);
const _ndc = new THREE.Vector2();
const _viewDir = new THREE.Vector3();
const _plane = new THREE.Plane();
const _planeHit = new THREE.Vector3();
const _offset = new THREE.Vector3();
const _pivot = new THREE.Vector3();

function normalizedWheelDelta(event: WheelEvent) {
  let dy = event.deltaY;
  if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) dy *= 16;
  else if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) dy *= 80;
  return THREE.MathUtils.clamp(dy, -140, 140);
}

/** Camera offset so the selected muscle faces the viewer (L/R, A/P, region). */
function facingOffset(focus: THREE.Vector3, distance: number): THREE.Vector3 {
  const { x, y, z } = focus;
  const side = x < -0.025 ? -1 : x > 0.025 ? 1 : 0;
  const posterior = z < 0.02;
  const anterior = z > 0.05;
  const cranial = y > 0.52;
  const caudal = y < -0.25;
  const limb = Math.abs(x) > 0.12;

  let dx: number;
  let dy: number;
  let dz: number;
  if (posterior) {
    dz = -0.88;
    dx = side * (limb ? 0.4 : 0.26);
  } else if (anterior) {
    dz = 0.9;
    dx = side * (limb ? 0.38 : 0.3);
  } else {
    dz = 0.52;
    dx = side === 0 ? 0.2 : side * 0.64;
  }
  dy = cranial ? 0.2 : caudal ? 0.05 : 0.15;
  if (cranial && !posterior) dz = Math.max(dz, 0.72);
  if (cranial && posterior) dy = 0.12;

  return new THREE.Vector3(dx, dy, dz).normalize().multiplyScalar(distance);
}

function goalsFor(muscle: Muscle | null): { eye: THREE.Vector3; target: THREE.Vector3 } {
  if (!muscle) {
    return {
      eye: new THREE.Vector3(...DEFAULT_EYE),
      target: new THREE.Vector3(...DEFAULT_TARGET),
    };
  }
  const [tx, ty, tz] = toLandmarkFocus(muscle.focus.position);
  let d = THREE.MathUtils.clamp(muscle.focus.distance, 0.45, 2.4);
  if (muscle.id === "grand-dorsal") d = Math.max(d, 1.28);
  else if (muscle.region === "dos") d = Math.max(d, 0.95);
  else if (muscle.region === "tête") d = Math.max(d, 0.72);
  const target = new THREE.Vector3(tx, ty, tz);
  return {
    target,
    eye: target.clone().add(facingOffset(target, d)),
  };
}

function isPickableMesh(obj: THREE.Object3D): obj is THREE.Mesh {
  if (!(obj instanceof THREE.Mesh) || !obj.visible) return false;
  if (SKIP_PICK.has(String(obj.userData.pick ?? ""))) return false;
  if (obj.material instanceof THREE.ShadowMaterial) return false;
  return true;
}

function pickSurface(
  raycaster: THREE.Raycaster,
  pointer: THREE.Vector2,
  camera: THREE.Camera,
  scene: THREE.Scene,
): THREE.Vector3 | null {
  _ndc.copy(pointer);
  raycaster.setFromCamera(_ndc, camera);
  const hits = raycaster.intersectObjects(scene.children, true);
  for (const hit of hits) {
    if (!isPickableMesh(hit.object)) continue;
    return hit.point.clone();
  }
  return null;
}

function cursorOnTargetPlane(
  raycaster: THREE.Raycaster,
  pointer: THREE.Vector2,
  camera: THREE.Camera,
  orbit: OrbitControlsImpl,
  out: THREE.Vector3,
): THREE.Vector3 {
  camera.getWorldDirection(_viewDir);
  _plane.setFromNormalAndCoplanarPoint(_viewDir, orbit.target);
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.ray.intersectPlane(_plane, _planeHit);
  return out.copy(hit ?? orbit.target);
}

function pointerFromClient(clientX: number, clientY: number, element: HTMLElement, out: THREE.Vector2) {
  const rect = element.getBoundingClientRect();
  const w = Math.max(rect.width, 1);
  const h = Math.max(rect.height, 1);
  out.set(((clientX - rect.left) / w) * 2 - 1, -((clientY - rect.top) / h) * 2 + 1);
}

function ease(dt: number, rate: number) {
  return 1 - Math.exp(-rate * dt);
}

function applyDollyToward(
  camera: THREE.Camera,
  orbit: OrbitControlsImpl,
  logFactor: number,
  pivot: THREE.Vector3,
) {
  const factor = Math.exp(logFactor);
  _offset.copy(camera.position).sub(pivot);
  const camDist = _offset.length();
  if (camDist > 1e-6) {
    const nextCam = THREE.MathUtils.clamp(camDist * factor, MIN_DISTANCE, MAX_DISTANCE);
    camera.position.copy(pivot).addScaledVector(_offset.multiplyScalar(1 / camDist), nextCam);
  }
  _offset.copy(orbit.target).sub(pivot);
  orbit.target.copy(pivot).addScaledVector(_offset, factor);
  _offset.copy(camera.position).sub(orbit.target);
  const dist = _offset.length();
  if (dist > 1e-6) {
    const clamped = THREE.MathUtils.clamp(dist, MIN_DISTANCE, MAX_DISTANCE);
    if (clamped !== dist) {
      camera.position.copy(orbit.target).addScaledVector(_offset.multiplyScalar(1 / dist), clamped);
    }
  }
  orbit.update();
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
  const applyFocusRef = useRef<(point: THREE.Vector3, smooth?: boolean) => void>(() => undefined);
  const pointers = useRef(new Map<number, { x: number; y: number }>());
  const pinchDist = useRef(0);

  function stopScriptedMotion() {
    animating.current = false;
  }

  function applyFocus(point: THREE.Vector3, smooth = true) {
    const orbit = controls.current;
    if (!orbit) return;
    const offset = camera.position.clone().sub(orbit.target);
    const dist = THREE.MathUtils.clamp(offset.length(), MIN_DISTANCE, MAX_DISTANCE);
    const dir =
      offset.lengthSq() > 1e-8 ? offset.normalize() : new THREE.Vector3(0.42, 0.18, 0.88).normalize();
    goalTarget.current.copy(point);
    goalEye.current.copy(point).addScaledVector(dir, dist);
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
    animating.current = true;
  }, [muscle, resetToken]);

  useEffect(() => {
    const element = gl.domElement;
    element.style.touchAction = "none";

    const queueZoom = (clientX: number, clientY: number, logDelta: number) => {
      const orbit = controls.current;
      if (!orbit) return;
      animating.current = false;
      pointerFromClient(clientX, clientY, element, pointer.current);
      cursorOnTargetPlane(raycaster.current, pointer.current, camera, orbit, _pivot);
      applyDollyToward(camera, orbit, logDelta, _pivot);
    };

    const onWheel = (event: WheelEvent) => {
      const orbit = controls.current;
      if (!orbit || !orbit.enabled) return;
      event.preventDefault();
      event.stopPropagation();
      queueZoom(event.clientX, event.clientY, normalizedWheelDelta(event) * ZOOM_PIXEL_SCALE);
    };

    const onDblClick = (event: MouseEvent) => {
      pointerFromClient(event.clientX, event.clientY, element, pointer.current);
      const hit = pickSurface(raycaster.current, pointer.current, camera, scene);
      if (hit) applyFocusRef.current(hit, true);
    };

    const pinchDistance = () => {
      const pts = [...pointers.current.values()];
      if (pts.length < 2) return 0;
      const dx = pts[0].x - pts[1].x;
      const dy = pts[0].y - pts[1].y;
      return Math.hypot(dx, dy);
    };

    const onPointerDown = (event: PointerEvent) => {
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (pointers.current.size === 2) {
        pinchDist.current = pinchDistance();
      }
    };

    const onPointerMove = (event: PointerEvent) => {
      if (!pointers.current.has(event.pointerId)) return;
      pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (pointers.current.size < 2 || pinchDist.current < 4) return;
      const next = pinchDistance();
      if (next < 4) return;
      const ratio = pinchDist.current / next;
      pinchDist.current = next;
      const logDelta = Math.log(THREE.MathUtils.clamp(ratio, 0.86, 1.16));
      if (Math.abs(logDelta) < 1e-5) return;
      const pts = [...pointers.current.values()];
      queueZoom((pts[0].x + pts[1].x) / 2, (pts[0].y + pts[1].y) / 2, logDelta);
    };

    const onPointerUp = (event: PointerEvent) => {
      pointers.current.delete(event.pointerId);
      if (pointers.current.size < 2) pinchDist.current = 0;
    };

    element.addEventListener("wheel", onWheel, { passive: false, capture: true });
    element.addEventListener("dblclick", onDblClick);
    element.addEventListener("pointerdown", onPointerDown);
    element.addEventListener("pointermove", onPointerMove);
    element.addEventListener("pointerup", onPointerUp);
    element.addEventListener("pointercancel", onPointerUp);
    element.addEventListener("pointerleave", onPointerUp);
    return () => {
      element.removeEventListener("wheel", onWheel, true);
      element.removeEventListener("dblclick", onDblClick);
      element.removeEventListener("pointerdown", onPointerDown);
      element.removeEventListener("pointermove", onPointerMove);
      element.removeEventListener("pointerup", onPointerUp);
      element.removeEventListener("pointercancel", onPointerUp);
      element.removeEventListener("pointerleave", onPointerUp);
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
      }
    }
  });

  return (
    <OrbitControls
      ref={controls}
      makeDefault
      enableDamping
      dampingFactor={DAMPING}
      enableZoom={false}
      enablePan
      screenSpacePanning
      minDistance={MIN_DISTANCE}
      maxDistance={MAX_DISTANCE}
      touches={{
        ONE: THREE.TOUCH.ROTATE,
        TWO: THREE.TOUCH.PAN,
      }}
      mouseButtons={{
        LEFT: THREE.MOUSE.ROTATE,
        MIDDLE: THREE.MOUSE.DOLLY,
        RIGHT: THREE.MOUSE.PAN,
      }}
      onStart={() => {
        stopScriptedMotion();
      }}
    />
  );
}
