import { Suspense } from "react";
import type { ChainSide } from "../data/chains";
import { publicUrl } from "../lib/publicUrl";
import { FLOOR_Y } from "./landmarks";
import { ZAnatomyFile } from "./ZAnatomyLayer";

type ZAnatomyBodyProps = {
  showMuscles: boolean;
  showAllMuscles: boolean;
  pinnedMuscleId: string | null;
  hiddenMuscleIds: string[];
  hiddenFasciaIds: string[];
  hiddenLigamentIds: string[];
  hiddenNerveIds: string[];
  hiddenOrganIds: string[];
  hiddenVesselIds: string[];
  hiddenBoneIds: string[];
  showLigaments: boolean;
  showFascia: boolean;
  showNerves: boolean;
  showOrgans: boolean;
  showVessels: boolean;
  showChains: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
  selectedId: string | null;
};

const NONE: string[] = [];

export default function ZAnatomyBody({
  showMuscles,
  showAllMuscles,
  pinnedMuscleId,
  hiddenMuscleIds,
  hiddenFasciaIds,
  hiddenLigamentIds,
  hiddenNerveIds,
  hiddenOrganIds,
  hiddenVesselIds,
  hiddenBoneIds,
  showLigaments,
  showFascia,
  showNerves,
  showOrgans,
  showVessels,
  showChains,
  activeChainIds,
  chainSide,
  selectedId,
}: ZAnatomyBodyProps) {
  const chain = {
    chainLayerOn: showChains,
    activeChainIds,
    chainSide,
    selectedId,
    pinnedId: pinnedMuscleId,
  };
  return (
    <group name="zanatomy">
      <Suspense fallback={null}>
        <ZAnatomyFile
          url={publicUrl("/models/zanatomy/squelette.glb")}
          file="squelette"
          layerVisible
          showAll
          hiddenIds={hiddenBoneIds}
          {...chain}
        />
      </Suspense>
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, FLOOR_Y, 0]}
        receiveShadow
        userData={{ pick: "ignore" }}
        raycast={() => null}
      >
        <circleGeometry args={[1.8, 48]} />
        <meshStandardMaterial color="#1b2432" roughness={1} metalness={0} />
      </mesh>
      {showMuscles || showChains ? (
        <Suspense fallback={null}>
          <ZAnatomyFile
            url={publicUrl("/models/zanatomy/muscles.glb")}
            file="muscles"
            layerVisible={showMuscles}
            showAll={showAllMuscles}
            hiddenIds={hiddenMuscleIds}
            {...chain}
          />
        </Suspense>
      ) : null}
      {showFascia || showChains ? (
        <Suspense fallback={null}>
          <ZAnatomyFile
            url={publicUrl("/models/zanatomy/fascias.glb")}
            file="fascias"
            layerVisible={showFascia}
            showAll
            hiddenIds={hiddenFasciaIds}
            {...chain}
          />
        </Suspense>
      ) : null}
      {showLigaments || showChains ? (
        <Suspense fallback={null}>
          <ZAnatomyFile
            url={publicUrl("/models/zanatomy/ligaments.glb")}
            file="ligaments"
            layerVisible={showLigaments}
            showAll
            hiddenIds={hiddenLigamentIds}
            {...chain}
          />
        </Suspense>
      ) : null}
      {showNerves ? (
        <Suspense fallback={null}>
          <ZAnatomyFile
            url={publicUrl("/models/zanatomy/nerfs.glb")}
            file="nerfs"
            layerVisible
            showAll
            hiddenIds={hiddenNerveIds}
            chainLayerOn={false}
            activeChainIds={NONE}
            chainSide="both"
            selectedId={selectedId}
            pinnedId={null}
          />
        </Suspense>
      ) : null}
      {showOrgans || showChains ? (
        <Suspense fallback={null}>
          <ZAnatomyFile
            url={publicUrl("/models/zanatomy/organes.glb")}
            file="organes"
            layerVisible={showOrgans}
            showAll
            hiddenIds={hiddenOrganIds}
            {...chain}
          />
        </Suspense>
      ) : null}
      {showOrgans ? (
        <Suspense fallback={null}>
          <ZAnatomyFile
            url={publicUrl("/models/zanatomy/organes-snc.glb")}
            file="organes-snc"
            layerVisible
            showAll
            hiddenIds={hiddenOrganIds}
            chainLayerOn={false}
            activeChainIds={NONE}
            chainSide="both"
            selectedId={selectedId}
            pinnedId={null}
          />
        </Suspense>
      ) : null}
      {showVessels ? (
        <Suspense fallback={null}>
          <ZAnatomyFile
            url={publicUrl("/models/zanatomy/vaisseaux.glb")}
            file="vaisseaux"
            layerVisible
            showAll
            hiddenIds={hiddenVesselIds}
            chainLayerOn={false}
            activeChainIds={NONE}
            chainSide="both"
            selectedId={selectedId}
            pinnedId={null}
          />
          <ZAnatomyFile
            url={publicUrl("/models/zanatomy/vaisseaux-extremites.glb")}
            file="vaisseaux-extremites"
            layerVisible
            showAll
            hiddenIds={hiddenVesselIds}
            chainLayerOn={false}
            activeChainIds={NONE}
            chainSide="both"
            selectedId={selectedId}
            pinnedId={null}
          />
        </Suspense>
      ) : null}
    </group>
  );
}
