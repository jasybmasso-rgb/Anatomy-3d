import type { StructureKind } from "../types/structure";

type ApplyFn = (selected: boolean) => void;

const registry = new Map<string, ApplyFn>();
let currentKey: string | null = null;
let invalidateFrame: (() => void) | null = null;

function keyOf(kind: StructureKind, id: string) {
  return `${kind}:${id}`;
}

export function setHighlightInvalidate(fn: (() => void) | null) {
  invalidateFrame = fn;
}

export function registerHighlight(kind: StructureKind, id: string, apply: ApplyFn) {
  registry.set(keyOf(kind, id), apply);
  if (currentKey === keyOf(kind, id)) apply(true);
}

export function unregisterHighlight(kind: StructureKind, id: string) {
  registry.delete(keyOf(kind, id));
}

/** Paint the pick highlight on the GPU immediately — do not wait on React or the camera. */
export function applyImmediateHighlight(kind: StructureKind, id: string) {
  const next = keyOf(kind, id);
  if (currentKey && currentKey !== next) {
    registry.get(currentKey)?.(false);
  }
  currentKey = next;
  registry.get(next)?.(true);
  invalidateFrame?.();
}

export function clearImmediateHighlight() {
  if (currentKey) registry.get(currentKey)?.(false);
  currentKey = null;
  invalidateFrame?.();
}

export function currentHighlightKey() {
  return currentKey;
}
