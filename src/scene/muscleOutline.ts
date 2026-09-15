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
  const pixels = getDeviceProfile().lowEnd ? 4.2 : 5.2;
  const material = new THREE.MeshBasicMaterial({
    color: "#000000",
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
      "#include <begin_vertex>",
      `#include <begin_vertex>
       transformed += normalize(objectNormal) * 0.0014;`,
    );
    shader.vertexShader = shader.vertexShader.replace(
      "#include <project_vertex>",
      `#include <project_vertex>
       {
         vec3 nView = normalize(transformedNormal);
         vec2 nSS = nView.xy;
         float nLen = max(length(nSS), 1e-5);
         nSS /= nLen;
         float px = uPixels * gl_Position.w * 2.0 / max(uResolution.y, 1.0);
         gl_Position.xy += nSS * px;
       }`,
    );
  };
  material.customProgramCacheKey = () => `anatomy-muscle-outline-hull-ss-v4-${pixels}`;
  outlineHullMaterials.push(material);
  return material;
}

function createEdgeMaterial(): LineMaterial {
  const mat = new LineMaterial({
    color: 0x000000,
    linewidth: getDeviceProfile().lowEnd ? 2.8 : 3.4,
    dashed: false,
    worldUnits: false,
    depthTest: true,
    depthWrite: false,
    transparent: false,
    toneMapped: false,
  });
  mat.resolution.copy(sharedResolution);
  mat.clipping = true;
  mat.clippingPlanes = [];
  mat.polygonOffset = true;
  mat.polygonOffsetFactor = -6;
  mat.polygonOffsetUnits = -6;
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

  const threshold = getDeviceProfile().lowEnd ? 38 : 28;
  const edges = new THREE.EdgesGeometry(mesh.geometry, threshold);
  const pos = edges.getAttribute("position");
  if (pos && pos.count >= 2) {
    const lg = new LineSegmentsGeometry();
    lg.setPositions(pos.array as Float32Array);
    const lines = new LineSegments2(lg, materials.edges);
    lines.name = "muscle-outline";
    lines.raycast = () => {};
    lines.frustumCulled = false;
    lines.renderOrder = (mesh.renderOrder ?? 0) + 4;
    mesh.add(lines);
  }
  edges.dispose();
}
