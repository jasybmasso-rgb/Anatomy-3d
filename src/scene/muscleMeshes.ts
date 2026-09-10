import type { Muscle } from "../types/muscle";
import { mirrorX, toLandmarkFocus, type Vec3 } from "./landmarks";

export type CapsulePrim = {
  kind: "capsule";
  from: Vec3;
  to: Vec3;
  radius: number;
  bilateral?: boolean;
};

export type BoxPrim = {
  kind: "box";
  position: Vec3;
  rotation: Vec3;
  size: Vec3;
  bilateral?: boolean;
};

export type MusclePrim = CapsulePrim | BoxPrim;

const HINTS: Record<string, MusclePrim[]> = {
  "fusiform-bras-ant": [
    { kind: "capsule", from: [-0.19, 0.46, 0.045], to: [-0.215, 0.2, 0.05], radius: 0.03, bilateral: true },
  ],
  "triceps-bras-post": [
    { kind: "capsule", from: [-0.19, 0.48, -0.04], to: [-0.215, 0.19, -0.045], radius: 0.032, bilateral: true },
    { kind: "capsule", from: [-0.14, 0.46, -0.07], to: [-0.21, 0.22, -0.04], radius: 0.022, bilateral: true },
  ],
  "delta-epaule": [
    { kind: "capsule", from: [-0.14, 0.5, 0.05], to: [-0.23, 0.4, 0.02], radius: 0.03, bilateral: true },
    { kind: "capsule", from: [-0.2, 0.54, 0], to: [-0.24, 0.4, 0], radius: 0.034, bilateral: true },
    { kind: "capsule", from: [-0.14, 0.5, -0.05], to: [-0.23, 0.4, -0.03], radius: 0.028, bilateral: true },
  ],
  "eventail-pectoral": [
    { kind: "capsule", from: [-0.02, 0.4, 0.09], to: [-0.18, 0.46, 0.04], radius: 0.028, bilateral: true },
    { kind: "capsule", from: [-0.02, 0.3, 0.09], to: [-0.18, 0.42, 0.04], radius: 0.03, bilateral: true },
    { kind: "capsule", from: [-0.02, 0.22, 0.08], to: [-0.17, 0.4, 0.03], radius: 0.024, bilateral: true },
  ],
  "nappe-dorsale": [
    { kind: "capsule", from: [-0.05, 0.02, -0.08], to: [-0.18, 0.42, -0.02], radius: 0.03, bilateral: true },
    { kind: "capsule", from: [-0.08, 0.12, -0.09], to: [-0.16, 0.38, -0.04], radius: 0.026, bilateral: true },
  ],
  "losange-trapeze": [
    { kind: "capsule", from: [0, 0.64, -0.02], to: [-0.16, 0.5, 0], radius: 0.022, bilateral: true },
    { kind: "capsule", from: [0, 0.44, -0.07], to: [-0.14, 0.46, -0.06], radius: 0.02, bilateral: true },
    { kind: "capsule", from: [0, 0.24, -0.06], to: [-0.1, 0.42, -0.08], radius: 0.018, bilateral: true },
  ],
  "sangle-scm": [
    { kind: "capsule", from: [-0.02, 0.42, 0.065], to: [-0.055, 0.64, 0.04], radius: 0.016, bilateral: true },
  ],
  "ischio-lat": [
    { kind: "capsule", from: [-0.06, -0.06, -0.05], to: [-0.12, -0.42, -0.05], radius: 0.028, bilateral: true },
  ],
  "ischio-med-sup": [
    { kind: "capsule", from: [-0.05, -0.06, -0.04], to: [-0.06, -0.44, -0.02], radius: 0.022, bilateral: true },
  ],
  "ischio-med-prof": [
    { kind: "capsule", from: [-0.055, -0.05, -0.035], to: [-0.055, -0.42, -0.03], radius: 0.024, bilateral: true },
  ],
  "quadriceps-droit": [
    { kind: "capsule", from: [-0.08, 0.02, 0.06], to: [-0.1, -0.4, 0.065], radius: 0.028, bilateral: true },
  ],
  "quadriceps-lat": [
    { kind: "capsule", from: [-0.13, -0.08, 0.0], to: [-0.12, -0.4, 0.02], radius: 0.032, bilateral: true },
  ],
  "quadriceps-med": [
    { kind: "capsule", from: [-0.055, -0.1, 0.025], to: [-0.075, -0.4, 0.045], radius: 0.028, bilateral: true },
  ],
  "quadriceps-prof": [
    { kind: "capsule", from: [-0.1, -0.08, 0.035], to: [-0.1, -0.38, 0.04], radius: 0.024, bilateral: true },
  ],
  "eventail-fessier": [
    { kind: "capsule", from: [-0.03, 0.05, -0.08], to: [-0.13, -0.1, -0.03], radius: 0.04, bilateral: true },
    { kind: "capsule", from: [-0.06, 0.02, -0.1], to: [-0.12, -0.14, -0.05], radius: 0.032, bilateral: true },
  ],
  "iliopsoas-profond": [
    { kind: "capsule", from: [0.02, 0.18, 0.02], to: [-0.08, -0.08, 0.03], radius: 0.024, bilateral: true },
  ],
  "jumeaux-mollet": [
    { kind: "capsule", from: [-0.08, -0.42, -0.03], to: [-0.1, -0.78, -0.045], radius: 0.026, bilateral: true },
    { kind: "capsule", from: [-0.12, -0.42, -0.03], to: [-0.1, -0.78, -0.045], radius: 0.026, bilateral: true },
  ],
  "soleaire-mollet": [
    { kind: "capsule", from: [-0.1, -0.5, -0.03], to: [-0.1, -0.8, -0.035], radius: 0.028, bilateral: true },
  ],
  "tibial-ant": [
    { kind: "capsule", from: [-0.1, -0.44, 0.045], to: [-0.1, -0.8, 0.055], radius: 0.02, bilateral: true },
  ],
  "droit-abdominal": [
    { kind: "capsule", from: [-0.035, -0.06, 0.085], to: [-0.03, 0.24, 0.085], radius: 0.022 },
    { kind: "capsule", from: [0.035, -0.06, 0.085], to: [0.03, 0.24, 0.085], radius: 0.022 },
  ],
  "oblique-lat": [
    { kind: "capsule", from: [-0.13, 0.28, 0.06], to: [-0.12, -0.02, 0.07], radius: 0.028, bilateral: true },
  ],
  "coiffe-supra": [
    { kind: "capsule", from: [-0.14, 0.53, -0.06], to: [-0.2, 0.5, 0.0], radius: 0.016, bilateral: true },
  ],
};

function fallbackFromFocus(muscle: Muscle): MusclePrim[] {
  const [x, y, z] = toLandmarkFocus(muscle.focus.position);
  return [
    {
      kind: "capsule",
      from: [x, y + 0.08, z],
      to: [x, y - 0.08, z],
      radius: 0.03,
    },
  ];
}

export function primitivesForMuscle(muscle: Muscle): MusclePrim[] {
  const listed = (muscle.meshHint && HINTS[muscle.meshHint]) || fallbackFromFocus(muscle);
  const out: MusclePrim[] = [];
  for (const prim of listed) {
    out.push(prim);
    if (!prim.bilateral) continue;
    if (prim.kind === "capsule") {
      out.push({
        ...prim,
        from: mirrorX(prim.from),
        to: mirrorX(prim.to),
        bilateral: false,
      });
    } else {
      out.push({
        ...prim,
        position: mirrorX(prim.position),
        rotation: [prim.rotation[0], -prim.rotation[1], -prim.rotation[2]],
        bilateral: false,
      });
    }
  }
  return out;
}
