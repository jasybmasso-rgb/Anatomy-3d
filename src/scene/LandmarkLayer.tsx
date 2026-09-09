import { Html } from "@react-three/drei";
import { useState } from "react";
import raw from "../data/landmarks.json";
import type { LandmarksFile } from "../data/landmarks";

const data = raw as LandmarksFile;

export function LandmarkLayer({ visible }: { visible: boolean }) {
  const [hovered, setHovered] = useState<string | null>(null);
  const [pinned, setPinned] = useState<string | null>(null);
  if (!visible) return null;

  return (
    <group>
      {data.landmarks.map((lm) => {
        const active = hovered === lm.id || pinned === lm.id;
        return (
          <group key={lm.id} position={lm.position}>
            <mesh
              onPointerOver={(event) => {
                event.stopPropagation();
                setHovered(lm.id);
              }}
              onPointerOut={() => setHovered((cur) => (cur === lm.id ? null : cur))}
              onClick={(event) => {
                event.stopPropagation();
                setPinned((cur) => (cur === lm.id ? null : lm.id));
              }}
            >
              <sphereGeometry args={[0.032, 12, 10]} />
              <meshBasicMaterial transparent opacity={0} depthWrite={false} />
            </mesh>
            <mesh raycast={() => null}>
              <sphereGeometry args={[active ? 0.016 : 0.011, 12, 10]} />
              <meshStandardMaterial
                color={active ? "#7eb6ff" : "#e0b53a"}
                emissive={active ? "#245a9a" : "#5a3d08"}
                roughness={0.35}
                metalness={0.1}
              />
            </mesh>
            {active ? (
              <Html center sprite zIndexRange={[30, 0]} style={{ pointerEvents: "none" }}>
                <div className="landmark-label">
                  <strong>{lm.name}</strong>
                  <em>{lm.nameLatin}</em>
                </div>
              </Html>
            ) : null}
          </group>
        );
      })}
    </group>
  );
}
