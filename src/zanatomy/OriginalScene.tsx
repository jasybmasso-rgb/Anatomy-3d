import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { CameraRig } from "../scene/CameraRig";
import { getDeviceProfile } from "../scene/deviceProfile";
import { attachWebglGuard } from "../scene/webglGuard";
import type { CameraFrame } from "./types";

const SCENE_BG = "#121a24";

function Lights() {
  return (
    <>
      <ambientLight intensity={0.36} />
      <hemisphereLight args={["#fff4ea", "#5a5048", 0.4]} />
      <directionalLight position={[2.6, 4.4, 3.1]} intensity={1.02} />
      <directionalLight position={[-3.1, 2.4, 1.4]} intensity={0.42} />
      <directionalLight position={[0.2, 1.6, 3.6]} intensity={0.32} />
    </>
  );
}

function structureName(object: THREE.Object3D): string {
  const named = object.userData.zaName;
  if (typeof named === "string" && named.length > 0) return named;
  let current: THREE.Object3D | null = object;
  while (current) {
    if (current.name) return current.name;
    current = current.parent;
  }
  return "Structure";
}

function Readout({
  onFrame,
}: {
  onFrame: (fps: number, triangles: number) => void;
}) {
  const scene = useThree((state) => state.scene);
  const acc = useRef({ frames: 0, time: 0 });
  useFrame((_, dt) => {
    acc.current.frames += 1;
    acc.current.time += dt;
    if (acc.current.time < 0.45) return;
    const fps = acc.current.frames / acc.current.time;
    acc.current.frames = 0;
    acc.current.time = 0;
    let triangles = 0;
    scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh) || !obj.visible) return;
      const index = obj.geometry.index;
      const positions = obj.geometry.getAttribute("position");
      triangles += index ? index.count / 3 : (positions?.count ?? 0) / 3;
    });
    onFrame(Math.round(fps), Math.round(triangles));
  });
  return null;
}

function NamePick({ onPick }: { onPick: (name: string | null) => void }) {
  const { camera, gl, scene } = useThree();
  const raycaster = useMemo(() => new THREE.Raycaster(), []);
  const pointer = useMemo(() => new THREE.Vector2(), []);
  const onPickRef = useRef(onPick);
  onPickRef.current = onPick;
  const selected = useRef<THREE.Mesh | null>(null);
  const original = useRef<THREE.Material | THREE.Material[] | null>(null);

  useEffect(() => {
    const element = gl.domElement;
    let down: { x: number; y: number } | null = null;
    let pointers = 0;
    let multi = false;

    const restore = () => {
      const mesh = selected.current;
      if (mesh && original.current) {
        const clones = mesh.material;
        mesh.material = original.current;
        const materials = Array.isArray(clones) ? clones : [clones];
        for (const material of materials) material.dispose();
      }
      selected.current = null;
      original.current = null;
    };

    const highlight = (mesh: THREE.Mesh) => {
      restore();
      original.current = mesh.material;
      const source = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      const clones = source.map((material) => {
        const clone = material.clone();
        if (clone instanceof THREE.MeshStandardMaterial) {
          clone.emissive = new THREE.Color("#ffe0a3");
          clone.emissiveIntensity = 0.45;
        }
        return clone;
      });
      mesh.material = clones.length === 1 ? clones[0] : clones;
      selected.current = mesh;
    };

    const onPointerDown = (event: PointerEvent) => {
      pointers += 1;
      if (pointers > 1) {
        multi = true;
        down = null;
        return;
      }
      if (event.button !== 0) return;
      down = { x: event.clientX, y: event.clientY };
    };

    const onPointerUp = (event: PointerEvent) => {
      pointers = Math.max(0, pointers - 1);
      if (multi) {
        if (pointers === 0) multi = false;
        down = null;
        return;
      }
      if (!down || event.button !== 0) return;
      const dx = event.clientX - down.x;
      const dy = event.clientY - down.y;
      down = null;
      if (dx * dx + dy * dy > 100) return;
      const rect = element.getBoundingClientRect();
      pointer.set(
        ((event.clientX - rect.left) / Math.max(rect.width, 1)) * 2 - 1,
        -((event.clientY - rect.top) / Math.max(rect.height, 1)) * 2 + 1,
      );
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(scene.children, true);
      const hit = hits.find((item) => item.object instanceof THREE.Mesh && item.object.visible);
      if (!hit || !(hit.object instanceof THREE.Mesh)) {
        restore();
        onPickRef.current(null);
        return;
      }
      highlight(hit.object);
      onPickRef.current(structureName(hit.object));
    };

    element.addEventListener("pointerdown", onPointerDown);
    element.addEventListener("pointerup", onPointerUp);
    return () => {
      element.removeEventListener("pointerdown", onPointerDown);
      element.removeEventListener("pointerup", onPointerUp);
      restore();
    };
  }, [camera, gl, pointer, raycaster, scene]);

  return null;
}

export function OriginalScene({
  groups,
  home,
  onFrame,
  onPick,
  onLost,
  onRestored,
}: {
  groups: THREE.Group[];
  home: CameraFrame;
  onFrame: (fps: number, triangles: number) => void;
  onPick: (name: string | null) => void;
  onLost: () => void;
  onRestored: () => void;
}) {
  const profile = getDeviceProfile();
  return (
    <Canvas
      className="anatomy-canvas"
      shadows={false}
      style={{ width: "100%", height: "100%", display: "block", touchAction: "none" }}
      camera={{ position: home.eye, fov: 38, near: 0.02, far: 40 }}
      dpr={[1, 1]}
      gl={{
        antialias: profile.antialias,
        alpha: false,
        powerPreference: profile.lowEnd ? "default" : "high-performance",
        failIfMajorPerformanceCaveat: false,
      }}
      onCreated={({ gl }) => {
        attachWebglGuard(gl.domElement, onLost, onRestored);
      }}
    >
      <color attach="background" args={[SCENE_BG]} />
      <fog attach="fog" args={[SCENE_BG, 8, 18]} />
      <Lights />
      {groups.map((group) => (
        <primitive key={group.uuid} object={group} />
      ))}
      <CameraRig focus={null} resetToken={0} homeEye={home.eye} homeTarget={home.target} />
      <NamePick onPick={onPick} />
      <Readout onFrame={onFrame} />
    </Canvas>
  );
}
