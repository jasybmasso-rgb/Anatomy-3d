import { useGLTF } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import type { Muscle } from "../types/muscle";
import { createFiberMuscleMaterial, paintFiberVertexColors } from "./fiberMaterial";

export function MuscleMesh({ muscle }: { muscle: Muscle }) {
  const gltf = useGLTF("/models/muscles.glb");
  const object = useMemo(() => {
    const src = gltf.scene.getObjectByName(muscle.id);
    if (!src) return null;
    const clone = src.clone(true);
    const axis = new THREE.Vector3(...(muscle.fiberAxis ?? [0, 1, 0]));
    if (axis.lengthSq() < 1e-8) axis.set(0, 1, 0);
    const material = createFiberMuscleMaterial();
    clone.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry = obj.geometry.clone();
        if (!obj.geometry.getAttribute("normal")) {
          obj.geometry.computeVertexNormals();
        }
        paintFiberVertexColors(obj.geometry, axis);
        obj.userData.pick = "muscle";
        obj.castShadow = true;
        obj.receiveShadow = false;
        obj.material = material;
        obj.visible = true;
      }
    });
    return clone;
  }, [gltf, muscle]);

  if (!object) return null;
  return <primitive object={object} />;
}

useGLTF.preload("/models/muscles.glb");
