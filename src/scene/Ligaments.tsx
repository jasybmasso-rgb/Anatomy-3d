import { useGLTF } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";

const LIGAMENT_COLOR = "#d7b48c";

export function Ligaments({ visible }: { visible: boolean }) {
  const gltf = useGLTF("/models/ligaments.glb");
  const scene = useMemo(() => {
    const clone = gltf.scene.clone(true);
    const material = new THREE.MeshPhysicalMaterial({
      color: LIGAMENT_COLOR,
      emissive: "#5a3a1c",
      emissiveIntensity: 0.18,
      roughness: 0.5,
      metalness: 0.02,
      transparent: true,
      opacity: 0.78,
      depthWrite: false,
      side: THREE.DoubleSide,
      vertexColors: false,
    });
    clone.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        const geom = obj.geometry;
        if (!geom.getAttribute("normal")) {
          geom.computeVertexNormals();
        }
        obj.userData.pick = "ligament";
        obj.castShadow = false;
        obj.receiveShadow = false;
        obj.material = material;
      }
    });
    return clone;
  }, [gltf]);

  if (!visible) return null;
  return <primitive object={scene} />;
}

useGLTF.preload("/models/ligaments.glb");
