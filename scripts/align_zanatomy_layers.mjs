/**
 * Bake the abdominal-wall fit onto the PR #4 Z-Anatomy GLBs and write one
 * file per app layer. Vessels away from the hands and feet, and the
 * brain/sense-organ extract, are simplified only until a small error budget
 * (meshoptimizer). Hand, foot and nerve tubes stay at the authored resolution.
 *
 *   NODE_PATH=/tmp/za-tools/node_modules node scripts/align_zanatomy_layers.mjs
 */
import fs from "node:fs";
import path from "node:path";
import { Document, NodeIO } from "@gltf-transform/core";
import { ALL_EXTENSIONS } from "@gltf-transform/extensions";
import { draco, prune, simplify } from "@gltf-transform/functions";
import draco3d from "draco3dgltf";
import { MeshoptSimplifier } from "meshoptimizer";

const SRC = "public/models/zanatomy-original";
const OUT = "public/models/zanatomy";
const PIVOT = [0, 0.861, 0.052];
const TARGET = [0, -0.064, 0.094];
const SCALE = 0.995;
const PITCH = (4 * Math.PI) / 180;
const COS = Math.cos(PITCH);
const SIN = Math.sin(PITCH);

const NERVE_RE = /nerve|plexus|ganglion|\bramus\b|cauda equina|chorda tympani|sympathetic trunk|ansa cervicalis/i;

function align(x, y, z) {
  const vx = x - PIVOT[0];
  const vy = y - PIVOT[1];
  const vz = z - PIVOT[2];
  const y2 = vy * COS - vz * SIN;
  const z2 = vy * SIN + vz * COS;
  return [vx * SCALE + TARGET[0], y2 * SCALE + TARGET[1], z2 * SCALE + TARGET[2]];
}

function rot(x, y, z) {
  return [x, y * COS - z * SIN, y * SIN + z * COS];
}

function transformDoc(doc) {
  const seen = new Set();
  for (const mesh of doc.getRoot().listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const pos = prim.getAttribute("POSITION");
      if (!pos || seen.has(pos)) continue;
      seen.add(pos);
      const src = pos.getArray();
      const out = new Float32Array(src.length);
      for (let i = 0; i < src.length; i += 3) {
        const p = align(src[i], src[i + 1], src[i + 2]);
        out[i] = p[0];
        out[i + 1] = p[1];
        out[i + 2] = p[2];
      }
      pos.setArray(out);
      const nrm = prim.getAttribute("NORMAL");
      if (nrm) {
        const na = nrm.getArray();
        const no = new Float32Array(na.length);
        for (let i = 0; i < na.length; i += 3) {
          const n = rot(na[i], na[i + 1], na[i + 2]);
          no[i] = n[0];
          no[i + 1] = n[1];
          no[i + 2] = n[2];
        }
        nrm.setArray(no);
      }
    }
  }
}

function triCount(doc) {
  let tris = 0;
  for (const mesh of doc.getRoot().listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const idx = prim.getIndices();
      if (idx) tris += Math.floor(idx.getCount() / 3);
      else {
        const pos = prim.getAttribute("POSITION");
        if (pos) tris += Math.floor(pos.getCount() / 3);
      }
    }
  }
  return tris;
}

function isNerveName(name) {
  if (/nucleus/i.test(name)) return false;
  return NERVE_RE.test(name);
}

/** Distal hand/foot vessels stay full-resolution. Height is still Z-Anatomy Y-up. */
function isExtremityVessel(name, centroidY, absX) {
  const n = name.toLowerCase();
  if (/digital|plantar arch|dorsalis pedis|arcuate artery|princeps pollicis|princeps hallucis|deep palmar|superficial palmar|dorsal venous arch|proper palmar|common palmar/.test(n)) {
    return true;
  }
  if (centroidY != null && centroidY < 0.16) return true;
  if (centroidY != null && absX > 0.22 && centroidY > 0.64 && centroidY < 0.95) return true;
  return false;
}

function nodeCentroidY(node) {
  const mesh = node.getMesh();
  if (!mesh) return null;
  let sx = 0;
  let sy = 0;
  let n = 0;
  for (const prim of mesh.listPrimitives()) {
    const pos = prim.getAttribute("POSITION");
    if (!pos) continue;
    const arr = pos.getArray();
    const step = Math.max(3, Math.floor(arr.length / 300) * 3);
    for (let i = 0; i < arr.length; i += step) {
      sx += Math.abs(arr[i]);
      sy += arr[i + 1];
      n += 1;
    }
  }
  if (!n) return null;
  return { y: sy / n, absX: sx / n };
}

async function makeIO() {
  const io = new NodeIO()
    .registerExtensions(ALL_EXTENSIONS)
    .registerDependencies({
      "draco3d.decoder": await draco3d.createDecoderModule(),
      "draco3d.encoder": await draco3d.createEncoderModule(),
    });
  return io;
}

async function writeDoc(io, doc, filename) {
  await doc.transform(
    prune(),
    draco({
      method: "edgebreaker",
      encodeSpeed: 5,
      quantizationBits: { POSITION: 16, NORMAL: 10, TEX_COORD: 12, COLOR: 8, GENERIC: 12 },
    }),
  );
  const file = path.join(OUT, filename);
  await io.write(file, doc);
  const bytes = fs.statSync(file).size;
  console.log(`WROTE ${filename} bytes=${bytes} tris=${triCount(doc)} nodes=${doc.getRoot().listNodes().length}`);
  return { file: filename, bytes, triangles: triCount(doc), nodes: doc.getRoot().listNodes().length };
}

function collectBounds(doc, file) {
  const rows = [];
  for (const node of doc.getRoot().listNodes()) {
    const mesh = node.getMesh();
    const name = node.getName() || "";
    if (!mesh || !name) continue;
    let min = [Infinity, Infinity, Infinity];
    let max = [-Infinity, -Infinity, -Infinity];
    let tris = 0;
    for (const prim of mesh.listPrimitives()) {
      const pos = prim.getAttribute("POSITION");
      if (!pos) continue;
      const arr = pos.getArray();
      for (let i = 0; i < arr.length; i += 3) {
        const x = arr[i];
        const y = arr[i + 1];
        const z = arr[i + 2];
        if (x < min[0]) min[0] = x;
        if (y < min[1]) min[1] = y;
        if (z < min[2]) min[2] = z;
        if (x > max[0]) max[0] = x;
        if (y > max[1]) max[1] = y;
        if (z > max[2]) max[2] = z;
      }
      const idx = prim.getIndices();
      tris += idx ? Math.floor(idx.getCount() / 3) : Math.floor(pos.getCount() / 3);
    }
    if (!Number.isFinite(min[0])) continue;
    rows.push({
      file,
      node: name,
      min: min.map((v) => Math.round(v * 1e5) / 1e5),
      max: max.map((v) => Math.round(v * 1e5) / 1e5),
      centroid: min.map((v, i) => Math.round(((v + max[i]) / 2) * 1e5) / 1e5),
      triangles: tris,
    });
  }
  return rows;
}

function dropNodes(doc, predicate) {
  for (const node of [...doc.getRoot().listNodes()]) {
    const name = node.getName() || "";
    if (predicate(name, node)) node.dispose();
  }
}

async function main() {
  await MeshoptSimplifier.ready;
  fs.mkdirSync(OUT, { recursive: true });
  const io = await makeIO();
  const report = [];
  const bounds = [];

  const plain = [
    ["squelette.glb", "squelette.glb"],
    ["muscles.glb", "muscles.glb"],
    ["fascias.glb", "fascias.glb"],
    ["ligaments.glb", "ligaments.glb"],
    ["organes.glb", "organes.glb"],
  ];
  for (const [srcName, outName] of plain) {
    console.log("READ", srcName);
    const doc = await io.read(path.join(SRC, srcName));
    const before = triCount(doc);
    transformDoc(doc);
    const meta = await writeDoc(io, doc, outName);
    meta.trianglesBefore = before;
    report.push(meta);
    bounds.push(...collectBounds(doc, outName.replace(".glb", "")));
  }

  console.log("READ nerfs.glb");
  const nervesSrc = await io.read(path.join(SRC, "nerfs.glb"));
  const nerveDoc = nervesSrc;
  const cnsDoc = await io.read(path.join(SRC, "nerfs.glb"));
  dropNodes(nerveDoc, (name) => !isNerveName(name));
  dropNodes(cnsDoc, (name) => isNerveName(name));
  const nerveBefore = triCount(nerveDoc);
  const cnsBefore = triCount(cnsDoc);
  transformDoc(nerveDoc);
  transformDoc(cnsDoc);
  console.log(`SIMPLIFY cns before=${cnsBefore}`);
  await cnsDoc.transform(
    simplify({ simplifier: MeshoptSimplifier, ratio: 0.62, error: 0.002, lockBorder: false }),
  );
  report.push({ ...(await writeDoc(io, nerveDoc, "nerfs.glb")), trianglesBefore: nerveBefore });
  bounds.push(...collectBounds(nerveDoc, "nerfs"));
  report.push({ ...(await writeDoc(io, cnsDoc, "organes-snc.glb")), trianglesBefore: cnsBefore });
  bounds.push(...collectBounds(cnsDoc, "organes-snc"));

  console.log("READ vaisseaux.glb");
  const vesselsFull = await io.read(path.join(SRC, "vaisseaux.glb"));
  const vesselsBody = await io.read(path.join(SRC, "vaisseaux.glb"));
  const extremityNames = new Set();
  for (const node of vesselsFull.getRoot().listNodes()) {
    const name = node.getName() || "";
    const c = nodeCentroidY(node);
    if (name && isExtremityVessel(name, c?.y ?? null, c?.absX ?? 0)) extremityNames.add(name);
  }
  console.log("extremity vessels", extremityNames.size);
  dropNodes(vesselsFull, (name) => !extremityNames.has(name));
  dropNodes(vesselsBody, (name) => extremityNames.has(name));
  const extBefore = triCount(vesselsFull);
  const bodyBefore = triCount(vesselsBody);
  transformDoc(vesselsFull);
  transformDoc(vesselsBody);
  console.log(`SIMPLIFY vessels body before=${bodyBefore}`);
  await vesselsBody.transform(
    simplify({ simplifier: MeshoptSimplifier, ratio: 0.5, error: 0.003, lockBorder: false }),
  );
  report.push({ ...(await writeDoc(io, vesselsFull, "vaisseaux-extremites.glb")), trianglesBefore: extBefore });
  bounds.push(...collectBounds(vesselsFull, "vaisseaux-extremites"));
  report.push({ ...(await writeDoc(io, vesselsBody, "vaisseaux.glb")), trianglesBefore: bodyBefore });
  bounds.push(...collectBounds(vesselsBody, "vaisseaux"));

  const summary = {
    alignment: { pivot: PIVOT, target: TARGET, scale: SCALE, pitchDegAboutX: 4 },
    files: report,
    triangles: report.reduce((s, r) => s + r.triangles, 0),
    bytes: report.reduce((s, r) => s + r.bytes, 0),
  };
  fs.writeFileSync(path.join(OUT, "build-report.json"), JSON.stringify(summary, null, 2));
  fs.writeFileSync("/tmp/za_bounds.json", JSON.stringify(bounds));
  console.log("SUMMARY", JSON.stringify(summary, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
