export type Vec3 = [number, number, number];

/** Plancher sous les pieds (origine monde près du bassin, Y-up, stature ~1,7 m). */
export const FLOOR_Y = -0.932;

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

/** Bassin si les pieds sont à Y = 0 (stature ~1,7 m). */
export const PELVIS_Y_FROM_FEET = 0.9;
const FOCUS_Y_MIN = FLOOR_Y + 0.04;
const FOCUS_Y_MAX = 0.86;

/**
 * Convertit `focus.position` vers l’espace des landmarks (origine bassin).
 * Accepte aussi un jeu « pieds à Y=0 » (tête ~1,6–1,7).
 */
export function toLandmarkFocus(position: Vec3): Vec3 {
  let [x, y, z] = position;
  if (y > 0.82) {
    y -= PELVIS_Y_FROM_FEET;
  }
  y = Math.min(FOCUS_Y_MAX, Math.max(FOCUS_Y_MIN, y));
  x = Math.min(0.45, Math.max(-0.45, x));
  z = Math.min(0.28, Math.max(-0.28, z));
  return [x, y, z];
}
