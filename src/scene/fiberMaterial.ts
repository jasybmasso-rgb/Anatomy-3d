import * as THREE from "three";

const BASE = new THREE.Color("#c44536");

/**
 * Pedagogical fiber direction: world-space stripes along origin→insertion (PCA).
 * Injected after project_vertex so it does not depend on USE_ENVMAP/shadow chunks.
 */
export function createFiberMuscleMaterial(fiberAxis: THREE.Vector3): THREE.MeshPhysicalMaterial {
  const material = new THREE.MeshPhysicalMaterial({
    color: BASE,
    roughness: 0.62,
    metalness: 0.0,
    transparent: true,
    opacity: 0.94,
    clearcoat: 0.0,
    sheen: 0.35,
    sheenColor: new THREE.Color("#8a2a20"),
    sheenRoughness: 0.85,
    side: THREE.DoubleSide,
    vertexColors: false,
  });
  const axis = fiberAxis.clone().normalize();
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uFiberDir = { value: axis };
    shader.vertexShader = shader.vertexShader
      .replace(
        "#include <common>",
        `#include <common>
varying vec3 vFiberPos;`,
      )
      .replace(
        "#include <project_vertex>",
        `#include <project_vertex>
vFiberPos = (modelMatrix * vec4(transformed, 1.0)).xyz;`,
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        "#include <common>",
        `#include <common>
varying vec3 vFiberPos;
uniform vec3 uFiberDir;`,
      )
      .replace(
        "#include <color_fragment>",
        `#include <color_fragment>
vec3 fdir = normalize(uFiberDir);
float along = dot(vFiberPos, fdir);
float t = fract(along * 20.0);
float groove = smoothstep(0.08, 0.0, abs(t - 0.5));
float fill = smoothstep(0.18, 0.42, abs(t - 0.5));
vec3 grooveCol = vec3(0.36, 0.08, 0.06);
vec3 ridgeCol = vec3(0.86, 0.38, 0.30);
diffuseColor.rgb = mix(ridgeCol, grooveCol, 0.55 + 0.45 * groove);
diffuseColor.rgb = mix(diffuseColor.rgb, ridgeCol, 0.22 * fill);`,
      );
  };
  material.customProgramCacheKey = () =>
    `fiber-v2:${axis.x.toFixed(3)},${axis.y.toFixed(3)},${axis.z.toFixed(3)}`;
  material.needsUpdate = true;
  return material;
}
