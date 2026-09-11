import { useGLTF } from "@react-three/drei";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { ligaments as catalog } from "../data/loadConnective";
import { applyFiberUVs, createLigamentFiberMaterial, inferLongAxis } from "./fiberMaterial";
import { attachFatRaycast } from "./fatRaycast";
import { setPickMeshes } from "./structurePick";

type LigamentEntry = {
  id: string;
  object: THREE.Object3D;
  material: THREE.MeshPhysicalMaterial;
  meshes: THREE.Mesh[];
  schematic: boolean;
};

function setLigamentSelected(material: THREE.MeshPhysicalMaterial, selected: boolean, schematic: boolean) {
  material.emissive.set(selected ? "#ffcc66" : schematic ? "#7a3a08" : "#5a2a06");
  material.emissiveIntensity = selected ? 0.42 : schematic ? 0.28 : 0.2;
}

type LigamentsProps = {
  visible: boolean;
  selectedId: string | null;
  hiddenIds: string[];
};

export function Ligaments({ visible, selectedId, hiddenIds }: LigamentsProps) {
  const gltf = useGLTF("/models/ligaments.glb");
  const entries = useMemo(() => {
    const list: LigamentEntry[] = [];
    const byId = new Map(catalog.map((part) => [part.id, part]));
    for (const part of catalog) {
      const src = gltf.scene.getObjectByName(part.id);
      if (!src) continue;
      const clone = src.clone(true);
      const schematic = (byId.get(part.id)?.source ?? "bodyparts3d").startsWith("synthetic");
      const material = createLigamentFiberMaterial(schematic);
      const meshes: THREE.Mesh[] = [];
      clone.traverse((obj) => {
        if (!(obj instanceof THREE.Mesh)) return;
        obj.geometry = obj.geometry.clone();
        if (!obj.geometry.getAttribute("normal")) obj.geometry.computeVertexNormals();
        const axis = inferLongAxis(obj.geometry);
        applyFiberUVs(obj.geometry, axis);
        obj.userData.pick = "ligament";
        obj.userData.structureId = part.id;
        obj.userData.pickPriority = 0;
        attachFatRaycast(obj, "ligament");
        obj.castShadow = false;
        obj.receiveShadow = false;
        obj.material = material;
        obj.renderOrder = schematic ? 4 : 3;
        meshes.push(obj);
      });
      clone.visible = false;
      list.push({ id: part.id, object: clone, material, meshes, schematic });
    }
    return list;
  }, [gltf]);

  useEffect(() => {
    const hidden = new Set(hiddenIds);
    const pick: THREE.Mesh[] = [];
    for (const entry of entries) {
      const on = visible && !hidden.has(entry.id);
      entry.object.visible = on;
      setLigamentSelected(entry.material, on && entry.id === selectedId, entry.schematic);
      if (on) pick.push(...entry.meshes);
    }
    setPickMeshes("ligament", pick);
    return () => setPickMeshes("ligament", []);
  }, [entries, hiddenIds, selectedId, visible]);

  return (
    <group name="ligaments">
      {entries.map((entry) => (
        <primitive key={entry.id} object={entry.object} />
      ))}
    </group>
  );
}

useGLTF.preload("/models/ligaments.glb");
