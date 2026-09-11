import { useGLTF } from "@react-three/drei";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { tintForMuscle, type ChainSide } from "../data/chains";
import { muscles } from "../data/loadMuscles";
import {
  applyFiberUVs,
  clipPlanesForSide,
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
  chainSide: ChainSide;
  onSelect: (id: string) => void;
};

type MuscleEntry = {
  id: string;
  object: THREE.Object3D;
  material: THREE.MeshPhysicalMaterial;
};

const CLICK_PX = 10;

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
      if (hidden.has(muscle.id)) continue;
      if (tintForMuscle(muscle.id, props.activeChainIds)) shown.add(muscle.id);
    }
  }
  return shown;
}

export function MuscleLayer(props: MuscleLayerProps) {
  const gltf = useGLTF("/models/muscles.glb");
  const pointerDown = useRef<{ x: number; y: number; id: string } | null>(null);
  const entries = useMemo(() => {
    const list: MuscleEntry[] = [];
    for (const muscle of muscles) {
      const src = gltf.scene.getObjectByName(muscle.id);
      if (!src) continue;
      const clone = src.clone(true);
      const hint = new THREE.Vector3(...(muscle.fiberAxis ?? [0, 0, 0]));
      const material = createFiberMuscleMaterial();
      clone.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh)) return;
        obj.geometry = obj.geometry.clone();
        if (!obj.geometry.getAttribute("normal")) {
          obj.geometry.computeVertexNormals();
        }
        applyFiberUVs(obj.geometry, hint.lengthSq() > 1e-8 ? hint : undefined);
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

  useEffect(() => {
    const shown = visibleIds(props);
    const chainOn = props.chainLayerOn && props.activeChainIds.length > 0;
    const planes = clipPlanesForSide(chainOn ? props.chainSide : "both");
    for (const entry of entries) {
      const on = shown.has(entry.id);
      entry.object.visible = on;
      if (!on) continue;
      const selected = entry.id === props.selectedMuscleId;
      const tintHex = chainOn ? tintForMuscle(entry.id, props.activeChainIds) : null;
      const tint = tintHex ? new THREE.Color(tintHex) : null;
      setMuscleTint(entry.material, tint, tint ? (selected ? 0.42 : 0.78) : 0);
      entry.material.transparent = false;
      entry.material.opacity = 1;
      entry.material.depthWrite = true;
      entry.material.clippingPlanes = planes;
      entry.material.emissive.set(selected ? "#4a1810" : "#000000");
      entry.material.emissiveIntensity = selected ? 0.16 : 0;
      entry.object.traverse((obj) => {
        if (obj instanceof THREE.Mesh) {
          obj.renderOrder = selected ? 6 : 5;
          obj.castShadow = true;
        }
      });
    }
  }, [entries, props]);

  return (
    <group name="muscles">
      {entries.map((entry) => (
        <primitive
          key={entry.id}
          object={entry.object}
          onPointerDown={(event: THREE.Event & { clientX?: number; clientY?: number }) => {
            pointerDown.current = {
              x: event.clientX ?? 0,
              y: event.clientY ?? 0,
              id: entry.id,
            };
          }}
          onPointerUp={(event: THREE.Event & { clientX?: number; clientY?: number; stopPropagation: () => void }) => {
            const down = pointerDown.current;
            pointerDown.current = null;
            if (!down || down.id !== entry.id) return;
            const dx = (event.clientX ?? 0) - down.x;
            const dy = (event.clientY ?? 0) - down.y;
            if (dx * dx + dy * dy > CLICK_PX * CLICK_PX) return;
            event.stopPropagation();
            props.onSelect(entry.id);
          }}
        />
      ))}
    </group>
  );
}

useGLTF.preload("/models/muscles.glb");
