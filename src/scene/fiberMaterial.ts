import * as THREE from "three";

const _p = new THREE.Vector3();
const _centroid = new THREE.Vector3();
const _radial = new THREE.Vector3();
const _normal = new THREE.Vector3();
const _binormal = new THREE.Vector3();
const _helper = new THREE.Vector3();

let fiberTexture: THREE.CanvasTexture | null = null;

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function smoothstep(edge0: number, edge1: number, x: number) {
  const t = THREE.MathUtils.clamp((x - edge0) / (edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

/** Fusiform pedagogical map: pale tendinous ends, deep-red belly, soft fiber streaks. */
export function getFiberTexture(): THREE.CanvasTexture {
  if (fiberTexture) return fiberTexture;
  const width = 1024;
  const height = 256;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) {
    throw new Error("fiber canvas unavailable");
  }
  const image = ctx.createImageData(width, height);
  const data = image.data;

  for (let y = 0; y < height; y += 1) {
    const t = y / height;
    for (let x = 0; x < width; x += 1) {
      const s = x / (width - 1);
      const belly = Math.pow(Math.sin(Math.PI * s), 1.12);
      const tendon = 1 - belly;

      const rCol = lerp(0.93, lerp(0.72, 0.48, belly), belly);
      const gCol = lerp(0.86, lerp(0.22, 0.08, belly), belly);
      const bCol = lerp(0.78, lerp(0.16, 0.07, belly), belly);

      const cycles = lerp(46, 11, belly);
      const phase = t * cycles * Math.PI * 2 + 0.55 * Math.sin(s * 19.0) + 0.28 * Math.sin(t * 14.0);
      const wave = 0.5 + 0.5 * Math.sin(phase);
      const fine = 0.5 + 0.5 * Math.sin(t * (cycles * 1.85) * Math.PI * 2 + s * 8.0);
      const ridge = smoothstep(0.22, 0.78, wave * 0.82 + fine * 0.18);

      const contrast = lerp(0.14, 0.38, belly);
      const shade = lerp(1 - contrast, 1 + contrast * 0.15, ridge);
      const pale = 1 + tendon * 0.08;
      const r = THREE.MathUtils.clamp(rCol * shade * pale, 0, 1);
      const g = THREE.MathUtils.clamp(gCol * shade * pale, 0, 1);
      const b = THREE.MathUtils.clamp(bCol * shade * pale, 0, 1);

      const i = (y * width + x) * 4;
      data[i] = Math.round(r * 255);
      data[i + 1] = Math.round(g * 255);
      data[i + 2] = Math.round(b * 255);
      data[i + 3] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = THREE.ClampToEdgeWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.anisotropy = 8;
  tex.needsUpdate = true;
  fiberTexture = tex;
  return tex;
}

function collectHalves(pos: THREE.BufferAttribute): number[][] {
  const left: number[] = [];
  const right: number[] = [];
  for (let i = 0; i < pos.count; i += 1) {
    if (pos.getX(i) < 0) left.push(i);
    else right.push(i);
  }
  const minFrac = pos.count * 0.12;
  if (left.length > minFrac && right.length > minFrac) return [left, right];
  const all = new Array<number>(pos.count);
  for (let i = 0; i < pos.count; i += 1) all[i] = i;
  return [all];
}

/** U along origin→insertion, V around the belly (repeat). Split L/R for bilateral meshes. */
export function applyFiberUVs(geometry: THREE.BufferGeometry, fiberAxis: THREE.Vector3) {
  const pos = geometry.getAttribute("position");
  if (!pos) return;
  const axis = fiberAxis.clone().normalize();
  if (axis.lengthSq() < 1e-10) axis.set(0, 1, 0);

  const uv = new Float32Array(pos.count * 2);
  const groups = collectHalves(pos as THREE.BufferAttribute);

  for (const indices of groups) {
    _centroid.set(0, 0, 0);
    for (const i of indices) {
      _centroid.x += pos.getX(i);
      _centroid.y += pos.getY(i);
      _centroid.z += pos.getZ(i);
    }
    _centroid.multiplyScalar(1 / Math.max(indices.length, 1));

    let minAlong = Number.POSITIVE_INFINITY;
    let maxAlong = Number.NEGATIVE_INFINITY;
    for (const i of indices) {
      _p.fromBufferAttribute(pos, i);
      const along = _p.clone().sub(_centroid).dot(axis);
      if (along < minAlong) minAlong = along;
      if (along > maxAlong) maxAlong = along;
    }
    const span = Math.max(maxAlong - minAlong, 1e-5);

    _helper.set(0, 1, 0);
    if (Math.abs(axis.dot(_helper)) > 0.92) _helper.set(1, 0, 0);
    _normal.copy(axis).cross(_helper).normalize();
    _binormal.copy(axis).cross(_normal).normalize();

    for (const i of indices) {
      _p.fromBufferAttribute(pos, i);
      _p.sub(_centroid);
      const along = _p.dot(axis);
      const u = THREE.MathUtils.clamp((along - minAlong) / span, 0, 1);
      _radial.copy(_p).addScaledVector(axis, -along);
      const v = Math.atan2(_radial.dot(_binormal), _radial.dot(_normal)) / (Math.PI * 2) + 0.5;
      uv[i * 2] = u;
      uv[i * 2 + 1] = v;
    }
  }

  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

export function createFiberMuscleMaterial(): THREE.MeshPhysicalMaterial {
  const material = new THREE.MeshPhysicalMaterial({
    color: "#ffffff",
    map: getFiberTexture(),
    roughness: 0.52,
    metalness: 0.0,
    transparent: true,
    opacity: 0.96,
    clearcoat: 0.06,
    side: THREE.DoubleSide,
    vertexColors: false,
  });
  if ("anisotropy" in material) {
    (material as THREE.MeshPhysicalMaterial & { anisotropy: number }).anisotropy = 0.35;
  }
  return material;
}
