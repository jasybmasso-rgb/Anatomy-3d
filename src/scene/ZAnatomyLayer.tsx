import { useGLTF } from "@react-three/drei";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { chainClipSide, matchesChainSide, tintForStructureId, type ChainSide } from "../data/chains";
import { zaPartsForFile, type ZaPart } from "../data/zanatomy";
import type { StructureKind } from "../types/structure";
import { getDeviceProfile } from "./deviceProfile";
import { attachFatRaycast } from "./fatRaycast";
import { currentHighlightKey, registerHighlight, unregisterHighlight } from "./selectionHighlight";
import { DRACO_DECODER_PATH } from "./zanatomyAbdo";
import { zaMaterial } from "./zaMaterials";
import { clearZaFilePicks, setZaFilePicks } from "./zaPicks";

const RENDER_ORDER: Record<StructureKind, number> = {
  bone: 0,
  fascia: 2,
  organ: 3,
  muscle: 4,
  ligament: 5,
  vessel: 6,
  nerve: 7,
};

type Entry = {
  part: ZaPart;
  tint: string | null;
  clip: ChainSide;
  meshes: THREE.Mesh[];
};

function paintEntry(entry: Entry, selected: boolean) {
  const material = zaMaterial(entry.part, entry.tint, selected, entry.clip);
  for (const mesh of entry.meshes) mesh.material = material;
}

/** GLTF accessor min/max can lag a baked vertex transform. Frustum culling must use the vertices. */
function refreshBounds(geometry: THREE.BufferGeometry) {
  if (geometry.userData.zaBounds === 1) return;
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  geometry.userData.zaBounds = 1;
}

function meshTriangles(mesh: THREE.Mesh): number {
  const geo = mesh.geometry;
  if (geo.index) return geo.index.count / 3;
  const pos = geo.getAttribute("position");
  return pos ? pos.count / 3 : 0;
}

export type ZAnatomyFileProps = {
  url: string;
  file: string;
  layerVisible: boolean;
  /** Muscles stay hidden until “afficher tous”, a selection, or a chain. Bones ignore this. */
  showAll: boolean;
  selectedId: string | null;
  pinnedId: string | null;
  hiddenIds: string[];
  chainLayerOn: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
};

export function ZAnatomyFile({
  url,
  file,
  layerVisible,
  showAll,
  selectedId,
  pinnedId,
  hiddenIds,
  chainLayerOn,
  activeChainIds,
  chainSide,
}: ZAnatomyFileProps) {
  const gltf = useGLTF(url, DRACO_DECODER_PATH);
  const entries = useMemo(() => {
    const byNode = new Map<string, ZaPart>();
    for (const part of zaPartsForFile(file)) {
      for (const node of part.nodes) {
        byNode.set(node, part);
        // Three.js PropertyBinding.sanitizeNodeName: spaces → _, drop . : / [ ]
        byNode.set(node.replace(/\s/g, "_").replace(/[[\].:/]/g, ""), part);
      }
    }
    const grouped = new Map<string, Entry>();
    const partFor = (obj: THREE.Object3D): ZaPart | undefined => {
      let current: THREE.Object3D | null = obj;
      while (current) {
        const hit = byNode.get(current.name);
        if (hit) return hit;
        current = current.parent;
      }
      return undefined;
    };
    gltf.scene.traverse((obj) => {
      if (!(obj instanceof THREE.Mesh)) return;
      const part = partFor(obj);
      if (!part) return;
      let entry = grouped.get(part.id);
      if (!entry) {
        entry = { part, tint: null, clip: "both", meshes: [] };
        grouped.set(part.id, entry);
      }
      const geometry = obj.geometry;
      if (!geometry.getAttribute("normal")) geometry.computeVertexNormals();
      refreshBounds(geometry);
      obj.material = zaMaterial(part, null, false, "both");
      obj.userData.pick = part.kind;
      obj.userData.structureId = part.id;
      if (part.kind === "muscle") obj.userData.muscleId = part.id;
      obj.castShadow = part.kind === "bone" && getDeviceProfile().shadows;
      obj.receiveShadow = part.kind === "bone" && getDeviceProfile().shadows;
      obj.renderOrder = RENDER_ORDER[part.kind];
      obj.frustumCulled = true;
      const tris = meshTriangles(obj);
      const thin = part.kind === "nerve" || part.kind === "vessel" || part.kind === "ligament";
      if (thin && tris > 0 && tris < 4000) attachFatRaycast(obj, part.kind);
      else obj.raycast = THREE.Mesh.prototype.raycast;
      entry.meshes.push(obj);
    });
    return [...grouped.values()];
  }, [file, gltf]);

  useEffect(() => {
    for (const entry of entries) {
      registerHighlight(entry.part.kind, entry.part.id, (selected) => {
        paintEntry(entry, selected);
      });
    }
    return () => {
      for (const entry of entries) unregisterHighlight(entry.part.kind, entry.part.id);
    };
  }, [entries]);

  useEffect(() => {
    const hidden = new Set(hiddenIds);
    const chainOn = chainLayerOn && activeChainIds.length > 0;
    const pick: THREE.Mesh[] = [];
    const profile = getDeviceProfile();
    for (const entry of entries) {
      const part = entry.part;
      const forced = part.id === selectedId || part.id === pinnedId;
      const tintHex = chainOn ? tintForStructureId(part.id, activeChainIds) : null;
      const inChain = Boolean(tintHex);
      let on = !hidden.has(part.id);
      if (part.kind === "bone") {
        on = on && layerVisible;
      } else if (part.kind === "muscle") {
        const listed = layerVisible && (showAll || forced);
        on = on && (listed || inChain);
      } else {
        on = on && (layerVisible || inChain);
      }
      if (
        chainOn &&
        !forced &&
        (part.kind === "muscle" || part.kind === "fascia" || part.kind === "ligament") &&
        !matchesChainSide(part.id, chainSide)
      ) {
        on = false;
      }
      for (const mesh of entry.meshes) mesh.visible = on;
      if (!on) continue;
      entry.tint = tintHex;
      entry.clip =
        chainOn && part.kind === "muscle" && part.bilateral
          ? chainClipSide(part.id, chainSide, activeChainIds)
          : "both";
      const highlighted = currentHighlightKey() === `${part.kind}:${part.id}`;
      paintEntry(entry, part.id === selectedId || highlighted);
      for (const mesh of entry.meshes) {
        mesh.renderOrder = part.id === selectedId ? 12 : RENDER_ORDER[part.kind];
        mesh.castShadow = part.kind === "bone" && profile.shadows;
      }
      pick.push(...entry.meshes);
    }
    setZaFilePicks(entries[0]?.part.kind ?? "bone", file, pick);
    return () => clearZaFilePicks(entries[0]?.part.kind ?? "bone", file);
  }, [
    activeChainIds,
    chainLayerOn,
    chainSide,
    entries,
    file,
    hiddenIds,
    layerVisible,
    pinnedId,
    selectedId,
    showAll,
  ]);

  // Drop GPU buffers when the layer unmounts. The parsed GLB stays in the useGLTF
  // cache, so turning the layer back on re-uploads from CPU memory and does not re-download.
  useEffect(() => {
    return () => {
      const seen = new Set<THREE.BufferGeometry>();
      for (const entry of entries) {
        for (const mesh of entry.meshes) {
          const geo = mesh.geometry;
          if (!geo || seen.has(geo)) continue;
          seen.add(geo);
          geo.dispose();
        }
      }
    };
  }, [entries]);

  return <primitive object={gltf.scene} />;
}
