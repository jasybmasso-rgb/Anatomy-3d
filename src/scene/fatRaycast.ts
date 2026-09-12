import * as THREE from "three";

const PICK_PAD: Record<string, number> = {
  ligament: 0.0075,
  nerve: 0.0065,
  vessel: 0.0055,
  fascia: 0.0035,
  organ: 0.002,
  muscle: 0,
};

/** Inflate a mesh along normals so thin tubes/sheets stay clickable. */
export function attachFatRaycast(mesh: THREE.Mesh, kind: string) {
  const padding = PICK_PAD[kind] ?? 0;
  if (padding <= 0) {
    mesh.raycast = THREE.Mesh.prototype.raycast;
    return;
  }
  const visual = mesh.geometry;
  if (!visual.getAttribute("normal")) visual.computeVertexNormals();
  const pick = visual.clone();
  const pos = pick.getAttribute("position") as THREE.BufferAttribute;
  const nrm = pick.getAttribute("normal") as THREE.BufferAttribute | undefined;
  if (!nrm) {
    mesh.raycast = THREE.Mesh.prototype.raycast;
    return;
  }
  for (let i = 0; i < pos.count; i += 1) {
    pos.setXYZ(
      i,
      pos.getX(i) + nrm.getX(i) * padding,
      pos.getY(i) + nrm.getY(i) * padding,
      pos.getZ(i) + nrm.getZ(i) * padding,
    );
  }
  pos.needsUpdate = true;
  pick.computeBoundingSphere();
  pick.computeBoundingBox();
  mesh.userData.pickGeometry = pick;
  mesh.raycast = function fatRaycast(raycaster: THREE.Raycaster, intersects: THREE.Intersection[]) {
    const before = intersects.length;
    THREE.Mesh.prototype.raycast.call(this, raycaster, intersects);
    if (intersects.length > before) return;
    this.geometry = pick;
    THREE.Mesh.prototype.raycast.call(this, raycaster, intersects);
    this.geometry = visual;
  };
}
