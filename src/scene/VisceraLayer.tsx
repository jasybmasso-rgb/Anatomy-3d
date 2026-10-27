import { useGLTF } from "@react-three/drei";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import type { VisceraPart } from "../types/structure";
import { attachFatRaycast } from "./fatRaycast";
import { registerHighlight, unregisterHighlight } from "./selectionHighlight";
import { setPickMeshes } from "./structurePick";
import { tintForStructureId } from "../data/chains";
import { getDeviceProfile } from "./deviceProfile";

const ORGAN_TONE: Record<string, string> = {
  kidney: "#a84840",
  spleen: "#963034",
  gut: "#c47658",
  gland: "#d6b084",
  liver: "#84342a",
  heart: "#9c2428",
  lung: "#d69a9a",
  brain: "#e8c4ba",
  default: "#c48c78",
};

function visceraColor(part: VisceraPart): string {
  if (part.kind === "nerve") return "#f6d648";
  if (part.kind === "vessel") return part.vesselKind === "vein" ? "#2a4aa8" : "#bc2a2a";
  return ORGAN_TONE[part.organTone ?? "default"] ?? ORGAN_TONE.default;
}

function createVisceraMaterial(part: VisceraPart): THREE.MeshStandardMaterial {
  const nerve = part.kind === "nerve";
  const vessel = part.kind === "vessel";
  const physical = getDeviceProfile().physicalMaterials;
  const opts = {
    color: visceraColor(part),
    roughness: nerve ? 0.38 : vessel ? 0.32 : 0.48,
    metalness: vessel ? 0.08 : 0.02,
    side: nerve || vessel ? THREE.DoubleSide : THREE.FrontSide,
    transparent: part.kind === "organ",
    opacity: part.kind === "organ" ? 0.92 : 1,
    depthWrite: part.kind !== "organ",
  } as const;
  if (physical) {
    return new THREE.MeshPhysicalMaterial({
      ...opts,
      clearcoat: nerve ? 0.22 : 0.08,
      sheen: nerve ? 0.45 : 0,
      sheenColor: new THREE.Color(nerve ? "#fff6b8" : "#000000"),
    });
  }
  return new THREE.MeshStandardMaterial(opts);
}

const NERVE_HIGHLIGHT = 0x3dfff2;

function paintNerveHighlight(material: THREE.MeshStandardMaterial, selected: boolean) {
  const physical = material as THREE.MeshPhysicalMaterial;
  const hasSheen = "sheen" in material;
  if (selected) {
    if (material.color.getHex() !== NERVE_HIGHLIGHT) {
      material.userData.restColor = material.color.getHex();
      if (hasSheen) {
        material.userData.restSheen = physical.sheen;
        material.userData.restSheenColor = physical.sheenColor.getHex();
      }
    }
    material.color.set(NERVE_HIGHLIGHT);
    material.emissive.set("#00ffe8");
    material.emissiveIntensity = 1.15;
    if (hasSheen) {
      physical.sheen = 0.2;
      physical.sheenColor.set("#d8fffb");
    }
  } else {
    if (material.color.getHex() === NERVE_HIGHLIGHT && material.userData.restColor != null) {
      material.color.set(material.userData.restColor as number);
    }
    material.emissive.set("#000000");
    material.emissiveIntensity = 0;
    if (hasSheen && material.userData.restSheenColor != null) {
      physical.sheen = (material.userData.restSheen as number) ?? 0.45;
      physical.sheenColor.set(material.userData.restSheenColor as number);
    }
  }
  if ("clearcoat" in material) {
    physical.clearcoat = selected ? 0.35 : material.userData.baseClearcoat ?? 0.08;
  }
}

function setSelected(
  material: THREE.MeshStandardMaterial,
  selected: boolean,
  kind: "nerve" | "organ" | "vessel",
) {
  if (kind === "nerve") {
    paintNerveHighlight(material, selected);
    return;
  }
  material.emissive.set(selected ? "#ffcc66" : "#000000");
  material.emissiveIntensity = selected ? 0.38 : 0;
  if ("clearcoat" in material) {
    (material as THREE.MeshPhysicalMaterial).clearcoat = selected
      ? 0.28
      : material.userData.baseClearcoat ?? 0.08;
  }
}

type VisceraLayerProps = {
  url: string;
  parts: VisceraPart[];
  kind: "nerve" | "organ" | "vessel";
  visible: boolean;
  chainLayerOn?: boolean;
  activeChainIds?: string[];
  selectedId: string | null;
  hiddenIds: string[];
};

export function VisceraLayer({
  url,
  parts,
  kind,
  visible,
  chainLayerOn = false,
  activeChainIds = [],
  selectedId,
  hiddenIds,
}: VisceraLayerProps) {
  const gltf = useGLTF(url);
  const entries = useMemo(() => {
    const list: { id: string; object: THREE.Object3D; material: THREE.MeshStandardMaterial; meshes: THREE.Mesh[] }[] =
      [];
    for (const part of parts) {
      const src = gltf.scene.getObjectByName(part.id);
      if (!src) continue;
      const clone = src.clone(true);
      const material = createVisceraMaterial(part);
      material.userData.baseColor = material.color.getHex();
      material.userData.baseClearcoat =
        "clearcoat" in material ? (material as THREE.MeshPhysicalMaterial).clearcoat : 0.08;
      const meshes: THREE.Mesh[] = [];
      clone.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh)) return;
        obj.geometry = obj.geometry.clone();
        if (!obj.geometry.getAttribute("normal")) obj.geometry.computeVertexNormals();
        obj.userData.pick = kind;
        obj.userData.structureId = part.id;
        attachFatRaycast(obj, kind);
        obj.castShadow = false;
        obj.receiveShadow = false;
        obj.material = material;
        obj.renderOrder = kind === "nerve" ? 7 : kind === "vessel" ? 6 : 4;
        meshes.push(obj);
      });
      clone.visible = false;
      list.push({ id: part.id, object: clone, material, meshes });
    }
    return list;
  }, [gltf, parts, kind]);

  useEffect(() => {
    for (const entry of entries) {
      registerHighlight(kind, entry.id, (selected) => setSelected(entry.material, selected, kind));
    }
    return () => {
      for (const entry of entries) unregisterHighlight(kind, entry.id);
    };
  }, [entries, kind]);

  useEffect(() => {
    const hidden = new Set(hiddenIds);
    const pick: THREE.Mesh[] = [];
    for (const entry of entries) {
      const tint = chainLayerOn ? tintForStructureId(entry.id, activeChainIds) : null;
      const on = !hidden.has(entry.id) && (visible || Boolean(tint));
      entry.object.visible = on;
      const base = entry.material.userData.baseColor as number | undefined;
      entry.material.color.set(tint ?? base ?? entry.material.color);
      setSelected(entry.material, on && entry.id === selectedId, kind);
      if (on) pick.push(...entry.meshes);
    }
    setPickMeshes(kind, pick);
    return () => setPickMeshes(kind, []);
  }, [activeChainIds, chainLayerOn, entries, hiddenIds, kind, selectedId, visible]);

  return (
    <group name={`${kind}s`} visible={visible || chainLayerOn}>
      {entries.map((entry) => (
        <primitive key={entry.id} object={entry.object} />
      ))}
    </group>
  );
}

