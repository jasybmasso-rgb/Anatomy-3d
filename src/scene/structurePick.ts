import { useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import type { StructureKind } from "../types/structure";
import { applyImmediateHighlight, setHighlightInvalidate } from "./selectionHighlight";

export type PickHit = {
  kind: StructureKind;
  id: string;
  distance: number;
};

const buckets = new Map<StructureKind, THREE.Mesh[]>();

/** When hits sit almost on top of each other, prefer thin catalog layers. */
const KIND_BIAS: Record<StructureKind, number> = {
  ligament: -0.014,
  nerve: -0.012,
  vessel: -0.010,
  fascia: -0.007,
  organ: 0,
  muscle: 0.005,
};

const RESIDUAL_VESSEL = new Set(["arbre-arteriel", "arbre-veineux"]);

export function setPickMeshes(kind: StructureKind, meshes: THREE.Mesh[]) {
  buckets.set(kind, meshes);
}

function clippingPlanesOf(obj: THREE.Object3D): THREE.Plane[] {
  if (!(obj instanceof THREE.Mesh)) return [];
  const mat = obj.material;
  if (!mat || Array.isArray(mat)) return [];
  return (mat.clippingPlanes as THREE.Plane[] | null) ?? [];
}

function isHitClipped(hit: THREE.Intersection): boolean {
  for (const plane of clippingPlanesOf(hit.object)) {
    if (plane.distanceToPoint(hit.point) < 0) return true;
  }
  return false;
}

export function collectStructureHits(raycaster: THREE.Raycaster): PickHit[] {
  const hits: PickHit[] = [];
  for (const [kind, meshes] of buckets) {
    if (meshes.length === 0) continue;
    for (const hit of raycaster.intersectObjects(meshes, false)) {
      if (isHitClipped(hit)) continue;
      const id = (hit.object.userData.structureId ?? hit.object.userData.muscleId) as unknown;
      if (typeof id !== "string") continue;
      hits.push({ kind, id, distance: hit.distance });
    }
  }
  hits.sort((a, b) => {
    const pa = a.distance + KIND_BIAS[a.kind] + (RESIDUAL_VESSEL.has(a.id) ? 0.02 : 0);
    const pb = b.distance + KIND_BIAS[b.kind] + (RESIDUAL_VESSEL.has(b.id) ? 0.02 : 0);
    return pa - pb;
  });
  const unique: PickHit[] = [];
  for (const hit of hits) {
    if (unique.some((row) => row.kind === hit.kind && row.id === hit.id)) continue;
    unique.push(hit);
  }
  return unique;
}

const CLICK_PX = 10;
const CYCLE_PX = 14;

type StructurePickProps = {
  onSelect: (kind: StructureKind, id: string) => void;
};

export function StructurePick({ onSelect }: StructurePickProps) {
  const { camera, gl, invalidate } = useThree();
  const raycaster = useMemo(() => new THREE.Raycaster(), []);
  const pointer = useMemo(() => new THREE.Vector2(), []);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const lastClick = useRef<{ x: number; y: number; keys: string[]; index: number } | null>(null);

  useEffect(() => {
    setHighlightInvalidate(() => invalidate());
    return () => setHighlightInvalidate(null);
  }, [invalidate]);

  useEffect(() => {
    const element = gl.domElement;
    let down: { x: number; y: number } | null = null;
    let activePointers = 0;
    let multiTouch = false;

    const onPointerDown = (event: PointerEvent) => {
      activePointers += 1;
      if (activePointers > 1) {
        multiTouch = true;
        down = null;
        return;
      }
      if (event.button !== 0) return;
      down = { x: event.clientX, y: event.clientY };
    };

    const onPointerUp = (event: PointerEvent) => {
      activePointers = Math.max(0, activePointers - 1);
      if (multiTouch) {
        if (activePointers === 0) multiTouch = false;
        down = null;
        return;
      }
      if (!down || event.button !== 0) return;
      const dx = event.clientX - down.x;
      const dy = event.clientY - down.y;
      down = null;
      if (dx * dx + dy * dy > CLICK_PX * CLICK_PX) return;
      const rect = element.getBoundingClientRect();
      const w = Math.max(rect.width, 1);
      const h = Math.max(rect.height, 1);
      pointer.set(((event.clientX - rect.left) / w) * 2 - 1, -((event.clientY - rect.top) / h) * 2 + 1);
      raycaster.setFromCamera(pointer, camera);
      const hits = collectStructureHits(raycaster);
      if (hits.length === 0) return;
      const keys = hits.map((hit) => `${hit.kind}:${hit.id}`);
      const prev = lastClick.current;
      const near =
        prev !== null && (event.clientX - prev.x) ** 2 + (event.clientY - prev.y) ** 2 <= CYCLE_PX * CYCLE_PX;
      const sameStack = near && prev !== null && prev.keys.length === keys.length && prev.keys.every((k, i) => k === keys[i]);
      const index = sameStack && prev ? (prev.index + 1) % keys.length : 0;
      lastClick.current = { x: event.clientX, y: event.clientY, keys, index };
      const chosen = hits[index];
      applyImmediateHighlight(chosen.kind, chosen.id);
      onSelectRef.current(chosen.kind, chosen.id);
    };

    element.addEventListener("pointerdown", onPointerDown);
    element.addEventListener("pointerup", onPointerUp);
    element.addEventListener("pointercancel", onPointerUp);
    return () => {
      element.removeEventListener("pointerdown", onPointerDown);
      element.removeEventListener("pointerup", onPointerUp);
      element.removeEventListener("pointercancel", onPointerUp);
    };
  }, [camera, gl, pointer, raycaster]);

  return null;
}
