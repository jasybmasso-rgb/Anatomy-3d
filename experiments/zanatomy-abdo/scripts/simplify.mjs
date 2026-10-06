/**
 * Position-weld + meshoptimizer simplification of models/original.glb.
 *
 * The glTF export splits vertices wherever normals differ, so the external
 * oblique arrived as one vertex per corner (flat). Weld is by position only;
 * smooth normals are recomputed. Triangle count of the full mesh is unchanged.
 *
 * Creases: these shells have almost no topological border. PreserveFolds tells
 * meshoptimizer to protect sharp dihedral edges (costal margin, sheet rim).
 * LockBorder keeps the rectus muscle/tendon seam from opening.
 *
 * Writes models/original.glb (welded), meshopt-25/10/05.glb and metrics.json.
 */
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Document, NodeIO } from "@gltf-transform/core";
import { compactPrimitive, dedup, prune } from "@gltf-transform/functions";
import { MeshoptSimplifier } from "meshoptimizer";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MODELS = path.join(ROOT, "models");
const SRC = path.join(MODELS, "original.glb");
const METRICS = path.join(ROOT, "metrics.json");

const RATIOS = [
  { id: "meshopt-25", ratio: 0.25 },
  { id: "meshopt-10", ratio: 0.1 },
  { id: "meshopt-05", ratio: 0.05 },
];
const ERROR_LADDER = [0.001, 0.003, 0.008, 0.02, 0.05, 0.12, 0.3, 1];
const NORMAL_WEIGHT = 0.02;

await MeshoptSimplifier.ready;

function triCount(document) {
  let n = 0;
  const perMesh = {};
  for (const mesh of document.getRoot().listMeshes()) {
    let m = 0;
    for (const prim of mesh.listPrimitives()) {
      const idx = prim.getIndices();
      if (idx) m += idx.getCount() / 3;
    }
    perMesh[mesh.getName() || "(unnamed)"] = m;
    n += m;
  }
  return { triangles: n, perMesh };
}

/** Merge vertices that share a position. Recompute area-weighted smooth normals. */
function weldByPosition(prim, tolerance = 1e-6) {
  const posAcc = prim.getAttribute("POSITION");
  const idxAcc = prim.getIndices();
  if (!posAcc || !idxAcc) return null;
  const pos = posAcc.getArray();
  const idx = idxAcc.getArray();
  const srcCount = pos.length / 3;
  const inv = 1 / tolerance;
  const buckets = new Map();
  const remap = new Uint32Array(srcCount);
  const newPos = [];
  let unique = 0;
  for (let v = 0; v < srcCount; v++) {
    const x = pos[v * 3];
    const y = pos[v * 3 + 1];
    const z = pos[v * 3 + 2];
    const key = `${Math.round(x * inv)}_${Math.round(y * inv)}_${Math.round(z * inv)}`;
    let id = buckets.get(key);
    if (id === undefined) {
      id = unique++;
      buckets.set(key, id);
      newPos.push(x, y, z);
    }
    remap[v] = id;
  }
  const kept = [];
  let dropped = 0;
  for (let i = 0; i < idx.length; i += 3) {
    const a = remap[idx[i]];
    const b = remap[idx[i + 1]];
    const c = remap[idx[i + 2]];
    if (a === b || b === c || c === a) {
      dropped++;
      continue;
    }
    kept.push(a, b, c);
  }
  const positions = new Float32Array(newPos);
  const indices = new Uint32Array(kept);
  const normals = smoothNormals(indices, positions, unique);

  const document = Document.fromGraph(prim.getGraph());
  const pAcc = document.createAccessor();
  pAcc.setType("VEC3");
  pAcc.setArray(positions);
  const nAcc = document.createAccessor();
  nAcc.setType("VEC3");
  nAcc.setArray(normals);
  const iAcc = document.createAccessor();
  iAcc.setType("SCALAR");
  iAcc.setArray(indices.length > 65535 ? indices : new Uint16Array(indices));
  prim.setAttribute("POSITION", pAcc);
  prim.setAttribute("NORMAL", nAcc);
  prim.setIndices(iAcc);
  for (const semantic of prim.listSemantics()) {
    if (semantic !== "POSITION" && semantic !== "NORMAL") prim.setAttribute(semantic, null);
  }
  return { beforeVerts: srcCount, afterVerts: unique, droppedTriangles: dropped, triangles: indices.length / 3 };
}

function smoothNormals(indices, positions, vertexCount) {
  const normals = new Float32Array(vertexCount * 3);
  for (let i = 0; i < indices.length; i += 3) {
    const a = indices[i];
    const b = indices[i + 1];
    const c = indices[i + 2];
    const ax = positions[a * 3];
    const ay = positions[a * 3 + 1];
    const az = positions[a * 3 + 2];
    const abx = positions[b * 3] - ax;
    const aby = positions[b * 3 + 1] - ay;
    const abz = positions[b * 3 + 2] - az;
    const acx = positions[c * 3] - ax;
    const acy = positions[c * 3 + 1] - ay;
    const acz = positions[c * 3 + 2] - az;
    const x = aby * acz - abz * acy;
    const y = abz * acx - abx * acz;
    const z = abx * acy - aby * acx;
    normals[a * 3] += x;
    normals[a * 3 + 1] += y;
    normals[a * 3 + 2] += z;
    normals[b * 3] += x;
    normals[b * 3 + 1] += y;
    normals[b * 3 + 2] += z;
    normals[c * 3] += x;
    normals[c * 3 + 1] += y;
    normals[c * 3 + 2] += z;
  }
  for (let v = 0; v < vertexCount; v++) {
    const x = normals[v * 3];
    const y = normals[v * 3 + 1];
    const z = normals[v * 3 + 2];
    const len = Math.hypot(x, y, z) || 1;
    normals[v * 3] = x / len;
    normals[v * 3 + 1] = y / len;
    normals[v * 3 + 2] = z / len;
  }
  return normals;
}

function simplifyPrimitive(prim, ratio) {
  const position = prim.getAttribute("POSITION");
  const normal = prim.getAttribute("NORMAL");
  const index = prim.getIndices();
  const indices = new Uint32Array(index.getArray());
  const positions = new Float32Array(position.getArray());
  const normals = new Float32Array(normal.getArray());
  const target = Math.max(3, Math.floor((indices.length * ratio) / 3) * 3);
  let chosen = null;
  for (const flags of [
    ["LockBorder", "PreserveFolds"],
    ["PreserveFolds"],
  ]) {
    for (const error of ERROR_LADDER) {
      const [dst, err] = MeshoptSimplifier.simplifyWithAttributes(
        indices,
        positions,
        3,
        normals,
        3,
        [NORMAL_WEIGHT, NORMAL_WEIGHT, NORMAL_WEIGHT],
        null,
        target,
        error,
        flags,
      );
      chosen = { dst, err, error, flags: flags.join("+") };
      if (dst.length <= target * 1.04) break;
    }
    if (chosen.dst.length <= target * 1.04) break;
  }
  const document = Document.fromGraph(prim.getGraph());
  const acc = document.createAccessor();
  acc.setType("SCALAR");
  acc.setArray(chosen.dst);
  prim.setIndices(acc);
  compactPrimitive(prim);
  return {
    before: indices.length / 3,
    after: chosen.dst.length / 3,
    target: target / 3,
    errorLimit: chosen.error,
    error: Number(chosen.err.toFixed(5)),
    flags: chosen.flags,
    verticesAfter: prim.getAttribute("POSITION").getCount(),
  };
}

function nameMeshes(document) {
  for (const node of document.getRoot().listNodes()) {
    const mesh = node.getMesh();
    if (mesh && node.getName() && !mesh.getName()) mesh.setName(node.getName());
  }
}

const io = new NodeIO();
const source = await io.read(SRC);
const rawStats = triCount(source);

const weldNotes = [];
for (const mesh of source.getRoot().listMeshes()) {
  for (const prim of mesh.listPrimitives()) {
    const note = weldByPosition(prim);
    if (!note) continue;
    weldNotes.push({ mesh: mesh.getName(), ...note });
    console.log(
      "weld",
      mesh.getName(),
      `verts ${note.beforeVerts}->${note.afterVerts}`,
      `tris ${note.triangles}`,
      `dropped ${note.droppedTriangles}`,
    );
  }
}
nameMeshes(source);
await source.transform(prune(), dedup());
const weldedStats = triCount(source);
await io.write(SRC, source);
console.log("welded original", weldedStats.triangles, "bytes", (await readFile(SRC)).length);

const results = [];
for (const level of RATIOS) {
  const document = await io.read(SRC);
  const notes = [];
  for (const mesh of document.getRoot().listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const note = simplifyPrimitive(prim, level.ratio);
      notes.push({ mesh: mesh.getName(), ...note });
      console.log(
        level.id,
        note.mesh,
        `${note.before}->${note.after}`,
        `target ${note.target}`,
        `err ${note.error} limit ${note.errorLimit}`,
        note.flags,
      );
    }
  }
  nameMeshes(document);
  await document.transform(prune(), dedup());
  const stats = triCount(document);
  const out = path.join(MODELS, `${level.id}.glb`);
  await io.write(out, document);
  const bytes = (await readFile(out)).length;
  console.log(level.id, "TOTAL", stats.triangles, `${((100 * stats.triangles) / weldedStats.triangles).toFixed(1)}%`, bytes);
  results.push({
    id: level.id,
    method: "meshoptimizer simplifyWithAttributes",
    flags: ["LockBorder", "PreserveFolds"],
    normalWeight: NORMAL_WEIGHT,
    requestedRatio: level.ratio,
    triangles: stats.triangles,
    percentOfOriginal: Number(((100 * stats.triangles) / weldedStats.triangles).toFixed(2)),
    perMesh: stats.perMesh,
    primitives: notes,
    glb: `models/${level.id}.glb`,
    glbBytes: bytes,
  });
}

const metrics = JSON.parse(await readFile(METRICS, "utf8"));
metrics.weld = {
  note: "Position weld (1e-6 m) + area-weighted smooth normals. Triangle count is the geometric count; flat split vertices were only an export artifact.",
  rawTriangles: rawStats.triangles,
  weldedTriangles: weldedStats.triangles,
  primitives: weldNotes,
  glbBytes: (await readFile(SRC)).length,
};
metrics.simplification = results;
metrics.original.glbBytes = metrics.weld.glbBytes;
metrics.original.triangles = weldedStats.triangles;
metrics.methodNote =
  "Primary decimation is meshoptimizer (LockBorder + PreserveFolds) after a position weld. " +
  "Blender Decimate collapse (no crease protection) is in metrics.decimate for comparison. " +
  "Source meshes are closed shells; the costal margin is a crease, not a border. " +
  "No UVs on the source.";
await writeFile(METRICS, JSON.stringify(metrics, null, 2));
