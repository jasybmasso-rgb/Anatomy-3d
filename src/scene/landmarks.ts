export type Vec3 = [number, number, number];

/** Plancher sous les pieds (origine monde près du bassin, Y-up, stature ~1,7 m). */
export const FLOOR_Y = -0.9;

export const LANDMARKS = {
  skull: [0, 0.66, 0.02] as Vec3,
  c7: [0, 0.5, -0.02] as Vec3,
  sternum: [0, 0.32, 0.07] as Vec3,
  xiphoid: [0, 0.18, 0.06] as Vec3,
  pelvis: [0, 0, 0] as Vec3,
  rAcromion: [-0.18, 0.5, 0] as Vec3,
  lAcromion: [0.18, 0.5, 0] as Vec3,
  rElbow: [-0.22, 0.18, 0.02] as Vec3,
  lElbow: [0.22, 0.18, 0.02] as Vec3,
  rWrist: [-0.22, -0.1, 0.03] as Vec3,
  lWrist: [0.22, -0.1, 0.03] as Vec3,
  rHip: [-0.09, -0.04, 0] as Vec3,
  lHip: [0.09, -0.04, 0] as Vec3,
  rKnee: [-0.1, -0.42, 0.02] as Vec3,
  lKnee: [0.1, -0.42, 0.02] as Vec3,
  rAnkle: [-0.1, -0.82, 0] as Vec3,
  lAnkle: [0.1, -0.82, 0] as Vec3,
  rFoot: [-0.1, -0.88, 0.08] as Vec3,
  lFoot: [0.1, -0.88, 0.08] as Vec3,
  rScapula: [-0.14, 0.42, -0.08] as Vec3,
  lScapula: [0.14, 0.42, -0.08] as Vec3,
} as const;

export function mirrorX([x, y, z]: Vec3): Vec3 {
  return [-x, y, z];
}
