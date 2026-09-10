import { useGLTF } from "@react-three/drei";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { tintForMuscle } from "../data/chains";
import { muscles } from "../data/loadMuscles";
import {
  applyFiberUVs,
  createFiberMuscleMaterial,
  setMuscleTint,
} from "./fiberMaterial";

export type MuscleLayerProps = {
  selectedMuscleId: string | null;
  showMuscles: boolean;
  showAllMuscles: boolean;
  hiddenMuscleIds: string[];
  chainLayerOn: boolean;
  activeChainIds: string[];
};

type MuscleEntry = {
  id: string;
  object: THREE.Object3D;
  material: THREE.MeshPhysicalMaterial;
};

function visibleIds(props: MuscleLayerProps): Set<string> {
  const hidden = new Set(props.hiddenMuscleIds);
  const shown = new Set<string>();
  if (props.showMuscles && props.showAllMuscles) {
    for (const muscle of muscles) {
      if (!hidden.has(muscle.id)) shown.add(muscle.id);
    }
  }
  if (props.showMuscles && props.selectedMuscleId && !hidden.has(props.selectedMuscleId)) {
    shown.add(props.selectedMuscleId);
  }
  if (props.chainLayerOn) {
    for (const muscle of muscles) {
      if (tintForMuscle(muscle.id, props.activeChainIds)) shown.add(muscle.id);
    }
  }
  return shown;
}

export function MuscleLayer(props: MuscleLayerProps) {
  const gltf = useGLTF("/models/muscles.glb");
  const entries = useMemo(() => {
    const list: MuscleEntry[] = [];
    for (const muscle of muscles) {
      const src = gltf.scene.getObjectByName(muscle.id);
      if (!src) continue;
      const clone = src.clone(true);
      const axis = new THREE.Vector3(...(muscle.fiberAxis ?? [0, 1, 0]));
      if (axis.lengthSq() < 1e-8) axis.set(0, 1, 0);
      const material = createFiberMuscleMaterial();
      clone.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh)) return;
        obj.geometry = obj.geometry.clone();
        if (!obj.geometry.getAttribute("normal")) {
          obj.geometry.computeVertexNormals();
        }
        applyFiberUVs(obj.geometry, axis);
        obj.userData.pick = "muscle";
        obj.userData.muscleId = muscle.id;
        obj.castShadow = true;
        obj.receiveShadow = false;
        obj.material = material;
      });
      clone.visible = false;
      list.push({ id: muscle.id, object: clone, material });
    }
    return list;
  }, [gltf]);

  const root = useMemo(() => {
    const group = new THREE.Group();
    group.name = "muscles";
    for (const entry of entries) group.add(entry.object);
    return group;
  }, [entries]);

  useEffect(() => {
    const shown = visibleIds(props);
    const showAll = props.showMuscles && props.showAllMuscles;
    const chainOn = props.chainLayerOn && props.activeChainIds.length > 0;
    for (const entry of entries) {
      const on = shown.has(entry.id);
      entry.object.visible = on;
      if (!on) continue;
      const selected = entry.id === props.selectedMuscleId;
      const tintHex = chainOn ? tintForMuscle(entry.id, props.activeChainIds) : null;
      const tint = tintHex ? new THREE.Color(tintHex) : null;
      const ghosted = showAll && !selected && !tint;
      const opacity = selected ? 0.97 : tint ? 0.94 : showAll ? (chainOn ? 0.28 : 0.52) : 0.96;
      setMuscleTint(entry.material, tint, tint ? (selected ? 0.42 : 0.78) : 0);
      entry.material.opacity = opacity;
      entry.material.transparent = opacity < 0.98;
      entry.material.depthWrite = selected || opacity > 0.85;
      entry.material.emissive.set(selected ? "#4a1810" : "#000000");
      entry.material.emissiveIntensity = selected ? 0.16 : 0;
      entry.object.traverse((obj) => {
        if (obj instanceof THREE.Mesh) {
          obj.renderOrder = selected ? 6 : ghosted ? 4 : 5;
          obj.castShadow = selected || !ghosted;
        }
      });
    }
  }, [entries, props]);

  return <primitive object={root} />;
}

useGLTF.preload("/models/muscles.glb");
