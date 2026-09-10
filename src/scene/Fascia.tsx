import { useGLTF } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import type { FasciaPart } from "../data/fascia";
import rawFascia from "../data/fascia.json";

function materialFor(source: string) {
  const schematic = source.startsWith("synthetic");
  return new THREE.MeshPhysicalMaterial({
    color: schematic ? "#8aa8bc" : "#7f9eb5",
    emissive: "#1c3344",
    emissiveIntensity: schematic ? 0.1 : 0.16,
    roughness: 0.42,
    metalness: 0.02,
    transparent: true,
    opacity: schematic ? 0.32 : 0.58,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexColors: false,
  });
}

export function Fascia({ visible }: { visible: boolean }) {
  const gltf = useGLTF("/models/fascia.glb");
  const scene = useMemo(() => {
    const clone = gltf.scene.clone(true);
    const byId = new Map<string, FasciaPart>(
      (rawFascia.fascia as FasciaPart[]).map((part) => [part.id, part]),
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
      obj.userData.pick = "fascia";
      obj.castShadow = false;
      obj.receiveShadow = false;
      obj.material = mat;
      obj.renderOrder = 2;
    });
    return clone;
  }, [gltf]);

  return <primitive object={scene} visible={visible} />;
}

useGLTF.preload("/models/fascia.glb");
