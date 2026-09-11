import { useGLTF } from "@react-three/drei";
import { useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { chainClipSide, tintForMuscle, type ChainSide } from "../data/chains";
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
  meshes: THREE.Mesh[];
};

const CLICK_PX = 10;
const THIN_SHEETS = new Set([
  "droit-abdomen",
  "oblique-interne",
  "transverse-de-l-abdomen",
  "oblique-externe",
  "grand-dorsal",
  "temporal",
  "masseter",
  "pterygoide-medial",
  "pterygoide-lateral",
]);

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

function applyTendonAttribute(geometry: THREE.BufferGeometry) {
  if (geometry.getAttribute("tendon")) return;
  const pos = geometry.getAttribute("position");
  const color = geometry.getAttribute("color");
  const arr = new Float32Array(pos.count);
  if (color) {
    for (let i = 0; i < pos.count; i += 1) {
      let r = color.getX(i);
      let g = color.getY(i);
      let b = color.getZ(i);
      if (r > 1.01 || g > 1.01 || b > 1.01) {
        r /= 255;
        g /= 255;
        b /= 255;
      }
      const lum = 0.299 * r + 0.587 * g + 0.114 * b;
      arr[i] = THREE.MathUtils.smoothstep(0.52, 0.82, lum);
    }
  }
  geometry.setAttribute("tendon", new THREE.BufferAttribute(arr, 1));
}

export function MuscleLayer(props: MuscleLayerProps) {
  const gltf = useGLTF("/models/muscles.glb");
  const { camera, gl } = useThree();
  const raycaster = useMemo(() => new THREE.Raycaster(), []);
  const pointer = useMemo(() => new THREE.Vector2(), []);
  const onSelectRef = useRef(props.onSelect);
  onSelectRef.current = props.onSelect;

  const entries = useMemo(() => {
    const list: MuscleEntry[] = [];
    for (const muscle of muscles) {
      const src = gltf.scene.getObjectByName(muscle.id);
      if (!src) continue;
      const clone = src.clone(true);
      const hint = new THREE.Vector3(...(muscle.fiberAxis ?? [0, 0, 0]));
      const material = createFiberMuscleMaterial();
      if (THIN_SHEETS.has(muscle.id)) material.side = THREE.DoubleSide;
      const meshes: THREE.Mesh[] = [];
      clone.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh)) return;
        obj.geometry = obj.geometry.clone();
        if (!obj.geometry.getAttribute("normal")) {
          obj.geometry.computeVertexNormals();
        }
        applyFiberUVs(obj.geometry, hint.lengthSq() > 1e-8 ? hint : undefined);
        applyTendonAttribute(obj.geometry);
        obj.userData.pick = "muscle";
        obj.userData.muscleId = muscle.id;
        obj.castShadow = true;
        obj.receiveShadow = false;
        obj.material = material;
        meshes.push(obj);
      });
      clone.visible = false;
      list.push({ id: muscle.id, object: clone, material, meshes });
    }
    return list;
  }, [gltf]);

  const meshList = useMemo(() => entries.flatMap((entry) => entry.meshes), [entries]);

  useEffect(() => {
    const shown = visibleIds(props);
    const chainOn = props.chainLayerOn && props.activeChainIds.length > 0;
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
      const side = chainOn ? chainClipSide(entry.id, props.chainSide, props.activeChainIds) : "both";
      entry.material.clippingPlanes = clipPlanesForSide(side);
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

  useEffect(() => {
    const element = gl.domElement;
    let down: { x: number; y: number } | null = null;

    const onPointerDown = (event: PointerEvent) => {
      if (event.button !== 0) return;
      down = { x: event.clientX, y: event.clientY };
    };

    const onPointerUp = (event: PointerEvent) => {
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
      const targets = meshList.filter((mesh) => {
        if (!mesh.visible) return false;
        let node: THREE.Object3D | null = mesh;
        while (node) {
          if (!node.visible) return false;
          node = node.parent;
        }
        return mesh.userData.pick === "muscle";
      });
      const hits = raycaster.intersectObjects(targets, false);
      for (const hit of hits) {
        const id = hit.object.userData.muscleId;
        if (typeof id === "string") {
          onSelectRef.current(id);
          break;
        }
      }
    };

    element.addEventListener("pointerdown", onPointerDown);
    element.addEventListener("pointerup", onPointerUp);
    return () => {
      element.removeEventListener("pointerdown", onPointerDown);
      element.removeEventListener("pointerup", onPointerUp);
    };
  }, [camera, gl, meshList, pointer, raycaster]);

  return (
    <group name="muscles">
      {entries.map((entry) => (
        <primitive key={entry.id} object={entry.object} />
      ))}
    </group>
  );
}

useGLTF.preload("/models/muscles.glb");
