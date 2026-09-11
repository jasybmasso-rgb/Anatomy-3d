import { useGLTF } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import type { Ligament } from "../data/ligaments";
import rawLigaments from "../data/ligaments.json";
import { applyFiberUVs, createLigamentFiberMaterial, inferLongAxis } from "./fiberMaterial";

export function Ligaments({ visible }: { visible: boolean }) {
  const gltf = useGLTF("/models/ligaments.glb");
  const scene = useMemo(() => {
    const clone = gltf.scene.clone(true);
    const byId = new Map<string, Ligament>(
      (rawLigaments.ligaments as Ligament[]).map((part) => [part.id, part]),
    );
    const cache = new Map<string, THREE.MeshPhysicalMaterial>();
    clone.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      obj.geometry = obj.geometry.clone();
      if (!obj.geometry.getAttribute("normal")) obj.geometry.computeVertexNormals();
      const axis = inferLongAxis(obj.geometry);
      applyFiberUVs(obj.geometry, axis);
      const id = obj.name || obj.parent?.name || "";
      const source = byId.get(id)?.source ?? "bodyparts3d";
      const schematic = source.startsWith("synthetic");
      const key = schematic ? "synthetic" : "bodyparts3d";
      let mat = cache.get(key);
      if (!mat) {
        mat = createLigamentFiberMaterial(schematic);
        cache.set(key, mat);
      }
      obj.userData.pick = "ligament";
      obj.raycast = () => {};
      obj.castShadow = false;
      obj.receiveShadow = false;
      obj.material = mat;
      obj.renderOrder = schematic ? 4 : 3;
    });
    return clone;
  }, [gltf]);

  return <primitive object={scene} visible={visible} />;
}

useGLTF.preload("/models/ligaments.glb");
