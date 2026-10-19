import * as THREE from "three";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { OriginalSystem } from "./types";

export function disposeGroup(group: THREE.Object3D) {
  group.traverse((obj) => {
    if (!(obj instanceof THREE.Mesh)) return;
    obj.geometry.dispose();
    const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
    for (const material of materials) material.dispose();
  });
}

export function loadSystem(
  system: OriginalSystem,
  onProgress: (loaded: number, total: number) => void,
): Promise<THREE.Group> {
  const draco = new DRACOLoader();
  draco.setDecoderPath("/draco/");
  const loader = new GLTFLoader();
  loader.setDRACOLoader(draco);
  const root = new THREE.Group();
  root.name = system.id;

  const totals = system.files.map((file) => file.bytes);
  const loaded = system.files.map(() => 0);

  const report = () => {
    onProgress(
      loaded.reduce((sum, value) => sum + value, 0),
      totals.reduce((sum, value) => sum + value, 0),
    );
  };

  const jobs = system.files.map(
    (file, index) =>
      new Promise<THREE.Group>((resolve, reject) => {
        loader.load(
          file.url,
          (gltf) => {
            gltf.scene.traverse((obj) => {
              if (!(obj instanceof THREE.Mesh)) return;
              obj.userData.zaName = obj.name || obj.parent?.name || system.label;
              obj.castShadow = false;
              obj.receiveShadow = false;
            });
            loaded[index] = file.bytes;
            report();
            resolve(gltf.scene);
          },
          (event) => {
            loaded[index] = event.total > 0 ? Math.min(event.loaded, file.bytes) : event.loaded;
            report();
          },
          (error) => reject(error),
        );
      }),
  );

  return Promise.all(jobs)
    .then((scenes) => {
      for (const scene of scenes) root.add(scene);
      return root;
    })
    .finally(() => {
      draco.dispose();
    });
}
