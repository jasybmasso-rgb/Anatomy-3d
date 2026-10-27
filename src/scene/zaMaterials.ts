import * as THREE from "three";
import type { ChainSide } from "../data/chains";
import type { ZaPart } from "../data/zanatomy";

/**
 * One material per look (tissue, chain tint, selection, clip).
 * Thousands of anatomical parts share a few dozen programs instead of a material each.
 */
const pool = new Map<string, THREE.MeshStandardMaterial>();

const CLIP_PLANES: Record<ChainSide, THREE.Plane[]> = {
  both: [],
  left: [new THREE.Plane(new THREE.Vector3(1, 0, 0), 0.01)],
  right: [new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0.01)],
};

type Look = {
  color: string;
  opacity: number;
  transparent: boolean;
  side: THREE.Side;
  roughness: number;
  metalness: number;
};

const LOOK: Record<string, Look> = {
  bone: { color: "#f0e4d0", opacity: 1, transparent: false, side: THREE.FrontSide, roughness: 0.48, metalness: 0.02 },
  cartilage: { color: "#b9d4e4", opacity: 0.72, transparent: true, side: THREE.DoubleSide, roughness: 0.28, metalness: 0.02 },
  muscle: { color: "#c4473a", opacity: 1, transparent: false, side: THREE.DoubleSide, roughness: 0.55, metalness: 0.02 },
  fascia: { color: "#8eabbe", opacity: 0.55, transparent: true, side: THREE.DoubleSide, roughness: 0.5, metalness: 0.02 },
  // Darker tan than bone (#f0e4d0) so the bands stay readable against the skeleton.
  ligament: { color: "#9a7344", opacity: 1, transparent: false, side: THREE.DoubleSide, roughness: 0.46, metalness: 0.02 },
  nerve: { color: "#f6d648", opacity: 1, transparent: false, side: THREE.DoubleSide, roughness: 0.38, metalness: 0.02 },
  artery: { color: "#bc2a2a", opacity: 1, transparent: false, side: THREE.DoubleSide, roughness: 0.34, metalness: 0.06 },
  vein: { color: "#2a4aa8", opacity: 1, transparent: false, side: THREE.DoubleSide, roughness: 0.34, metalness: 0.06 },
  organ: { color: "#c48c78", opacity: 0.94, transparent: true, side: THREE.FrontSide, roughness: 0.5, metalness: 0.02 },
};

function lookKey(part: ZaPart): string {
  if (part.kind === "bone") return part.tissue === "cartilage" ? "cartilage" : "bone";
  if (part.kind === "vessel") return part.vesselKind === "vein" ? "vein" : "artery";
  return part.kind;
}

export function zaMaterial(
  part: ZaPart,
  tint: string | null,
  selected: boolean,
  clip: ChainSide,
): THREE.MeshStandardMaterial {
  const lookId = lookKey(part);
  const key = `${lookId}|${tint ?? ""}|${selected ? 1 : 0}|${clip}`;
  const cached = pool.get(key);
  if (cached) return cached;
  const look = LOOK[lookId] ?? LOOK.organ;
  // Gold emissive sits on the yellow nerve and disappears. Cyan wins over a chain tint.
  const nerveSelected = selected && lookId === "nerve";
  const material = new THREE.MeshStandardMaterial({
    color: nerveSelected ? "#3dfff2" : (tint ?? look.color),
    roughness: look.roughness,
    metalness: look.metalness,
    transparent: look.transparent,
    opacity: look.opacity,
    depthWrite: !look.transparent,
    side: look.side,
    clippingPlanes: CLIP_PLANES[clip],
    clipShadows: clip !== "both",
  });
  if (nerveSelected) {
    material.emissive.set("#00ffe8");
    material.emissiveIntensity = 1.15;
  } else if (tint) {
    material.emissive.set(tint);
    material.emissiveIntensity = selected ? 0.5 : 0.28;
  } else if (selected) {
    material.emissive.set("#ffcc66");
    material.emissiveIntensity = 0.38;
  }
  pool.set(key, material);
  return material;
}
