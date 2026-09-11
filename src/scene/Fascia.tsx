import { useGLTF } from "@react-three/drei";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import {
  fasciaIdsForChains,
  matchesChainSide,
  tintForFascia,
  type ChainSide,
} from "../data/chains";
import type { FasciaPart } from "../data/fascia";
import rawFascia from "../data/fascia.json";
import { clipPlanesForSide } from "./fiberMaterial";

function materialFor(source: string, tintHex?: string | null) {
  const schematic = source.startsWith("synthetic");
  const tint = tintHex ? new THREE.Color(tintHex) : null;
  return new THREE.MeshPhysicalMaterial({
    color: tint ?? (schematic ? "#9bb6c8" : "#7f9eb5"),
    emissive: tint ? tint.clone().multiplyScalar(0.25) : new THREE.Color("#1c3344"),
    emissiveIntensity: tint ? 0.22 : schematic ? 0.08 : 0.16,
    roughness: 0.48,
    metalness: 0.02,
    transparent: true,
    opacity: tint ? 0.62 : schematic ? 0.38 : 0.58,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexColors: false,
    clippingPlanes: [],
    clipShadows: true,
  });
}

type FasciaProps = {
  layerVisible: boolean;
  chainLayerOn: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
};

export function Fascia({ layerVisible, chainLayerOn, activeChainIds, chainSide }: FasciaProps) {
  const gltf = useGLTF("/models/fascia.glb");
  const scene = useMemo(() => {
    const clone = gltf.scene.clone(true);
    const byId = new Map<string, FasciaPart>(
      (rawFascia.fascia as FasciaPart[]).map((part) => [part.id, part]),
    );
    clone.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      const geom = obj.geometry;
      if (!geom.getAttribute("normal")) geom.computeVertexNormals();
      const id = obj.name || obj.parent?.name || "";
      obj.userData.pick = "fascia";
      obj.userData.fasciaId = id;
      obj.userData.source = byId.get(id)?.source ?? "bodyparts3d";
      obj.castShadow = false;
      obj.receiveShadow = false;
      obj.renderOrder = 2;
    });
    return clone;
  }, [gltf]);

  useEffect(() => {
    const chainIds = chainLayerOn ? new Set(fasciaIdsForChains(activeChainIds)) : new Set<string>();
    const planes = clipPlanesForSide(chainLayerOn ? chainSide : "both");
    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      const id = String(obj.userData.fasciaId ?? obj.name ?? "");
      const inChain = chainIds.has(id);
      const sideOk = matchesChainSide(id, chainLayerOn ? chainSide : "both");
      obj.visible = sideOk && (layerVisible || inChain);
      if (!obj.visible) return;
      const tint = inChain ? tintForFascia(id, activeChainIds) : null;
      const mat = materialFor(String(obj.userData.source ?? "bodyparts3d"), tint);
      mat.clippingPlanes = planes;
      obj.material = mat;
    });
  }, [scene, layerVisible, chainLayerOn, activeChainIds, chainSide]);

  return <primitive object={scene} />;
}

useGLTF.preload("/models/fascia.glb");
