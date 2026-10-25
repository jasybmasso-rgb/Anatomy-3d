import type { ChainSide } from "../data/chains";
import { nerves, organs, vessels } from "../data/loadViscera";
import { Fascia } from "./Fascia";
import { Ligaments } from "./Ligaments";
import { MuscleLayer } from "./MuscleLayer";
import { Skeleton } from "./Skeleton";
import { VisceraLayer } from "./VisceraLayer";

type ProceduralBodyProps = {
  showMuscles: boolean;
  showAllMuscles: boolean;
  pinnedMuscleId: string | null;
  selectedMuscleId: string | null;
  hiddenMuscleIds: string[];
  hiddenFasciaIds: string[];
  hiddenLigamentIds: string[];
  hiddenNerveIds: string[];
  hiddenOrganIds: string[];
  hiddenVesselIds: string[];
  showLigaments: boolean;
  showFascia: boolean;
  showNerves: boolean;
  showOrgans: boolean;
  showVessels: boolean;
  showChains: boolean;
  activeChainIds: string[];
  chainSide: ChainSide;
  selectedKind: string | null;
  selectedId: string | null;
};

export default function ProceduralBody(props: ProceduralBodyProps) {
  return (
    <group name="procedural">
      <Skeleton />
      {props.showFascia || props.showChains ? (
        <Fascia
          layerVisible={props.showFascia}
          selectedId={props.selectedKind === "fascia" ? props.selectedId : null}
          hiddenIds={props.hiddenFasciaIds}
          chainLayerOn={props.showChains}
          activeChainIds={props.activeChainIds}
          chainSide={props.chainSide}
        />
      ) : null}
      {props.showLigaments ? (
        <Ligaments
          visible={props.showLigaments}
          selectedId={props.selectedKind === "ligament" ? props.selectedId : null}
          hiddenIds={props.hiddenLigamentIds}
        />
      ) : null}
      {props.showOrgans ? (
        <VisceraLayer
          url="/models/organs.glb"
          parts={organs}
          kind="organ"
          visible={props.showOrgans}
          selectedId={props.selectedKind === "organ" ? props.selectedId : null}
          hiddenIds={props.hiddenOrganIds}
        />
      ) : null}
      {props.showVessels ? (
        <VisceraLayer
          url="/models/vessels.glb"
          parts={vessels}
          kind="vessel"
          visible={props.showVessels}
          selectedId={props.selectedKind === "vessel" ? props.selectedId : null}
          hiddenIds={props.hiddenVesselIds}
        />
      ) : null}
      {props.showNerves ? (
        <VisceraLayer
          url="/models/nerves.glb"
          parts={nerves}
          kind="nerve"
          visible={props.showNerves}
          selectedId={props.selectedKind === "nerve" ? props.selectedId : null}
          hiddenIds={props.hiddenNerveIds}
        />
      ) : null}
      <MuscleLayer
        selectedMuscleId={props.selectedMuscleId}
        pinnedMuscleId={props.pinnedMuscleId}
        showMuscles={props.showMuscles}
        showAllMuscles={props.showAllMuscles}
        hiddenMuscleIds={props.hiddenMuscleIds}
        chainLayerOn={props.showChains}
        activeChainIds={props.activeChainIds}
        chainSide={props.chainSide}
      />
    </group>
  );
}
