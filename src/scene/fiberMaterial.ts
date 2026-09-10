import * as THREE from "three";

const _p = new THREE.Vector3();
const _centroid = new THREE.Vector3();
const _radial = new THREE.Vector3();
const _normal = new THREE.Vector3();
const _binormal = new THREE.Vector3();
const _helper = new THREE.Vector3();
const _size = new THREE.Vector3();

const GLSL_NOISE = /* glsl */ `
float fiberHash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}
float fiberNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  float a = fiberHash(i);
  float b = fiberHash(i + vec2(1.0, 0.0));
  float c = fiberHash(i + vec2(0.0, 1.0));
  float d = fiberHash(i + vec2(1.0, 1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}
float fiberFbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 5; i++) {
    v += a * fiberNoise(p);
    p *= 2.09;
    a *= 0.5;
  }
  return v;
}
vec2 fiberCirc(float around) {
  float ang = around * 6.28318530718;
  return vec2(cos(ang), sin(ang));
}
`;

const GLSL_MUSCLE_ALBEDO = /* glsl */ `
vec3 pedagogicalMuscleAlbedo(vec2 uv, vec3 tint, float tintMix) {
  float along = clamp(uv.x, 0.0, 1.0);
  vec2 circ = fiberCirc(uv.y);
  float belly = pow(sin(3.14159265 * along), 1.42);
  float tendon = 1.0 - belly;
  float endCap = 1.0 - smoothstep(0.0, 0.13, min(along, 1.0 - along));

  vec3 tendonCol = vec3(0.94, 0.88, 0.76);
  vec3 midCol = vec3(0.62, 0.14, 0.10);
  vec3 bellyCol = vec3(0.33, 0.038, 0.036);
  vec3 base = mix(tendonCol, mix(midCol, bellyCol, smoothstep(0.18, 1.0, belly)), smoothstep(0.0, 0.42, belly));
  base = mix(base, vec3(0.97, 0.93, 0.84), endCap * 0.92);

  // Wider spacing in the belly, denser toward origin / insertion.
  float density = mix(72.0, 17.0, belly);
  float warp = fiberFbm(circ * 2.2 + vec2(along * 2.8, 4.1)) - 0.5;
  vec2 fuv = circ * density + vec2(warp * 2.1, along * 1.6);
  float n = fiberFbm(fuv);
  n = n * 0.62 + fiberFbm(fuv * 2.35 + vec2(along * 3.4, 9.0)) * 0.38;
  float ridge = smoothstep(0.32, 0.74, n);
  float contrast = mix(0.16, 0.055, belly);
  float shade = mix(1.0 - contrast, 1.0 + contrast * 0.28, ridge);
  vec3 col = base * shade;
  col = mix(col, mix(col, tendonCol, 0.4), tendon * ridge * 0.22);
  col = mix(col, col * tint, clamp(tintMix, 0.0, 1.0));
  return clamp(col, 0.0, 1.0);
}
float pedagogicalMuscleRoughness(vec2 uv) {
  float along = clamp(uv.x, 0.0, 1.0);
  float belly = pow(sin(3.14159265 * along), 1.42);
  return mix(0.38, 0.62, belly);
}
`;

const GLSL_LIGAMENT_ALBEDO = /* glsl */ `
vec3 pedagogicalLigamentAlbedo(vec2 uv) {
  float along = clamp(uv.x, 0.0, 1.0);
  vec2 circ = fiberCirc(uv.y);
  float density = 48.0;
  float warp = fiberFbm(circ * 1.8 + vec2(along * 2.4, 2.7)) - 0.5;
  vec2 fuv = circ * density + vec2(warp * 1.6, along * 2.0);
  float n = fiberFbm(fuv) * 0.7 + fiberFbm(fuv * 2.2 + 5.0) * 0.3;
  float ridge = smoothstep(0.34, 0.7, n);
  vec3 base = vec3(0.86, 0.76, 0.62);
  vec3 fiber = vec3(0.93, 0.86, 0.74);
  vec3 col = mix(base * 0.92, fiber, ridge * 0.55);
  float endFlare = 1.0 - smoothstep(0.0, 0.12, min(along, 1.0 - along));
  col = mix(col, vec3(0.91, 0.82, 0.68), endFlare * 0.25);
  return clamp(col, 0.0, 1.0);
}
`;

function patchAfterCommon(fragmentShader: string, extras: string): string {
  if (!fragmentShader.includes("#include <common>")) return fragmentShader;
  return fragmentShader.replace("#include <common>", `#include <common>\n${extras}`);
}

let dummyMap: THREE.DataTexture | null = null;
function getDummyMap(): THREE.DataTexture {
  if (dummyMap) return dummyMap;
  const tex = new THREE.DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1);
  tex.needsUpdate = true;
  dummyMap = tex;
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

/** U along origin→insertion, V around the belly. Split L/R for bilateral meshes. */
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
      _p.sub(_centroid);
      const along = _p.dot(axis);
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

/** Longest AABB axis — good enough for ligaments and unknown fiber direction. */
export function inferLongAxis(geometry: THREE.BufferGeometry): THREE.Vector3 {
  if (!geometry.boundingBox) geometry.computeBoundingBox();
  const box = geometry.boundingBox;
  if (!box) return new THREE.Vector3(0, 1, 0);
  box.getSize(_size);
  if (_size.x >= _size.y && _size.x >= _size.z) return new THREE.Vector3(1, 0, 0);
  if (_size.y >= _size.x && _size.y >= _size.z) return new THREE.Vector3(0, 1, 0);
  return new THREE.Vector3(0, 0, 1);
}

export type FiberMaterialKind = "muscle" | "ligament";

export function createFiberMuscleMaterial(): THREE.MeshPhysicalMaterial {
  const material = new THREE.MeshPhysicalMaterial({
    color: "#ffffff",
    map: getDummyMap(),
    roughness: 0.52,
    metalness: 0.0,
    transparent: true,
    opacity: 0.96,
    clearcoat: 0.05,
    side: THREE.FrontSide,
    vertexColors: false,
  });
  material.userData.uTint = new THREE.Color(1, 1, 1);
  material.userData.uTintMix = { value: 0 };
  material.userData.kind = "muscle";
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uTint = { value: material.userData.uTint };
    shader.uniforms.uTintMix = material.userData.uTintMix;
    shader.fragmentShader = shader.fragmentShader.replace(
      "uniform vec3 diffuse;",
      "uniform vec3 diffuse;\nuniform vec3 uTint;\nuniform float uTintMix;",
    );
    shader.fragmentShader = patchAfterCommon(
      shader.fragmentShader,
      `${GLSL_NOISE}\n${GLSL_MUSCLE_ALBEDO}`,
    );
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <map_fragment>",
      /* glsl */ `
      {
        vec2 fiberUv = vMapUv;
        vec3 fiberAlbedo = pedagogicalMuscleAlbedo(fiberUv, uTint, uTintMix);
        diffuseColor *= vec4(fiberAlbedo, 1.0);
      }
      `,
    );
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <roughnessmap_fragment>",
      `#include <roughnessmap_fragment>
       roughnessFactor = pedagogicalMuscleRoughness(vMapUv);
      `,
    );
    material.userData.shader = shader;
  };
  material.customProgramCacheKey = () => "anatomy-fiber-muscle-v4";
  return material;
}

export function createLigamentFiberMaterial(schematic: boolean): THREE.MeshPhysicalMaterial {
  const material = new THREE.MeshPhysicalMaterial({
    color: "#ffffff",
    map: getDummyMap(),
    roughness: schematic ? 0.58 : 0.5,
    metalness: 0.0,
    transparent: true,
    opacity: schematic ? 0.82 : 0.94,
    depthTest: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexColors: false,
    emissive: schematic ? "#2a1c10" : "#3a2414",
    emissiveIntensity: schematic ? 0.06 : 0.12,
  });
  material.userData.kind = "ligament";
  material.onBeforeCompile = (shader) => {
    shader.fragmentShader = patchAfterCommon(
      shader.fragmentShader,
      `${GLSL_NOISE}\n${GLSL_LIGAMENT_ALBEDO}`,
    );
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <map_fragment>",
      /* glsl */ `
      {
        vec3 fiberAlbedo = pedagogicalLigamentAlbedo(vMapUv);
        diffuseColor *= vec4(fiberAlbedo, 1.0);
      }
      `,
    );
    material.userData.shader = shader;
  };
  material.customProgramCacheKey = () =>
    schematic ? "anatomy-fiber-ligament-synth-v2" : "anatomy-fiber-ligament-bp3d-v2";
  return material;
}

export function setMuscleTint(material: THREE.MeshPhysicalMaterial, tint: THREE.Color | null, mix = 0.48) {
  const current = material.userData.uTint as THREE.Color | undefined;
  const mixRef = material.userData.uTintMix as { value: number } | undefined;
  if (tint && current && mixRef) {
    current.copy(tint);
    mixRef.value = mix;
  } else if (current && mixRef) {
    current.setRGB(1, 1, 1);
    mixRef.value = 0;
  } else if (tint) {
    material.color.copy(tint);
    material.color.lerp(new THREE.Color("#ffffff"), 0.4);
  } else {
    material.color.set("#ffffff");
  }
}
