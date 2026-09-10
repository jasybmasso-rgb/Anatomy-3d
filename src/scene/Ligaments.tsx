import { useGLTF } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import type { Ligament } from "../data/ligaments";
import rawLigaments from "../data/ligaments.json";

const BP3D_COLOR = "#d7b48c";
const SYNTH_COLOR = "#c4a078";

function materialFor(source: string) {
  const schematic = source.startsWith("synthetic");
  return new THREE.MeshPhysicalMaterial({
    color: schematic ? SYNTH_COLOR : BP3D_COLOR,
    emissive: schematic ? "#5a3a18" : "#6a4220",
    emissiveIntensity: schematic ? 0.22 : 0.4,
    roughness: schematic ? 0.55 : 0.48,
    metalness: 0.02,
    transparent: true,
    opacity: schematic ? 0.62 : 0.95,
    depthTest: !schematic,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexColors: false,
  });
}

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
      const geom = obj.geometry;
      if (!geom.getAttribute("normal")) geom.computeVertexNormals();
      const id = obj.name || obj.parent?.name || "";
      const source = byId.get(id)?.source ?? "bodyparts3d";
      let mat = cache.get(source);
      if (!mat) {
        mat = materialFor(source);
        cache.set(source, mat);
      }
      obj.userData.pick = "ligament";
      obj.castShadow = false;
      obj.receiveShadow = false;
      obj.material = mat;
      obj.renderOrder = source.startsWith("synthetic") ? 4 : 3;
    });
    return clone;
  }, [gltf]);

  return <primitive object={scene} visible={visible} />;
}

useGLTF.preload("/models/ligaments.glb");
