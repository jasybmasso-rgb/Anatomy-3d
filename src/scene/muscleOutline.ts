import * as THREE from "three";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";
import { LineSegments2 } from "three/examples/jsm/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/examples/jsm/lines/LineSegmentsGeometry.js";
import { getDeviceProfile } from "./deviceProfile";

const sharedResolution = new THREE.Vector2(1280, 800);
const outlineLineMaterials: LineMaterial[] = [];
const outlineHullMaterials: THREE.MeshBasicMaterial[] = [];

/** Keep Line2 pixel width correct after canvas resize / DPR changes. */
export function setOutlineResolution(width: number, height: number) {
  sharedResolution.set(Math.max(width, 1), Math.max(height, 1));
  for (const mat of outlineLineMaterials) mat.resolution.copy(sharedResolution);
  for (const mat of outlineHullMaterials) {
    const shader = mat.userData.shader as { uniforms?: { uResolution?: { value: THREE.Vector2 } } } | undefined;
    shader?.uniforms?.uResolution?.value.copy(sharedResolution);
  }
}

function createHullMaterial(): THREE.MeshBasicMaterial {
  const low = getDeviceProfile().lowEnd;
  const pixels = low ? 2.4 : 2.8;
  const material = new THREE.MeshBasicMaterial({
    color: "#0a0a0c",
    side: THREE.BackSide,
    depthWrite: false,
    depthTest: true,
    transparent: false,
    toneMapped: false,
    clippingPlanes: [],
    clipShadows: true,
  });
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uPixels = { value: pixels };
    shader.uniforms.uResolution = { value: sharedResolution };
    material.userData.shader = shader;
    shader.vertexShader = `uniform float uPixels;\nuniform vec2 uResolution;\n${shader.vertexShader}`;
    shader.vertexShader = shader.vertexShader.replace(
      "#include <project_vertex>",
      `#include <project_vertex>
       {
         vec3 nView = normalize(transformedNormal);
         vec2 nSS = nView.xy;
         float nLen = length(nSS);
         if (nLen > 1e-5) nSS /= nLen;
         else nSS = vec2(1.0, 0.0);
         float px = uPixels * gl_Position.w * 2.0 / max(uResolution.y, 1.0);
         gl_Position.xy += nSS * px;
       }`,
    );
  };
  material.customProgramCacheKey = () => `anatomy-muscle-outline-hull-ss-${pixels}`;
  outlineHullMaterials.push(material);
  return material;
}

function createEdgeMaterial(): LineMaterial {
  const low = getDeviceProfile().lowEnd;
  const mat = new LineMaterial({
    color: 0x0a0a0c,
    linewidth: low ? 1.8 : 2.4,
    dashed: false,
    worldUnits: false,
    depthTest: true,
    depthWrite: false,
    transparent: false,
    toneMapped: false,
  });
  mat.resolution.copy(sharedResolution);
  mat.clippingPlanes = [];
  outlineLineMaterials.push(mat);
  return mat;
}

export type MuscleOutlineBundle = {
  hull: THREE.MeshBasicMaterial;
  edges: LineMaterial;
};

/** Per-muscle materials so chain clipping stays independent. */
export function createMuscleOutlineMaterials(): MuscleOutlineBundle {
  return { hull: createHullMaterial(), edges: createEdgeMaterial() };
}

export function attachMuscleOutline(mesh: THREE.Mesh, materials: MuscleOutlineBundle): void {
  const hull = new THREE.Mesh(mesh.geometry, materials.hull);
  hull.name = "muscle-outline";
  hull.raycast = () => {};
  hull.castShadow = false;
  hull.receiveShadow = false;
  hull.frustumCulled = true;
  hull.renderOrder = (mesh.renderOrder ?? 0) + 2;
  mesh.add(hull);

  if (getDeviceProfile().lowEnd) return;

  const threshold = 32;
  const edges = new THREE.EdgesGeometry(mesh.geometry, threshold);
  const pos = edges.getAttribute("position");
  if (pos && pos.count >= 2) {
    const lg = new LineSegmentsGeometry();
    lg.setPositions(pos.array as Float32Array);
    const lines = new LineSegments2(lg, materials.edges);
    lines.name = "muscle-outline";
    lines.raycast = () => {};
    lines.frustumCulled = true;
    lines.renderOrder = (mesh.renderOrder ?? 0) + 3;
    mesh.add(lines);
  }
  edges.dispose();
}
