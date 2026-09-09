import { CameraControls } from "@react-three/drei";
import { useEffect, useRef } from "react";
import type { Muscle } from "../types/muscle";

export const DEFAULT_EYE: [number, number, number] = [1.62, 0.4, 2.15];
export const DEFAULT_TARGET: [number, number, number] = [0, 0.08, 0];

export function CameraRig({ muscle }: { muscle: Muscle | null }) {
  const controls = useRef<CameraControls>(null);

  useEffect(() => {
    const cam = controls.current;
    if (!cam) return;

    if (!muscle) {
      const [ex, ey, ez] = DEFAULT_EYE;
      const [tx, ty, tz] = DEFAULT_TARGET;
      void cam.setLookAt(ex, ey, ez, tx, ty, tz, true);
      return;
    }

    const [tx, ty, tz] = muscle.focus.position;
    const d = muscle.focus.distance;
    void cam.setLookAt(tx + d * 0.42, ty + d * 0.18, tz + d * 0.88, tx, ty, tz, true);
  }, [muscle]);

  return (
    <CameraControls
      ref={controls}
      minDistance={0.35}
      maxDistance={6}
      smoothTime={0.38}
      draggingSmoothTime={0.1}
    />
  );
}
