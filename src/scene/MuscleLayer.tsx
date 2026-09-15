import { useGLTF } from "@react-three/drei";
import { useThree } from "@react-three/fiber";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { chainClipSide, tintForMuscle, type ChainSide } from "../data/chains";
import { muscles } from "../data/loadMuscles";
import { getDeviceProfile } from "./deviceProfile";
import { registerHighlight, unregisterHighlight } from "./selectionHighlight";
import { setPickMeshes } from "./structurePick";
import {
  applyFiberUVs,
  clipPlanesForSide,
  createFiberMuscleMaterial,
  setMuscleTendonAlpha,
  setMuscleTint,
  setMuscleSelected,
} from "./fiberMaterial";
import { attachMuscleOutline, createMuscleOutlineMaterials, setOutlineResolution } from "./muscleOutline";

export type MuscleLayerProps = {
  selectedMuscleId: string | null;
  pinnedMuscleId: string | null;
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
  material: THREE.MeshPhongMaterial;
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

const APO_TRANSPARENT = new Set(["oblique-externe", "oblique-interne", "transverse-de-l-abdomen"]);

/** Superficial → drawn later. Deep wall / back stay behind even if sheets kiss. */
const WALL_ORDER: Record<string, number> = {
  "transverse-de-l-abdomen": 1,
  "oblique-interne": 2,
  "dentele-posterieur-inferieur": 2,
  "iliocostal-thoracique": 2,
  "iliocostal-lombaire": 2,
  "longissimus-du-thorax": 2,
  "droit-abdomen": 4,
  "oblique-externe": 9,
  "grand-dorsal": 11,
};

const WALL_OFFSET: Record<string, number> = {
  "transverse-de-l-abdomen": 14,
  "oblique-interne": 7,
  "dentele-posterieur-inferieur": 12,
  "iliocostal-thoracique": 12,
  "iliocostal-lombaire": 10,
  "longissimus-du-thorax": 10,
  "droit-abdomen": 0,
  "oblique-externe": -10,
  "grand-dorsal": -16,
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
  if (props.showMuscles && props.pinnedMuscleId && !hidden.has(props.pinnedMuscleId)) {
    shown.add(props.pinnedMuscleId);
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
  const size = useThree((state) => state.size);
  const dpr = useThree((state) => state.viewport.dpr);

  useEffect(() => {
    setOutlineResolution(size.width * dpr, size.height * dpr);
  }, [size.width, size.height, dpr]);

  const entries = useMemo(() => {
    const list: MuscleEntry[] = [];
    for (const muscle of muscles) {
      const src = gltf.scene.getObjectByName(muscle.id);
      if (!src) continue;
      const clone = src.clone(true);
      const hint = new THREE.Vector3(...(muscle.fiberAxis ?? [0, 0, 0]));
      const material = createFiberMuscleMaterial();
      const outlineMaterials = createMuscleOutlineMaterials();
      if (THIN_SHEETS.has(muscle.id)) material.side = THREE.DoubleSide;
      if (APO_TRANSPARENT.has(muscle.id)) {
        setMuscleTendonAlpha(material, 0.34);
        material.transparent = true;
        material.depthWrite = true;
        material.opacity = 1;
      }
      const wallOff = WALL_OFFSET[muscle.id];
      if (wallOff !== undefined) {
        material.polygonOffset = true;
        material.polygonOffsetFactor = wallOff;
        material.polygonOffsetUnits = wallOff;
      }
      const meshes: THREE.Mesh[] = [];
      clone.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh)) return;
        if (obj.name === "muscle-outline") return;
        obj.geometry = obj.geometry.clone();
        if (!obj.geometry.getAttribute("normal")) {
          obj.geometry.computeVertexNormals();
        }
        applyFiberUVs(obj.geometry, hint.lengthSq() > 1e-8 ? hint : undefined);
        if (!obj.geometry.getAttribute("color")) {
          const n = obj.geometry.getAttribute("position").count;
          const rgb = new Float32Array(n * 3);
          for (let i = 0; i < n; i += 1) {
            rgb[i * 3] = 0.769;
            rgb[i * 3 + 1] = 0.282;
            rgb[i * 3 + 2] = 0.227;
          }
          obj.geometry.setAttribute("color", new THREE.BufferAttribute(rgb, 3));
        }
        obj.userData.pick = "muscle";
        obj.userData.muscleId = muscle.id;
        obj.raycast = THREE.Mesh.prototype.raycast;
        obj.castShadow = getDeviceProfile().shadows;
        obj.receiveShadow = false;
        obj.material = material;
        attachMuscleOutline(obj, outlineMaterials);
        meshes.push(obj);
      });
      clone.visible = false;
      list.push({ id: muscle.id, object: clone, material, meshes });
    }
    return list;
  }, [gltf]);

  useEffect(() => {
    for (const entry of entries) {
      registerHighlight("muscle", entry.id, (selected) => setMuscleSelected(entry.material, selected));
    }
    return () => {
      for (const entry of entries) unregisterHighlight("muscle", entry.id);
    };
  }, [entries]);

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
      const apo = APO_TRANSPARENT.has(entry.id);
      entry.material.transparent = apo;
      entry.material.opacity = 1;
      entry.material.depthWrite = true;
      const side = chainOn ? chainClipSide(entry.id, props.chainSide, props.activeChainIds) : "both";
      const planes = clipPlanesForSide(side);
      entry.material.clippingPlanes = planes;
      entry.object.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh) && obj.type !== "LineSegments2") return;
        if (obj.name === "muscle-outline") {
          const raw = (obj as THREE.Mesh).material;
          const mats = Array.isArray(raw) ? raw : [raw];
          for (const mat of mats) {
            if (mat && "clippingPlanes" in mat) {
              (mat as THREE.Material & { clippingPlanes: THREE.Plane[] }).clippingPlanes = planes;
            }
          }
          obj.renderOrder = selected ? 14 : Math.max((WALL_ORDER[entry.id] ?? 5) + 3, 3);
          return;
        }
        if (!(obj instanceof THREE.Mesh)) return;
        obj.renderOrder = selected ? 12 : (WALL_ORDER[entry.id] ?? 5);
        obj.castShadow = getDeviceProfile().shadows;
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
