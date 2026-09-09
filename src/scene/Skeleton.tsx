import { useGLTF } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import { FLOOR_Y } from "./landmarks";

const BONE_COLOR = "#f0e4d0";

export function Skeleton() {
  const gltf = useGLTF("/models/skeleton.glb");
  const scene = useMemo(() => {
    const clone = gltf.scene.clone(true);
    const material = new THREE.MeshStandardMaterial({
      color: BONE_COLOR,
      roughness: 0.48,
      metalness: 0.02,
      vertexColors: false,
    });
    clone.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        const geom = obj.geometry;
        if (!geom.getAttribute("normal")) {
          geom.computeVertexNormals();
        }
        obj.castShadow = true;
        obj.receiveShadow = true;
        obj.material = material;
      }
    });
    return clone;
  }, [gltf]);

  return (
    <group>
      <primitive object={scene} />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, FLOOR_Y, 0]} receiveShadow>
        <circleGeometry args={[1.8, 48]} />
        <meshStandardMaterial color="#1b2432" roughness={1} metalness={0} />
      </mesh>
    </group>
  );
}

useGLTF.preload("/models/skeleton.glb");
