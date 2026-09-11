import { useGLTF } from "@react-three/drei";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { chainClipSide, tintForMuscle, type ChainSide } from "../data/chains";
import { muscles } from "../data/loadMuscles";
import { setPickMeshes } from "./structurePick";
import {
  applyFiberUVs,
  clipPlanesForSide,
  createFiberMuscleMaterial,
  setMuscleTint,
  setMuscleSelected,
} from "./fiberMaterial";

export type MuscleLayerProps = {
  selectedMuscleId: string | null;
  showMuscles: boolean;
  showAllMuscles: boolean;
  hiddenMuscleIds: string[];
  chainLayerOn: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
};

type MuscleEntry = {
  id: string;
  object: THREE.Object3D;
  material: THREE.MeshPhysicalMaterial;
  meshes: THREE.Mesh[];
};

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

/** Superficial → drawn later. Deep wall stays behind even if sheets kiss. */
const WALL_ORDER: Record<string, number> = {
  "transverse-de-l-abdomen": 2,
  "oblique-interne": 3,
  "droit-abdomen": 4,
  "oblique-externe": 6,
};

const WALL_OFFSET: Record<string, number> = {
  "transverse-de-l-abdomen": 4,
  "oblique-interne": 2,
  "droit-abdomen": 0,
  "oblique-externe": -2,
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
  const uv = geometry.getAttribute("uv");
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
      arr[i] = THREE.MathUtils.smoothstep(0.48, 0.86, lum);
    }
  }
  if (uv) {
    for (let i = 0; i < pos.count; i += 1) {
      const along = THREE.MathUtils.clamp(uv.getX(i), 0, 1);
      const end = 1 - THREE.MathUtils.smoothstep(0, 0.16, Math.min(along, 1 - along));
      arr[i] = Math.max(arr[i], end * 0.82);
    }
  }
  geometry.setAttribute("tendon", new THREE.BufferAttribute(arr, 1));
}

export function MuscleLayer(props: MuscleLayerProps) {
  const gltf = useGLTF("/models/muscles.glb");

  const entries = useMemo(() => {
    const list: MuscleEntry[] = [];
    for (const muscle of muscles) {
      const src = gltf.scene.getObjectByName(muscle.id);
      if (!src) continue;
      const clone = src.clone(true);
      const hint = new THREE.Vector3(...(muscle.fiberAxis ?? [0, 0, 0]));
      const material = createFiberMuscleMaterial();
      if (THIN_SHEETS.has(muscle.id)) material.side = THREE.DoubleSide;
      const wallOff = WALL_OFFSET[muscle.id];
      if (wallOff !== undefined) {
        material.polygonOffset = true;
        material.polygonOffsetFactor = wallOff;
        material.polygonOffsetUnits = wallOff;
      }
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
        obj.raycast = THREE.Mesh.prototype.raycast;
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
      setMuscleTint(entry.material, tint, tint ? (selected ? 0.48 : 0.78) : 0);
      setMuscleSelected(entry.material, selected);
      entry.material.transparent = false;
      entry.material.opacity = 1;
      entry.material.depthWrite = true;
      const side = chainOn ? chainClipSide(entry.id, props.chainSide, props.activeChainIds) : "both";
      entry.material.clippingPlanes = clipPlanesForSide(side);
      entry.object.traverse((obj) => {
        if (obj instanceof THREE.Mesh) {
          obj.renderOrder = selected ? 8 : (WALL_ORDER[entry.id] ?? 5);
          obj.castShadow = true;
        }
      });
    }
    setPickMeshes(
      "muscle",
      entries.flatMap((entry) => (entry.object.visible ? entry.meshes : [])),
    );
    return () => setPickMeshes("muscle", []);
  }, [entries, props]);

  return (
    <group name="muscles">
      {entries.map((entry) => (
        <primitive key={entry.id} object={entry.object} />
      ))}
    </group>
  );
}

useGLTF.preload("/models/muscles.glb");
