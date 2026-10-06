/**
 * Draco and meshopt sizes for every GLB in models/.
 * Writes models/compressed/ and merges metrics.compression.
 */
import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { NodeIO } from "@gltf-transform/core";
import { KHRDracoMeshCompression, EXTMeshoptCompression } from "@gltf-transform/extensions";
import { cloneDocument, draco, meshopt } from "@gltf-transform/functions";
import draco3d from "draco3dgltf";
import { MeshoptEncoder } from "meshoptimizer";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MODELS = path.join(ROOT, "models");
const OUT = path.join(MODELS, "compressed");
await mkdir(OUT, { recursive: true });
await MeshoptEncoder.ready;

const io = new NodeIO()
  .registerExtensions([KHRDracoMeshCompression, EXTMeshoptCompression])
  .registerDependencies({
    "draco3d.encoder": await draco3d.createEncoderModule(),
    "draco3d.decoder": await draco3d.createDecoderModule(),
    "meshopt.encoder": MeshoptEncoder,
  });

const files = (await readdir(MODELS)).filter((name) => name.endsWith(".glb")).sort();
const rows = [];
for (const name of files) {
  const src = path.join(MODELS, name);
  const raw = (await readFile(src)).length;
  const document = await io.read(src);
  const dracoDoc = cloneDocument(document);
  await dracoDoc.transform(draco({ method: "edgebreaker", quantizePosition: 14, quantizeNormal: 10, quantizeTexcoord: 12 }));
  const dracoPath = path.join(OUT, name.replace(/\.glb$/, ".draco.glb"));
  await io.write(dracoPath, dracoDoc);
  const dracoBytes = (await readFile(dracoPath)).length;

  const meshoptDoc = cloneDocument(document);
  await meshoptDoc.transform(meshopt({ encoder: MeshoptEncoder, level: "high" }));
  const meshoptPath = path.join(OUT, name.replace(/\.glb$/, ".meshopt.glb"));
  await io.write(meshoptPath, meshoptDoc);
  const meshoptBytes = (await readFile(meshoptPath)).length;

  const row = { file: name, rawBytes: raw, dracoBytes, meshoptBytes };
  rows.push(row);
  console.log(
    name,
    "raw",
    (raw / 1024).toFixed(0) + "K",
    "draco",
    (dracoBytes / 1024).toFixed(0) + "K",
    "meshopt",
    (meshoptBytes / 1024).toFixed(0) + "K",
  );
}

const metricsPath = path.join(ROOT, "metrics.json");
const metrics = JSON.parse(await readFile(metricsPath, "utf8"));
metrics.compression = {
  note: "Draco edgebreaker (pos 14, nrm 10, uv 12) and EXT_meshopt_compression level high, via gltf-transform. Textures stay PNG.",
  files: rows,
};
await writeFile(metricsPath, JSON.stringify(metrics, null, 2));
