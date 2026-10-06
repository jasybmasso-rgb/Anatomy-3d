import { useGLTF } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import { getDeviceProfile } from "./deviceProfile";
import { FLOOR_Y } from "./landmarks";

const BONE_COLOR = "#f0e4d0";
const CARTILAGE_COLOR = "#b9d4e4";

function isCartilageNode(obj: THREE.Object3D): boolean {
  let current: THREE.Object3D | null = obj;
  while (current) {
    const name = current.name.toLowerCase();
    if (name.includes("cartilage")) return true;
    current = current.parent;
  }
  return false;
}

export function Skeleton() {
  const gltf = useGLTF("/models/skeleton.glb");
  const scene = useMemo(() => {
    const clone = gltf.scene.clone(true);
    const boneMaterial = new THREE.MeshStandardMaterial({
      color: BONE_COLOR,
      roughness: 0.48,
      metalness: 0.02,
      vertexColors: false,
    });
    const cartilageMaterial = getDeviceProfile().physicalMaterials
      ? new THREE.MeshPhysicalMaterial({
          color: CARTILAGE_COLOR,
          roughness: 0.22,
          metalness: 0.0,
          transparent: true,
          opacity: 0.72,
          clearcoat: 0.28,
          clearcoatRoughness: 0.35,
          side: THREE.DoubleSide,
          vertexColors: false,
          depthWrite: true,
        })
      : new THREE.MeshPhongMaterial({
          color: CARTILAGE_COLOR,
          shininess: 18,
          transparent: true,
          opacity: 0.72,
          side: THREE.DoubleSide,
          depthWrite: true,
        });
    clone.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        const geom = obj.geometry;
        if (!geom.getAttribute("normal")) {
          geom.computeVertexNormals();
        }
        obj.userData.pick = "bone";
        obj.castShadow = true;
        obj.receiveShadow = true;
        obj.material = isCartilageNode(obj) ? cartilageMaterial : boneMaterial;
      }
    });
    return clone;
  }, [gltf]);

  return (
    <group>
      <primitive object={scene} />
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, FLOOR_Y, 0]}
        receiveShadow
        userData={{ pick: "ignore" }}
        raycast={() => null}
      >
        <circleGeometry args={[1.8, 48]} />
        <meshStandardMaterial color="#1b2432" roughness={1} metalness={0} />
      </mesh>
    </group>
  );
}

useGLTF.preload("/models/skeleton.glb");
