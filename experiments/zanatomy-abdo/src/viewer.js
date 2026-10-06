import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const VARIANTS = [
  { id: "original", label: "Original", file: "models/original.glb" },
  { id: "m25", label: "25 %", file: "models/meshopt-25.glb" },
  { id: "m10", label: "10 %", file: "models/meshopt-10.glb" },
  { id: "m10nm", label: "10 % + normales 2K", file: "models/meshopt-10-nm.glb" },
  { id: "m10nm1k", label: "10 % + normales 1K", file: "models/meshopt-10-nm1k.glb" },
  { id: "m05", label: "5 %", file: "models/meshopt-05.glb" },
  { id: "m05nm", label: "5 % + normales 2K", file: "models/meshopt-05-nm.glb" },
  { id: "m05nm1k", label: "5 % + normales 1K", file: "models/meshopt-05-nm1k.glb" },
  { id: "d25", label: "Decimate 25 %", file: "models/decimate-25.glb" },
  { id: "d10", label: "Decimate 10 %", file: "models/decimate-10.glb" },
  { id: "d05", label: "Decimate 5 %", file: "models/decimate-05.glb" },
];

const GRID = ["original", "m25", "m10nm", "m05nm"];

const params = new URLSearchParams(location.search);
const shot = params.get("shot") === "1";
if (shot) document.body.classList.add("shot");

const stage = document.getElementById("stage");
const variantSelect = document.getElementById("variant");
const fpsEl = document.getElementById("fps");
for (const variant of VARIANTS) {
  const option = document.createElement("option");
  option.value = variant.id;
  option.textContent = variant.label;
  variantSelect.append(option);
}

const loader = new GLTFLoader();
const cache = new Map();
const clock = new THREE.Clock();
let frames = 0;
let fps = 0;
let viewName = params.get("view") === "close" ? "close" : "front";
let layout = params.get("layout") === "single" ? "single" : "grid";
let lodOn = params.get("lod") === "1";

const hemi = () => new THREE.HemisphereLight(0xfff4ea, 0xb7b1a8, 0.72);
const key = () => {
  const light = new THREE.DirectionalLight(0xffffff, 1.55);
  light.position.set(0.45, 1.15, 0.85);
  return light;
};
const fill = () => {
  const light = new THREE.DirectionalLight(0xd5def0, 0.38);
  light.position.set(-0.9, 0.35, -0.35);
  return light;
};

function tuneMaterial(material) {
  material.roughness = 0.48;
  material.metalness = 0;
  material.side = THREE.DoubleSide;
  if (material.normalMap) material.normalScale.set(1, 1);
}

function prepare(root) {
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
    for (const material of materials) tuneMaterial(material);
  });
  return root;
}

function triangleCount(root) {
  let triangles = 0;
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    const geometry = obj.geometry;
    triangles += geometry.index ? geometry.index.count / 3 : geometry.attributes.position.count / 3;
  });
  return triangles;
}

async function loadVariant(id) {
  if (cache.has(id)) return cache.get(id);
  const variant = VARIANTS.find((item) => item.id === id);
  const gltf = await loader.loadAsync(variant.file);
  const root = prepare(gltf.scene);
  const record = { id, label: variant.label, root, triangles: triangleCount(root) };
  cache.set(id, record);
  return record;
}

function fitBox(root) {
  return new THREE.Box3().setFromObject(root);
}

function namedBox(root, name) {
  let found = null;
  root.traverse((obj) => {
    if (obj.name === name) found = obj;
  });
  return found ? new THREE.Box3().setFromObject(found) : fitBox(root);
}

function poseCamera(camera, root) {
  const box = fitBox(root);
  const center = box.getCenter(new THREE.Vector3());
  const radius = Math.max(box.getSize(new THREE.Vector3()).length() * 0.55, 0.2);
  let azimuth = THREE.MathUtils.degToRad(24);
  let elevation = THREE.MathUtils.degToRad(12);
  let distance = radius * 2.35;
  let look = center.clone();
  if (viewName === "close") {
    const oblique = namedBox(root, "external_l");
    const size = oblique.getSize(new THREE.Vector3());
    look = oblique.getCenter(new THREE.Vector3());
    look.y += size.y * 0.34;
    look.x += size.x * 0.05;
    azimuth = THREE.MathUtils.degToRad(32);
    elevation = THREE.MathUtils.degToRad(18);
    distance = Math.max(size.x, size.y) * 1.15;
  }
  if (params.get("az")) azimuth = THREE.MathUtils.degToRad(Number(params.get("az")));
  if (params.get("el")) elevation = THREE.MathUtils.degToRad(Number(params.get("el")));
  if (params.get("dist")) distance = Number(params.get("dist"));
  const offset = new THREE.Vector3(
    Math.sin(azimuth) * Math.cos(elevation),
    Math.sin(elevation),
    Math.cos(azimuth) * Math.cos(elevation),
  ).multiplyScalar(distance);
  camera.position.copy(look).add(offset);
  camera.near = 0.01;
  camera.far = 50;
  camera.lookAt(look);
  camera.updateProjectionMatrix();
  return look;
}

const panes = [];

function makePane(parent) {
  const wrap = document.createElement("div");
  wrap.style.position = "absolute";
  wrap.style.overflow = "hidden";
  const label = document.createElement("div");
  label.className = "label";
  const canvas = document.createElement("canvas");
  canvas.style.width = "100%";
  canvas.style.height = "100%";
  canvas.style.display = "block";
  wrap.append(canvas, label);
  parent.append(wrap);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, shot ? 1 : 1.5));
  renderer.setClearColor(0xe6e1d8, 1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 50);
  scene.add(hemi(), key(), fill());
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.enabled = !shot;
  const pane = { wrap, label, renderer, scene, camera, controls, root: null, record: null };
  panes.push(pane);
  return pane;
}

function clearPanes() {
  for (const pane of panes) {
    pane.renderer.dispose();
    pane.wrap.remove();
  }
  panes.length = 0;
}

function layoutPanes(count) {
  const width = stage.clientWidth;
  const height = stage.clientHeight;
  const cols = count === 1 ? 1 : 2;
  const rows = count === 1 ? 1 : 2;
  panes.forEach((pane, index) => {
    const col = index % cols;
    const row = Math.floor(index / cols);
    const w = Math.floor(width / cols);
    const h = Math.floor(height / rows);
    pane.wrap.style.left = `${col * w}px`;
    pane.wrap.style.top = `${row * h}px`;
    pane.wrap.style.width = `${w}px`;
    pane.wrap.style.height = `${h}px`;
    pane.renderer.setSize(w, h, false);
    pane.camera.aspect = w / Math.max(1, h);
    pane.camera.updateProjectionMatrix();
  });
}

async function show(ids) {
  clearPanes();
  const records = [];
  for (const id of ids) {
    try {
      records.push(await loadVariant(id));
    } catch (error) {
      console.warn("missing variant", id, error);
    }
  }
  if (!records.length) return;
  for (const record of records) {
    const pane = makePane(stage);
    const root = record.root.clone(true);
    pane.scene.add(root);
    pane.root = root;
    pane.record = record;
    const look = poseCamera(pane.camera, root);
    pane.controls.target.copy(look);
    pane.controls.update();
    pane.label.innerHTML = `<b>${record.label}</b> <span>${record.triangles.toLocaleString("fr-FR")} triangles</span>`;
  }
  layoutPanes(panes.length);
  syncCameras(panes[0]);
  window.__ready = true;
  window.__variants = records.map((record) => ({
    id: record.id,
    label: record.label,
    triangles: record.triangles,
  }));
}

function syncCameras(source) {
  for (const pane of panes) {
    if (pane === source) continue;
    pane.camera.position.copy(source.camera.position);
    pane.camera.quaternion.copy(source.camera.quaternion);
    pane.controls.target.copy(source.controls.target);
  }
}

function applyLod(distance) {
  if (!lodOn || layout !== "single" || panes.length !== 1) return;
  const base = panes[0].baseDistance || distance;
  panes[0].baseDistance = base;
  const near = distance < base * 1.25 ? "m25" : "m05";
  const pane = panes[0];
  if (pane.record?.id === near) return;
  const next = cache.get(near);
  if (!next) return;
  pane.scene.remove(pane.root);
  const root = next.root.clone(true);
  pane.scene.add(root);
  pane.root = root;
  pane.record = next;
  pane.label.innerHTML = `<b>LOD ${next.label}</b> <span>${next.triangles.toLocaleString("fr-FR")} triangles</span>`;
}

function animate() {
  requestAnimationFrame(animate);
  const dt = clock.getDelta();
  frames += 1;
  if (panes[0]) {
    panes[0].controls.update();
    syncCameras(panes[0]);
    const distance = panes[0].camera.position.distanceTo(panes[0].controls.target);
    applyLod(distance);
  }
  for (const pane of panes) pane.renderer.render(pane.scene, pane.camera);
  if (frames % 20 === 0) {
    fps = dt > 0 ? Math.round(1 / dt) : 0;
    // The interval above is per frame, so recompute over a short window instead.
  }
}

let fpsFrames = 0;
let fpsStamp = performance.now();
setInterval(() => {
  const now = performance.now();
  const elapsed = (now - fpsStamp) / 1000;
  fps = elapsed > 0 ? Math.round((frames - fpsFrames) / elapsed) : 0;
  fpsFrames = frames;
  fpsStamp = now;
  if (fpsEl) fpsEl.textContent = `${fps} img/s`;
  window.__fps = fps;
}, 500);

document.getElementById("grid").addEventListener("click", () => {
  layout = "grid";
  document.getElementById("grid").setAttribute("aria-pressed", "true");
  document.getElementById("single").setAttribute("aria-pressed", "false");
  show(GRID);
});
document.getElementById("single").addEventListener("click", () => {
  layout = "single";
  document.getElementById("grid").setAttribute("aria-pressed", "false");
  document.getElementById("single").setAttribute("aria-pressed", "true");
  show([variantSelect.value]);
});
variantSelect.addEventListener("change", () => {
  if (layout === "single") show([variantSelect.value]);
});
document.getElementById("front").addEventListener("click", () => {
  viewName = "front";
  show(layout === "grid" ? GRID : [variantSelect.value]);
});
document.getElementById("close").addEventListener("click", () => {
  viewName = "close";
  show(layout === "grid" ? GRID : [variantSelect.value]);
});
document.getElementById("lod").addEventListener("change", (event) => {
  lodOn = event.target.checked;
  if (lodOn) {
    layout = "single";
    Promise.all([loadVariant("m25"), loadVariant("m05")]).then(() => show(["m25"]));
  }
});
window.addEventListener("resize", () => layoutPanes(panes.length));

const initial = params.get("variant");
if (initial) {
  layout = "single";
  variantSelect.value = initial;
}
if (params.get("layout") === "single") layout = "single";
show(layout === "grid" ? GRID : [initial || "original"]).then(() => {
  if (params.get("bench") === "1") {
    const samples = [];
    const started = performance.now();
    const timer = setInterval(() => {
      samples.push(window.__fps || 0);
      if (performance.now() - started > 2500) {
        clearInterval(timer);
        const warm = samples.slice(1);
        const avg = warm.length ? Math.round(warm.reduce((a, b) => a + b, 0) / warm.length) : 0;
        window.__bench = { fps: avg, samples: warm, triangles: panes[0]?.record?.triangles ?? null };
        document.body.dataset.bench = String(avg);
      }
    }, 400);
  }
});
animate();
