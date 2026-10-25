import { useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { chainClipSide, matchesChainSide, tintForStructureId, type ChainSide } from "../data/chains";
import { zaPartsForFile, type ZaPart } from "../data/zanatomy";
import type { StructureKind } from "../types/structure";
import { getDeviceProfile } from "./deviceProfile";
import { clipPlanesForSide } from "./fiberMaterial";
import { attachFatRaycast } from "./fatRaycast";
import { registerHighlight, unregisterHighlight } from "./selectionHighlight";
import { DRACO_DECODER_PATH } from "./zanatomyAbdo";
import { clearZaFilePicks, setZaFilePicks } from "./zaPicks";

const RENDER_ORDER: Record<StructureKind, number> = {
  bone: 0,
  fascia: 2,
  organ: 3,
  muscle: 4,
  ligament: 5,
  vessel: 6,
  nerve: 7,
};

type Entry = {
  part: ZaPart;
  material: THREE.MeshStandardMaterial;
  meshes: THREE.Mesh[];
};

function styleFor(part: ZaPart): {
  color: string;
  opacity: number;
  transparent: boolean;
  side: THREE.Side;
  roughness: number;
} {
  if (part.kind === "bone") {
    if (part.tissue === "cartilage") {
      return { color: "#b9d4e4", opacity: 0.72, transparent: true, side: THREE.DoubleSide, roughness: 0.28 };
    }
    return { color: "#f0e4d0", opacity: 1, transparent: false, side: THREE.FrontSide, roughness: 0.48 };
  }
  if (part.kind === "muscle") {
    return { color: "#c4473a", opacity: 1, transparent: false, side: THREE.DoubleSide, roughness: 0.55 };
  }
  if (part.kind === "fascia") {
    return { color: "#8eabbe", opacity: 0.55, transparent: true, side: THREE.DoubleSide, roughness: 0.5 };
  }
  if (part.kind === "ligament") {
    return { color: "#d9c7a2", opacity: 1, transparent: false, side: THREE.DoubleSide, roughness: 0.46 };
  }
  if (part.kind === "nerve") {
    return { color: "#f6d648", opacity: 1, transparent: false, side: THREE.DoubleSide, roughness: 0.38 };
  }
  if (part.kind === "vessel") {
    const vein = part.vesselKind === "vein";
    return {
      color: vein ? "#2a4aa8" : "#bc2a2a",
      opacity: 1,
      transparent: false,
      side: THREE.DoubleSide,
      roughness: 0.34,
    };
  }
  return { color: "#c48c78", opacity: 0.94, transparent: true, side: THREE.FrontSide, roughness: 0.5 };
}

function createMaterial(part: ZaPart): THREE.MeshStandardMaterial {
  const style = styleFor(part);
  const material = new THREE.MeshStandardMaterial({
    color: style.color,
    roughness: style.roughness,
    metalness: part.kind === "vessel" ? 0.06 : 0.02,
    transparent: style.transparent,
    opacity: style.opacity,
    depthWrite: !style.transparent,
    side: style.side,
    clippingPlanes: [],
  });
  material.userData.baseColor = new THREE.Color(style.color);
  material.userData.baseOpacity = style.opacity;
  return material;
}

function paint(material: THREE.MeshStandardMaterial, tintHex: string | null, selected: boolean) {
  const base = material.userData.baseColor as THREE.Color;
  const opacity = material.userData.baseOpacity as number;
  if (tintHex) {
    material.color.set(tintHex);
    material.emissive.set(tintHex);
    material.emissiveIntensity = selected ? 0.5 : 0.28;
  } else {
    material.color.copy(base);
    material.emissive.set(selected ? "#ffcc66" : "#000000");
    material.emissiveIntensity = selected ? 0.38 : 0;
  }
  material.opacity = opacity;
}

function meshTriangles(mesh: THREE.Mesh): number {
  const geo = mesh.geometry;
  if (geo.index) return geo.index.count / 3;
  const pos = geo.getAttribute("position");
  return pos ? pos.count / 3 : 0;
}

export type ZAnatomyFileProps = {
  url: string;
  file: string;
  layerVisible: boolean;
  /** Muscles stay hidden until “afficher tous”, a selection, or a chain. Bones ignore this. */
  showAll: boolean;
  selectedId: string | null;
  pinnedId: string | null;
  hiddenIds: string[];
  chainLayerOn: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
};

export function ZAnatomyFile({
  url,
  file,
  layerVisible,
  showAll,
  selectedId,
  pinnedId,
  hiddenIds,
  chainLayerOn,
  activeChainIds,
  chainSide,
}: ZAnatomyFileProps) {
  const gltf = useGLTF(url, DRACO_DECODER_PATH);
  const entries = useMemo(() => {
    const byNode = new Map<string, ZaPart>();
    for (const part of zaPartsForFile(file)) {
      for (const node of part.nodes) {
        byNode.set(node, part);
        // Three.js PropertyBinding.sanitizeNodeName: spaces → _, drop . : / [ ]
        byNode.set(node.replace(/\s/g, "_").replace(/[[\].:/]/g, ""), part);
      }
    }
    const grouped = new Map<string, Entry>();
    const partFor = (obj: THREE.Object3D): ZaPart | undefined => {
      let current: THREE.Object3D | null = obj;
      while (current) {
        const hit = byNode.get(current.name);
        if (hit) return hit;
        current = current.parent;
      }
      return undefined;
    };
    gltf.scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      const part = partFor(obj);
      if (!part) return;
      let entry = grouped.get(part.id);
      if (!entry) {
        entry = { part, material: createMaterial(part), meshes: [] };
        grouped.set(part.id, entry);
      }
      const geometry = obj.geometry;
      if (!geometry.getAttribute("normal")) geometry.computeVertexNormals();
      obj.material = entry.material;
      obj.userData.pick = part.kind;
      obj.userData.structureId = part.id;
      if (part.kind === "muscle") obj.userData.muscleId = part.id;
      obj.castShadow = part.kind === "bone" && getDeviceProfile().shadows;
      obj.receiveShadow = part.kind === "bone" && getDeviceProfile().shadows;
      obj.renderOrder = RENDER_ORDER[part.kind];
      obj.frustumCulled = true;
      const tris = meshTriangles(obj);
      const thin = part.kind === "nerve" || part.kind === "vessel" || part.kind === "ligament";
      if (thin && tris > 0 && tris < 4000) attachFatRaycast(obj, part.kind);
      else obj.raycast = THREE.Mesh.prototype.raycast;
      entry.meshes.push(obj);
    });
    return [...grouped.values()];
  }, [file, gltf]);

  useEffect(() => {
    for (const entry of entries) {
      registerHighlight(entry.part.kind, entry.part.id, (selected) => {
        paint(entry.material, null, selected);
      });
    }
    return () => {
      for (const entry of entries) unregisterHighlight(entry.part.kind, entry.part.id);
    };
  }, [entries]);

  useEffect(() => {
    const hidden = new Set(hiddenIds);
    const chainOn = chainLayerOn && activeChainIds.length > 0;
    const pick: THREE.Mesh[] = [];
    const profile = getDeviceProfile();
    for (const entry of entries) {
      const part = entry.part;
      const forced = part.id === selectedId || part.id === pinnedId;
      const tintHex = chainOn ? tintForStructureId(part.id, activeChainIds) : null;
      const inChain = Boolean(tintHex);
      let on = !hidden.has(part.id);
      if (part.kind === "bone") {
        on = on && layerVisible;
      } else if (part.kind === "muscle") {
        const listed = layerVisible && (showAll || forced);
        on = on && (listed || inChain);
      } else {
        on = on && (layerVisible || inChain);
      }
      if (
        chainOn &&
        !forced &&
        (part.kind === "muscle" || part.kind === "fascia" || part.kind === "ligament") &&
        !matchesChainSide(part.id, chainSide)
      ) {
        on = false;
      }
      for (const mesh of entry.meshes) {
        mesh.visible = on;
        mesh.userData.wantVisible = on;
      }
      if (!on) continue;
      paint(entry.material, tintHex, part.id === selectedId);
      const clip =
        chainOn && part.kind === "muscle" && part.bilateral
          ? chainClipSide(part.id, chainSide, activeChainIds)
          : "both";
      entry.material.clippingPlanes = clipPlanesForSide(clip);
      for (const mesh of entry.meshes) {
        mesh.renderOrder = part.id === selectedId ? 12 : RENDER_ORDER[part.kind];
        mesh.castShadow = part.kind === "bone" && profile.shadows;
      }
      pick.push(...entry.meshes);
    }
    setZaFilePicks(entries[0]?.part.kind ?? "bone", file, pick);
    return () => clearZaFilePicks(entries[0]?.part.kind ?? "bone", file);
  }, [
    activeChainIds,
    chainLayerOn,
    chainSide,
    entries,
    file,
    hiddenIds,
    layerVisible,
    pinnedId,
    selectedId,
    showAll,
  ]);

  const tick = useRef(0);
  useFrame(({ camera }) => {
    if (!getDeviceProfile().lowEnd) return;
    tick.current += 1;
    if (tick.current % 12 !== 0) return;
    const center = new THREE.Vector3();
    for (const entry of entries) {
      if (entry.part.id === selectedId) continue;
      for (const mesh of entry.meshes) {
        if (!mesh.userData.wantVisible) continue;
        const geo = mesh.geometry;
        if (!geo.boundingSphere) geo.computeBoundingSphere();
        const sphere = geo.boundingSphere;
        if (!sphere) continue;
        center.copy(sphere.center);
        mesh.localToWorld(center);
        const dist = camera.position.distanceTo(center);
        const tiny = meshTriangles(mesh) < 900;
        mesh.visible = !(tiny && dist > 1.15);
      }
    }
  });

  useEffect(() => {
    return () => {
      for (const entry of entries) entry.material.dispose();
    };
  }, [entries]);

  return <primitive object={gltf.scene} />;
}
