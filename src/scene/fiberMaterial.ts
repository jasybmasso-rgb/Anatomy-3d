import * as THREE from "three";

const _p = new THREE.Vector3();
const _centroid = new THREE.Vector3();
const _radial = new THREE.Vector3();
const _normal = new THREE.Vector3();
const _binormal = new THREE.Vector3();
const _helper = new THREE.Vector3();
const _size = new THREE.Vector3();
const _axis = new THREE.Vector3();
const _covCol = new THREE.Vector3();

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
  float endCap = 1.0 - smoothstep(0.0, 0.10, min(along, 1.0 - along));

  vec3 tendonCol = vec3(0.94, 0.88, 0.76);
  vec3 midCol = vec3(0.62, 0.14, 0.10);
  vec3 bellyCol = vec3(0.33, 0.038, 0.036);
  vec3 base = mix(tendonCol, mix(midCol, bellyCol, smoothstep(0.18, 1.0, belly)), smoothstep(0.0, 0.42, belly));
  base = mix(base, vec3(0.97, 0.93, 0.84), endCap * 0.38);

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
  float lum = dot(col, vec3(0.32, 0.5, 0.18));
  vec3 chainCol = tint * mix(0.4, 1.2, lum);
  col = mix(col, chainCol, clamp(tintMix, 0.0, 1.0));
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
  float density = 44.0;
  float warp = fiberFbm(circ * 1.8 + vec2(along * 2.4, 2.7)) - 0.5;
  vec2 fuv = circ * density + vec2(warp * 1.6, along * 2.0);
  float n = fiberFbm(fuv) * 0.7 + fiberFbm(fuv * 2.2 + 5.0) * 0.3;
  float ridge = smoothstep(0.34, 0.7, n);
  vec3 base = vec3(0.72, 0.38, 0.07);
  vec3 fiber = vec3(0.96, 0.74, 0.22);
  vec3 col = mix(base, fiber, ridge * 0.72);
  float endFlare = 1.0 - smoothstep(0.0, 0.16, min(along, 1.0 - along));
  col = mix(col, vec3(0.93, 0.62, 0.16), endFlare * 0.55);
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

/** Longest principal axis of the given vertices (model space, not world +Y). */
export function pcaLongAxis(
  pos: THREE.BufferAttribute,
  indices: number[],
  hint?: THREE.Vector3,
): THREE.Vector3 {
  _centroid.set(0, 0, 0);
  for (const i of indices) {
    _centroid.x += pos.getX(i);
    _centroid.y += pos.getY(i);
    _centroid.z += pos.getZ(i);
  }
  _centroid.multiplyScalar(1 / Math.max(indices.length, 1));

  let xx = 0;
  let xy = 0;
  let xz = 0;
  let yy = 0;
  let yz = 0;
  let zz = 0;
  for (const i of indices) {
    const dx = pos.getX(i) - _centroid.x;
    const dy = pos.getY(i) - _centroid.y;
    const dz = pos.getZ(i) - _centroid.z;
    xx += dx * dx;
    xy += dx * dy;
    xz += dx * dz;
    yy += dy * dy;
    yz += dy * dz;
    zz += dz * dz;
  }

  _axis.copy(hint && hint.lengthSq() > 1e-8 ? hint : _helper.set(0, 1, 0));
  if (_axis.lengthSq() < 1e-10) _axis.set(0, 1, 0);
  _axis.normalize();
  for (let iter = 0; iter < 14; iter += 1) {
    _covCol.set(
      xx * _axis.x + xy * _axis.y + xz * _axis.z,
      xy * _axis.x + yy * _axis.y + yz * _axis.z,
      xz * _axis.x + yz * _axis.y + zz * _axis.z,
    );
    if (_covCol.lengthSq() < 1e-12) break;
    _axis.copy(_covCol).normalize();
  }
  if (hint && hint.lengthSq() > 1e-8 && _axis.dot(hint) < 0) _axis.negate();
  return _axis.clone();
}

/** U along the mesh long axis (PCA, aligned with O→I hint), V around the belly. */
export function applyFiberUVs(geometry: THREE.BufferGeometry, fiberAxis?: THREE.Vector3) {
  const pos = geometry.getAttribute("position");
  if (!pos) return;
  const hint = fiberAxis?.clone();
  if (hint && hint.lengthSq() < 1e-10) hint.set(0, 0, 0);

  const uv = new Float32Array(pos.count * 2);
  const groups = collectHalves(pos as THREE.BufferAttribute);

  for (const indices of groups) {
    const axis = pcaLongAxis(pos as THREE.BufferAttribute, indices, hint && hint.lengthSq() > 0 ? hint : undefined);
    if (axis.lengthSq() < 1e-10) axis.set(0, 1, 0);

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

/** Longest AABB axis — fallback for ligaments when PCA is overkill. */
export function inferLongAxis(geometry: THREE.BufferGeometry): THREE.Vector3 {
  if (!geometry.boundingBox) geometry.computeBoundingBox();
  const box = geometry.boundingBox;
  if (!box) return new THREE.Vector3(0, 1, 0);
  box.getSize(_size);
  if (_size.x >= _size.y && _size.x >= _size.z) return new THREE.Vector3(1, 0, 0);
  if (_size.y >= _size.x && _size.y >= _size.z) return new THREE.Vector3(0, 1, 0);
  return new THREE.Vector3(0, 0, 1);
}

export function clipPlanesForSide(side: "both" | "left" | "right"): THREE.Plane[] {
  if (side === "right") return [new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0.01)];
  if (side === "left") return [new THREE.Plane(new THREE.Vector3(1, 0, 0), 0.01)];
  return [];
}

export type FiberMaterialKind = "muscle" | "ligament";

export function createFiberMuscleMaterial(): THREE.MeshPhysicalMaterial {
  const material = new THREE.MeshPhysicalMaterial({
    color: "#ffffff",
    map: getDummyMap(),
    roughness: 0.52,
    metalness: 0.0,
    transparent: false,
    opacity: 1,
    depthWrite: true,
    clearcoat: 0.05,
    side: THREE.FrontSide,
    vertexColors: false,
    clippingPlanes: [],
    clipShadows: true,
  });
  material.userData.uTint = new THREE.Color(1, 1, 1);
  material.userData.uTintMix = { value: 0 };
  material.userData.uSelected = { value: 0 };
  material.userData.kind = "muscle";
  material.onBeforeCompile = (shader) => {
    shader.uniforms.uTint = { value: material.userData.uTint };
    shader.uniforms.uTintMix = material.userData.uTintMix;
    shader.uniforms.uSelected = material.userData.uSelected;
    shader.vertexShader = shader.vertexShader.replace(
      "#include <common>",
      `#include <common>\nattribute float tendon;\nvarying float vTendon;`,
    );
    shader.vertexShader = shader.vertexShader.replace(
      "#include <begin_vertex>",
      `#include <begin_vertex>\nvTendon = tendon;`,
    );
    shader.fragmentShader = shader.fragmentShader.replace(
      "uniform vec3 diffuse;",
      "uniform vec3 diffuse;\nuniform vec3 uTint;\nuniform float uTintMix;\nuniform float uSelected;\nvarying float vTendon;",
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
        vec3 tendonCol = vec3(0.94, 0.88, 0.76);
        fiberAlbedo = mix(fiberAlbedo, tendonCol, clamp(vTendon, 0.0, 1.0));
        float selected = clamp(uSelected, 0.0, 1.0);
        fiberAlbedo = mix(fiberAlbedo, fiberAlbedo * vec3(1.18, 1.08, 0.88), selected * 0.38);
        #ifndef FLAT_SHADED
        vec3 nView = normalize(vNormal);
        float fres = pow(1.0 - abs(nView.z), 2.15);
        fiberAlbedo += vec3(1.0, 0.76, 0.28) * fres * selected * 1.05;
        #else
        fiberAlbedo += vec3(0.45, 0.22, 0.06) * selected * 0.16;
        #endif
        diffuseColor *= vec4(fiberAlbedo, 1.0);
      }
      `,
    );
    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <roughnessmap_fragment>",
      `#include <roughnessmap_fragment>
       roughnessFactor = mix(pedagogicalMuscleRoughness(vMapUv), 0.36, clamp(vTendon, 0.0, 1.0));
       roughnessFactor = mix(roughnessFactor, 0.28, clamp(uSelected, 0.0, 1.0) * 0.55);
      `,
    );
    material.userData.shader = shader;
  };
  material.customProgramCacheKey = () => "anatomy-fiber-muscle-v9-selected";
  return material;
}

export function createLigamentFiberMaterial(schematic: boolean): THREE.MeshPhysicalMaterial {
  const material = new THREE.MeshPhysicalMaterial({
    color: "#ffffff",
    map: getDummyMap(),
    roughness: schematic ? 0.52 : 0.46,
    metalness: 0.04,
    transparent: true,
    opacity: schematic ? 0.92 : 0.96,
    depthTest: !schematic,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexColors: false,
    emissive: schematic ? "#7a3a08" : "#5a2a06",
    emissiveIntensity: schematic ? 0.28 : 0.2,
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
    schematic ? "anatomy-fiber-ligament-synth-v4" : "anatomy-fiber-ligament-bp3d-v4";
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

export function setMuscleSelected(material: THREE.MeshPhysicalMaterial, selected: boolean) {
  const sel = material.userData.uSelected as { value: number } | undefined;
  if (sel) sel.value = selected ? 1 : 0;
  material.emissive.set(selected ? "#ff9a4a" : "#000000");
  material.emissiveIntensity = selected ? 0.28 : 0;
  material.clearcoat = selected ? 0.18 : 0.05;
}
