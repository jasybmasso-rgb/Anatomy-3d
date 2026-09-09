import { Html } from "@react-three/drei";
import { useState } from "react";
import raw from "../data/landmarks.json";
import type { LandmarksFile } from "../data/landmarks";

const data = raw as LandmarksFile;

export function LandmarkLayer({ visible }: { visible: boolean }) {
  const [hovered, setHovered] = useState<string | null>(null);
  if (!visible) return null;

  return (
    <group>
      {data.landmarks.map((lm) => {
        const active = hovered === lm.id;
        return (
          <mesh
            key={lm.id}
            position={lm.position}
            onPointerOver={(event) => {
              event.stopPropagation();
              setHovered(lm.id);
            }}
            onPointerOut={() => setHovered((cur) => (cur === lm.id ? null : cur))}
          >
            <sphereGeometry args={[active ? 0.016 : 0.011, 12, 10]} />
            <meshStandardMaterial
              color={active ? "#7eb6ff" : "#e0b53a"}
              emissive={active ? "#245a9a" : "#5a3d08"}
              roughness={0.35}
              metalness={0.1}
            />
            {active ? (
              <Html center distanceFactor={5} style={{ pointerEvents: "none" }}>
                <div className="landmark-label">
                  <strong>{lm.name}</strong>
                  <em>{lm.nameLatin}</em>
                </div>
              </Html>
            ) : null}
          </mesh>
        );
      })}
    </group>
  );
}
