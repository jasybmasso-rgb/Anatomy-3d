import * as THREE from "three";

const RIDGE = new THREE.Color("#d45a4c");
const GROOVE = new THREE.Color("#5c140e");

/** Stripe frequency in cycles per metre along the fiber axis. */
const CYCLES_PER_M = 32;

const _p = new THREE.Vector3();
const _c = new THREE.Color();

export function paintFiberVertexColors(geometry: THREE.BufferGeometry, fiberAxis: THREE.Vector3) {
  const pos = geometry.getAttribute("position");
  if (!pos) return;
  const axis = fiberAxis.clone().normalize();
  const colors = new Float32Array(pos.count * 3);
  for (let i = 0; i < pos.count; i += 1) {
    _p.fromBufferAttribute(pos, i);
    const along = _p.dot(axis);
    const wave = 0.5 + 0.5 * Math.sin(along * CYCLES_PER_M * Math.PI * 2);
    const band = wave * wave;
    _c.copy(GROOVE).lerp(RIDGE, band);
    colors[i * 3] = _c.r;
    colors[i * 3 + 1] = _c.g;
    colors[i * 3 + 2] = _c.b;
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
}

export function createFiberMuscleMaterial(): THREE.MeshPhysicalMaterial {
  return new THREE.MeshPhysicalMaterial({
    color: "#ffffff",
    roughness: 0.58,
    metalness: 0.0,
    transparent: true,
    opacity: 0.94,
    clearcoat: 0.04,
    side: THREE.DoubleSide,
    vertexColors: true,
  });
}
