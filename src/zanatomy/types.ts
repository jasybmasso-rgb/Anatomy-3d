export type OriginalFile = {
  url: string;
  bytes: number;
  triangles: number;
  objects: number;
};

export type OriginalSystem = {
  id: string;
  label: string;
  defaultOn: boolean;
  triangles: number;
  objects: number;
  files: OriginalFile[];
};

export type CameraFrame = {
  eye: [number, number, number];
  target: [number, number, number];
};

export type OriginalManifest = {
  source: {
    repo: string;
    file: string;
    date: string;
    license: string;
    authors: string;
    upstream: string;
  };
  compression: {
    method: string;
    quantizePosition: number;
    quantizeNormal: number;
    quantizeTexcoord: number;
    decimated: boolean;
    note: string;
  };
  systems: OriginalSystem[];
  totalTriangles: number;
  totalBytes: number;
  frames: Record<string, { eye: number[]; target: number[] }>;
};

export function asFrame(value: { eye: number[]; target: number[] } | undefined): CameraFrame | null {
  if (!value || value.eye.length < 3 || value.target.length < 3) return null;
  return {
    eye: [value.eye[0], value.eye[1], value.eye[2]],
    target: [value.target[0], value.target[1], value.target[2]],
  };
}
