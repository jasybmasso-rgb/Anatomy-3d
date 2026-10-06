import * as THREE from "three";

export type OrbitFocusOptions = {
  smooth?: boolean;
};

type OrbitFocusHandler = (point: THREE.Vector3, options?: OrbitFocusOptions) => void;

let handler: OrbitFocusHandler | null = null;

export function registerOrbitFocus(next: OrbitFocusHandler | null) {
  handler = next;
}

export function requestOrbitFocus(point: THREE.Vector3, options?: OrbitFocusOptions) {
  handler?.(point, options);
}
