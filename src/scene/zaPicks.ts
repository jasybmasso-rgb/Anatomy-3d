import type * as THREE from "three";
import type { StructureKind } from "../types/structure";
import { setPickMeshes } from "./structurePick";

const byKind = new Map<StructureKind, Map<string, THREE.Mesh[]>>();

/** Several GLBs can feed one Couches layer. Merge their pick meshes. */
export function setZaFilePicks(kind: StructureKind, file: string, meshes: THREE.Mesh[]) {
  let files = byKind.get(kind);
  if (!files) {
    files = new Map();
    byKind.set(kind, files);
  }
  files.set(file, meshes);
  const all: THREE.Mesh[] = [];
  for (const list of files.values()) all.push(...list);
  setPickMeshes(kind, all);
}

export function clearZaFilePicks(kind: StructureKind, file: string) {
  const files = byKind.get(kind);
  if (!files) return;
  files.delete(file);
  const all: THREE.Mesh[] = [];
  for (const list of files.values()) all.push(...list);
  setPickMeshes(kind, all);
}
