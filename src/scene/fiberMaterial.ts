import * as THREE from "three";

const BASE = new THREE.Color("#c44536");
const FIBER = new THREE.Color("#7a2218");

export function createFiberMuscleMaterial(fiberAxis: THREE.Vector3): THREE.MeshPhysicalMaterial {
  const material = new THREE.MeshPhysicalMaterial({
    color: BASE,
    roughness: 0.42,
    metalness: 0.03,
    transparent: true,
    opacity: 0.92,
    clearcoat: 0.12,
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
        "#include <worldpos_vertex>",
        `#include <worldpos_vertex>
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
float t = fract(along * 28.0);
float band = smoothstep(0.0, 0.08, t) * smoothstep(0.42, 0.18, t);
float fine = 0.55 + 0.45 * sin(along * 92.0);
float fiber = clamp(band * 0.85 + (1.0 - fine) * 0.22, 0.0, 1.0);
vec3 fiberCol = vec3(0.42, 0.10, 0.07);
diffuseColor.rgb = mix(diffuseColor.rgb, fiberCol, 0.55 * fiber);`,
      );
  };
  material.customProgramCacheKey = () =>
    `fiber:${axis.x.toFixed(3)},${axis.y.toFixed(3)},${axis.z.toFixed(3)}`;
  return material;
}

void FIBER;
