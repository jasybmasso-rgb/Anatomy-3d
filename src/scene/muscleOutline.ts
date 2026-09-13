import * as THREE from "three";
import { getDeviceProfile } from "./deviceProfile";

/** Thin inverted-hull outline — cheap extra draw, readable when muscles overlap. */
export function createMuscleOutlineMaterial(): THREE.MeshBasicMaterial {
  const inflate = getDeviceProfile().lowEnd ? 0.0020 : 0.0026;
  const material = new THREE.MeshBasicMaterial({
    color: "#0a0a0c",
    side: THREE.BackSide,
    depthWrite: true,
    depthTest: true,
    transparent: false,
    clippingPlanes: [],
    clipShadows: true,
  });
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uInflate = { value: inflate };
    shader.vertexShader = `uniform float uInflate;\n${shader.vertexShader}`;
    shader.vertexShader = shader.vertexShader.replace(
      "#include <begin_vertex>",
      `#include <begin_vertex>
       transformed += normalize(objectNormal) * uInflate;`,
    );
  };
  material.customProgramCacheKey = () => `anatomy-muscle-outline-v2-${inflate}`;
  return material;
}

export function attachMuscleOutline(mesh: THREE.Mesh, material: THREE.MeshBasicMaterial): THREE.Mesh {
  const outline = new THREE.Mesh(mesh.geometry, material);
  outline.name = "muscle-outline";
  outline.raycast = () => {};
  outline.castShadow = false;
  outline.receiveShadow = false;
  outline.frustumCulled = true;
  outline.renderOrder = Math.max((mesh.renderOrder ?? 0) - 1, 0);
  mesh.add(outline);
  return outline;
}
