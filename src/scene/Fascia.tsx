import { useGLTF } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";

const FASCIA_COLOR = "#7f9eb5";

export function Fascia({ visible }: { visible: boolean }) {
  const gltf = useGLTF("/models/fascia.glb");
  const scene = useMemo(() => {
    const clone = gltf.scene.clone(true);
    const material = new THREE.MeshPhysicalMaterial({
      color: FASCIA_COLOR,
      emissive: "#1c3344",
      emissiveIntensity: 0.16,
      roughness: 0.42,
      metalness: 0.02,
      transparent: true,
      opacity: 0.58,
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
        obj.userData.pick = "fascia";
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

useGLTF.preload("/models/fascia.glb");
