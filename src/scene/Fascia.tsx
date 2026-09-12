import { useGLTF } from "@react-three/drei";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import {
  fasciaIdsForChains,
  matchesChainSide,
  tintForFascia,
  type ChainSide,
} from "../data/chains";
import { fascias as catalog } from "../data/loadConnective";
import { clipPlanesForSide } from "./fiberMaterial";
import { attachFatRaycast } from "./fatRaycast";
import { registerHighlight, unregisterHighlight } from "./selectionHighlight";
import { setPickMeshes } from "./structurePick";

function materialFor(source: string) {
  const schematic = source.startsWith("synthetic");
  return new THREE.MeshPhysicalMaterial({
    color: schematic ? "#9bb6c8" : "#7f9eb5",
    emissive: new THREE.Color("#1c3344"),
    emissiveIntensity: schematic ? 0.08 : 0.16,
    roughness: 0.48,
    metalness: 0.02,
    transparent: true,
    opacity: schematic ? 0.38 : 0.58,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexColors: false,
    clippingPlanes: [],
    clipShadows: true,
  });
}

function paintFascia(
  material: THREE.MeshPhysicalMaterial,
  source: string,
  tintHex: string | null,
  selected: boolean,
) {
  const schematic = source.startsWith("synthetic");
  const tint = tintHex ? new THREE.Color(tintHex) : null;
  material.color.copy(tint ?? (schematic ? new THREE.Color("#9bb6c8") : new THREE.Color("#7f9eb5")));
  material.emissive.copy(
    selected ? new THREE.Color("#ffcc66") : tint ? tint.clone().multiplyScalar(0.25) : new THREE.Color("#1c3344"),
  );
  material.emissiveIntensity = selected ? 0.36 : tint ? 0.22 : schematic ? 0.08 : 0.16;
  material.opacity = tint ? 0.62 : schematic ? 0.38 : 0.58;
}

type FasciaProps = {
  layerVisible: boolean;
  selectedId: string | null;
  hiddenIds: string[];
  chainLayerOn: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
};

export function Fascia({
  layerVisible,
  selectedId,
  hiddenIds,
  chainLayerOn,
  activeChainIds,
  chainSide,
}: FasciaProps) {
  const gltf = useGLTF("/models/fascia.glb");
  const entries = useMemo(() => {
    const list: {
      id: string;
      object: THREE.Object3D;
      meshes: THREE.Mesh[];
      source: string;
      material: THREE.MeshPhysicalMaterial;
    }[] = [];
    const byId = new Map(catalog.map((part) => [part.id, part]));
    for (const part of catalog) {
      const src = gltf.scene.getObjectByName(part.id);
      if (!src) continue;
      const clone = src.clone(true);
      const meshes: THREE.Mesh[] = [];
      clone.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh)) return;
        const geom = obj.geometry;
        if (!geom.getAttribute("normal")) geom.computeVertexNormals();
        obj.userData.pick = "fascia";
        obj.userData.fasciaId = part.id;
        obj.userData.structureId = part.id;
        obj.userData.source = byId.get(part.id)?.source ?? "bodyparts3d";
        attachFatRaycast(obj, "fascia");
        obj.castShadow = false;
        obj.receiveShadow = false;
        obj.renderOrder = 2;
        meshes.push(obj);
      });
      const source = String(byId.get(part.id)?.source ?? "bodyparts3d");
      const material = materialFor(source);
      for (const mesh of meshes) mesh.material = material;
      clone.visible = false;
      list.push({
        id: part.id,
        object: clone,
        meshes,
        source,
        material,
      });
    }
    return list;
  }, [gltf]);

  useEffect(() => {
    for (const entry of entries) {
      registerHighlight("fascia", entry.id, (selected) => paintFascia(entry.material, entry.source, null, selected));
    }
    return () => {
      for (const entry of entries) unregisterHighlight("fascia", entry.id);
    };
  }, [entries]);

  useEffect(() => {
    const hidden = new Set(hiddenIds);
    const chainIds = chainLayerOn ? new Set(fasciaIdsForChains(activeChainIds)) : new Set<string>();
    const planes = clipPlanesForSide(chainLayerOn ? chainSide : "both");
    const pick: THREE.Mesh[] = [];
    for (const entry of entries) {
      const inChain = chainIds.has(entry.id);
      const sideOk = matchesChainSide(entry.id, chainLayerOn ? chainSide : "both");
      const on = sideOk && !hidden.has(entry.id) && (layerVisible || inChain);
      entry.object.visible = on;
      if (!on) continue;
      const tint = inChain ? tintForFascia(entry.id, activeChainIds) : null;
      paintFascia(entry.material, entry.source, tint, entry.id === selectedId);
      entry.material.clippingPlanes = planes;
      pick.push(...entry.meshes);
    }
    setPickMeshes("fascia", pick);
    return () => setPickMeshes("fascia", []);
  }, [entries, layerVisible, chainLayerOn, activeChainIds, chainSide, hiddenIds, selectedId]);

  return (
    <group name="fascias">
      {entries.map((entry) => (
        <primitive key={entry.id} object={entry.object} />
      ))}
    </group>
  );
}

