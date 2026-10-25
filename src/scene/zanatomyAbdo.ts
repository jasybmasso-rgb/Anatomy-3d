import * as THREE from "three";
import { publicUrl } from "../lib/publicUrl";
import {
  applyFiberUVs,
  createFiberMuscleMaterial,
  setMuscleTendonAlpha,
} from "./fiberMaterial";

export const ZANATOMY_ABDO_URL = publicUrl("/models/zanatomy-abdo.glb");
export const DRACO_DECODER_PATH = publicUrl("/draco/");

/** Abdominal wall muscles replaced by the Z-Anatomy mesh when that mode is on. */
export const ABDOMINAL_WALL_IDS = [
  "droit-abdomen",
  "oblique-externe",
  "oblique-interne",
  "transverse-de-l-abdomen",
] as const;

export type AbdominalWallId = (typeof ABDOMINAL_WALL_IDS)[number];

const ABDOMINAL_WALL = new Set<string>(ABDOMINAL_WALL_IDS);

/** OE / OI / TA keep a translucent procedural aponeurosis. Rectus keeps the linea alba strip. */
const SHEATH_IDS = new Set<string>(["oblique-externe", "oblique-interne", "transverse-de-l-abdomen"]);

export function isAbdominalWall(id: string): id is AbdominalWallId {
  return ABDOMINAL_WALL.has(id);
}

/**
 * Z-Anatomy (May 2023) is Y-up, origin near the feet, anterior +Z, patient left +X.
 * The app skeleton is the same facing, origin near the pelvis, stature ~1.7 m.
 *
 * Fit (pubic origin of rectus pinned on the pubic crest, xiphoid / costal margin
 * checked against the anterior skeleton): uniform scale 0.995, +4° pitch about X.
 * Patient left stays +X, so Myers L/R clipping still cuts on x = 0.
 */
const PIVOT = new THREE.Vector3(0, 0.861, 0.052);
const TARGET = new THREE.Vector3(0, -0.064, 0.094);
const SCALE = 0.995;
const PITCH = (4 * Math.PI) / 180;
const AXIS_X = new THREE.Vector3(1, 0, 0);

const MUSCLE_RED: [number, number, number] = [196 / 255, 72 / 255, 58 / 255];
const TENDON_WHITE: [number, number, number] = [245 / 255, 236 / 255, 214 / 255];

/** Medial limit of the fleshy belly — same semilunar curves as the procedural sheaths. */
const SEMILUNAR: Record<string, { y: number[]; x: number[] }> = {
  "oblique-externe": {
    y: [-0.04, 0.04, 0.1, 0.18, 0.26],
    x: [0.118, 0.112, 0.09, 0.066, 0.056],
  },
  "oblique-interne": {
    y: [-0.02, 0.04, 0.12, 0.22],
    x: [0.07, 0.064, 0.058, 0.056],
  },
  "transverse-de-l-abdomen": {
    y: [-0.04, 0.04, 0.14, 0.26],
    x: [0.058, 0.056, 0.05, 0.04],
  },
};

/** How far the Z-Anatomy flesh still tucks under the translucent sheath (metres). */
const SHEATH_OVERLAP = 0.008;

const FLESH_OFFSET: Record<string, number> = {
  "transverse-de-l-abdomen": 8,
  "oblique-interne": 3,
  "droit-abdomen": 0,
  "oblique-externe": -6,
};

const APO_OFFSET: Record<string, number> = {
  "transverse-de-l-abdomen": 4,
  "oblique-interne": -1,
  "droit-abdomen": -2,
  "oblique-externe": -12,
};

const FLESH_ORDER: Record<string, number> = {
  "transverse-de-l-abdomen": 1,
  "oblique-interne": 3,
  "droit-abdomen": 5,
  "oblique-externe": 8,
};

const APO_ORDER: Record<string, number> = {
  "transverse-de-l-abdomen": 2,
  "oblique-interne": 4,
  "droit-abdomen": 6,
  "oblique-externe": 10,
};

const ZA_PREFIX: Record<string, AbdominalWallId> = {
  rectus: "droit-abdomen",
  external: "oblique-externe",
  internal: "oblique-interne",
  transversus: "transverse-de-l-abdomen",
};

export type MuscleRep = {
  object: THREE.Group;
  materials: THREE.MeshPhongMaterial[];
  meshes: THREE.Mesh[];
};

const _centroid = new THREE.Vector3();

function semilunarX(muscleId: string, y: number): number {
  const curve = SEMILUNAR[muscleId];
  if (!curve) return 0;
  const { y: stops, x: values } = curve;
  if (y <= stops[0]) return values[0];
  for (let i = 1; i < stops.length; i += 1) {
    if (y <= stops[i]) {
      const t = (y - stops[i - 1]) / (stops[i] - stops[i - 1]);
      return values[i - 1] + t * (values[i] - values[i - 1]);
    }
  }
  return values[values.length - 1];
}

function muscleIdFromName(name: string): AbdominalWallId | null {
  const key = name.split("_")[0];
  return ZA_PREFIX[key] ?? null;
}

function isLeftMesh(mesh: THREE.Mesh): boolean {
  const name = `${mesh.parent?.name ?? ""} ${mesh.name}`;
  return /(^|_)l(_|$)/.test(name);
}

function isTendonMesh(mesh: THREE.Mesh): boolean {
  if (/rectus_[lr]_2$/.test(mesh.name)) return true;
  const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  return mats.some((mat) => (mat?.name ?? "").toLowerCase().includes("tendon"));
}

function flipWinding(geometry: THREE.BufferGeometry) {
  const index = geometry.getIndex();
  if (!index) return;
  for (let i = 0; i < index.count; i += 3) {
    const a = index.getX(i);
    const c = index.getX(i + 2);
    index.setX(i, c);
    index.setX(i + 2, a);
  }
  index.needsUpdate = true;
}

function alignGeometry(source: THREE.BufferGeometry, flip: boolean): THREE.BufferGeometry {
  const geometry = source.clone();
  if (flip) flipWinding(geometry);
  const pos = geometry.getAttribute("position");
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i += 1) {
    v.fromBufferAttribute(pos as THREE.BufferAttribute, i);
    v.sub(PIVOT);
    v.applyAxisAngle(AXIS_X, PITCH);
    v.multiplyScalar(SCALE);
    v.add(TARGET);
    pos.setXYZ(i, v.x, v.y, v.z);
  }
  pos.needsUpdate = true;
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return geometry;
}

function paintSolid(geometry: THREE.BufferGeometry, rgb: [number, number, number]) {
  const count = geometry.getAttribute("position").count;
  const arr = new Float32Array(count * 3);
  for (let i = 0; i < count; i += 1) {
    arr[i * 3] = rgb[0];
    arr[i * 3 + 1] = rgb[1];
    arr[i * 3 + 2] = rgb[2];
  }
  geometry.setAttribute("color", new THREE.BufferAttribute(arr, 3));
}

function vertexTendon(color: THREE.BufferAttribute | THREE.InterleavedBufferAttribute, index: number): number {
  let r = color.getX(index);
  let g = color.getY(index);
  let b = color.getZ(index);
  if (r > 1.01 || g > 1.01 || b > 1.01) {
    r /= 255;
    g /= 255;
    b /= 255;
  }
  const lum = 0.299 * r + 0.587 * g + 0.114 * b;
  const chroma = Math.max(r, g, b) - Math.min(r, g, b);
  const pale = THREE.MathUtils.smoothstep(0.55, 0.84, lum);
  const unsaturated = 1 - THREE.MathUtils.smoothstep(0.16, 0.42, chroma);
  return pale * unsaturated;
}

function triangleCentroid(
  pos: THREE.BufferAttribute | THREE.InterleavedBufferAttribute,
  ia: number,
  ib: number,
  ic: number,
  target: THREE.Vector3,
) {
  target.set(
    (pos.getX(ia) + pos.getX(ib) + pos.getX(ic)) / 3,
    (pos.getY(ia) + pos.getY(ib) + pos.getY(ic)) / 3,
    (pos.getZ(ia) + pos.getZ(ib) + pos.getZ(ic)) / 3,
  );
}

function filterTriangles(
  geometry: THREE.BufferGeometry,
  keep: (ia: number, ib: number, ic: number) => boolean,
): THREE.BufferGeometry | null {
  const index = geometry.getIndex();
  const pos = geometry.getAttribute("position");
  const normal = geometry.getAttribute("normal");
  const uv = geometry.getAttribute("uv");
  const color = geometry.getAttribute("color");
  if (!pos) return null;
  const triCount = index ? index.count / 3 : pos.count / 3;
  const ids: number[] = [];
  for (let t = 0; t < triCount; t += 1) {
    const ia = index ? index.getX(t * 3) : t * 3;
    const ib = index ? index.getX(t * 3 + 1) : t * 3 + 1;
    const ic = index ? index.getX(t * 3 + 2) : t * 3 + 2;
    if (keep(ia, ib, ic)) ids.push(ia, ib, ic);
  }
  if (ids.length === 0) return null;
  const out = new THREE.BufferGeometry();
  const n = ids.length;
  const pArr = new Float32Array(n * 3);
  const nArr = normal ? new Float32Array(n * 3) : null;
  const uArr = uv ? new Float32Array(n * 2) : null;
  const cArr = color ? new Float32Array(n * 3) : null;
  for (let i = 0; i < n; i += 1) {
    const vi = ids[i];
    pArr[i * 3] = pos.getX(vi);
    pArr[i * 3 + 1] = pos.getY(vi);
    pArr[i * 3 + 2] = pos.getZ(vi);
    if (nArr && normal) {
      nArr[i * 3] = normal.getX(vi);
      nArr[i * 3 + 1] = normal.getY(vi);
      nArr[i * 3 + 2] = normal.getZ(vi);
    }
    if (uArr && uv) {
      uArr[i * 2] = uv.getX(vi);
      uArr[i * 2 + 1] = uv.getY(vi);
    }
    if (cArr && color) {
      let r = color.getX(vi);
      let g = color.getY(vi);
      let b = color.getZ(vi);
      if (r > 1.01 || g > 1.01 || b > 1.01) {
        r /= 255;
        g /= 255;
        b /= 255;
      }
      cArr[i * 3] = r;
      cArr[i * 3 + 1] = g;
      cArr[i * 3 + 2] = b;
    }
  }
  out.setAttribute("position", new THREE.BufferAttribute(pArr, 3));
  if (nArr) out.setAttribute("normal", new THREE.BufferAttribute(nArr, 3));
  if (uArr) out.setAttribute("uv", new THREE.BufferAttribute(uArr, 2));
  if (cArr) out.setAttribute("color", new THREE.BufferAttribute(cArr, 3));
  return out;
}

/**
 * Z-Anatomy bakes the OE / OI / TA aponeurosis into the same opaque material.
 * Drop that medial sheet so the existing translucent procedural sheath can show
 * the rectus instead of z-fighting an opaque duplicate.
 */
function dropMedialSheath(geometry: THREE.BufferGeometry, muscleId: string): THREE.BufferGeometry | null {
  if (!SEMILUNAR[muscleId]) return geometry;
  const pos = geometry.getAttribute("position");
  const filtered = filterTriangles(geometry, (ia, ib, ic) => {
    triangleCentroid(pos, ia, ib, ic, _centroid);
    if (_centroid.z < 0.02) return true;
    return Math.abs(_centroid.x) >= semilunarX(muscleId, _centroid.y) - SHEATH_OVERLAP;
  });
  return filtered;
}

function isPaleTriangle(
  color: THREE.BufferAttribute | THREE.InterleavedBufferAttribute,
  ia: number,
  ib: number,
  ic: number,
): boolean {
  const w0 = vertexTendon(color, ia);
  const w1 = vertexTendon(color, ib);
  const w2 = vertexTendon(color, ic);
  const avg = (w0 + w1 + w2) / 3;
  const max = Math.max(w0, w1, w2);
  return avg > 0.28 && max > 0.45;
}

function bakeWorld(geometry: THREE.BufferGeometry, mesh: THREE.Mesh): THREE.BufferGeometry {
  mesh.updateWorldMatrix(true, false);
  const baked = geometry.clone();
  baked.applyMatrix4(mesh.matrixWorld);
  return baked;
}

function extractProceduralSheet(
  meshes: THREE.Mesh[],
  mode: "sheath" | "linea",
): THREE.BufferGeometry | null {
  const parts: THREE.BufferGeometry[] = [];
  for (const mesh of meshes) {
    const geometry = bakeWorld(mesh.geometry, mesh);
    const color = geometry.getAttribute("color");
    const pos = geometry.getAttribute("position");
    if (!color || !pos) continue;
    const sheet = filterTriangles(geometry, (ia, ib, ic) => {
      if (!isPaleTriangle(color, ia, ib, ic)) return false;
      if (mode === "linea") {
        triangleCentroid(pos, ia, ib, ic, _centroid);
        if (Math.abs(_centroid.x) > 0.0045) return false;
      }
      return true;
    });
    if (sheet) parts.push(sheet);
  }
  if (parts.length === 0) return null;
  if (parts.length === 1) return parts[0];
  const merged = new THREE.BufferGeometry();
  const count = parts.reduce((sum, part) => sum + part.getAttribute("position").count, 0);
  const pArr = new Float32Array(count * 3);
  const nArr = new Float32Array(count * 3);
  const uArr = new Float32Array(count * 2);
  const cArr = new Float32Array(count * 3);
  let cursor = 0;
  for (const part of parts) {
    const n = part.getAttribute("position").count;
    pArr.set(part.getAttribute("position").array as Float32Array, cursor * 3);
    const normal = part.getAttribute("normal");
    if (normal) nArr.set(normal.array as Float32Array, cursor * 3);
    const uv = part.getAttribute("uv");
    if (uv) uArr.set(uv.array as Float32Array, cursor * 2);
    const col = part.getAttribute("color");
    if (col) cArr.set(col.array as Float32Array, cursor * 3);
    cursor += n;
  }
  merged.setAttribute("position", new THREE.BufferAttribute(pArr, 3));
  merged.setAttribute("normal", new THREE.BufferAttribute(nArr, 3));
  merged.setAttribute("uv", new THREE.BufferAttribute(uArr, 2));
  merged.setAttribute("color", new THREE.BufferAttribute(cArr, 3));
  return merged;
}

function fleshMaterial(muscleId: string): THREE.MeshPhongMaterial {
  const material = createFiberMuscleMaterial();
  material.side = THREE.DoubleSide;
  material.name = `za-${muscleId}`;
  const offset = FLESH_OFFSET[muscleId] ?? 0;
  material.polygonOffset = true;
  material.polygonOffsetFactor = offset;
  material.polygonOffsetUnits = offset;
  return material;
}

function apoMaterial(muscleId: string): THREE.MeshPhongMaterial {
  const material = createFiberMuscleMaterial();
  material.side = THREE.DoubleSide;
  material.name = `apo-${muscleId}`;
  setMuscleTendonAlpha(material, 0.5);
  material.transparent = true;
  material.depthWrite = true;
  material.opacity = 1;
  material.polygonOffset = true;
  material.polygonOffsetFactor = APO_OFFSET[muscleId] ?? -4;
  material.polygonOffsetUnits = APO_OFFSET[muscleId] ?? -4;
  material.userData.aponeurosis = true;
  return material;
}

function makeMesh(
  geometry: THREE.BufferGeometry,
  material: THREE.MeshPhongMaterial,
  muscleId: string,
  renderOrder: number,
): THREE.Mesh {
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = `za-${muscleId}`;
  mesh.userData.pick = "muscle";
  mesh.userData.muscleId = muscleId;
  mesh.userData.renderOrder = renderOrder;
  mesh.castShadow = true;
  mesh.receiveShadow = false;
  mesh.frustumCulled = true;
  return mesh;
}

export function buildZAnatomyReps(
  scene: THREE.Object3D,
  proceduralMeshes: Map<string, THREE.Mesh[]>,
  fiberAxis: Map<string, THREE.Vector3 | undefined>,
): Map<string, MuscleRep> {
  const buckets = new Map<AbdominalWallId, THREE.Mesh[]>();
  scene.traverse((obj) => {
    if (!(obj instanceof THREE.Mesh)) return;
    const id = muscleIdFromName(obj.name) ?? muscleIdFromName(obj.parent?.name ?? "");
    if (!id) return;
    const list = buckets.get(id) ?? [];
    list.push(obj);
    buckets.set(id, list);
  });

  const reps = new Map<string, MuscleRep>();
  for (const id of ABDOMINAL_WALL_IDS) {
    const sources = buckets.get(id) ?? [];
    const group = new THREE.Group();
    group.name = `zanatomy-${id}`;
    const flesh = fleshMaterial(id);
    const materials: THREE.MeshPhongMaterial[] = [flesh];
    const meshes: THREE.Mesh[] = [];
    const lockHint = SHEATH_IDS.has(id);
    const hint = fiberAxis.get(id);

    for (const source of sources) {
      let geometry = alignGeometry(source.geometry, isLeftMesh(source));
      paintSolid(geometry, isTendonMesh(source) ? TENDON_WHITE : MUSCLE_RED);
      applyFiberUVs(geometry, hint, lockHint);
      if (SHEATH_IDS.has(id)) {
        const kept = dropMedialSheath(geometry, id);
        if (!kept) continue;
        if (kept !== geometry) geometry = kept;
      }
      const mesh = makeMesh(geometry, flesh, id, FLESH_ORDER[id] ?? 5);
      group.add(mesh);
      meshes.push(mesh);
    }

    const procedural = proceduralMeshes.get(id) ?? [];
    const sheet = extractProceduralSheet(procedural, id === "droit-abdomen" ? "linea" : "sheath");
    if (sheet) {
      const apo = apoMaterial(id);
      materials.push(apo);
      const mesh = makeMesh(sheet, apo, id, APO_ORDER[id] ?? 6);
      mesh.name = `apo-${id}`;
      group.add(mesh);
      meshes.push(mesh);
    }

    group.visible = false;
    reps.set(id, { object: group, materials, meshes });
  }
  return reps;
}
