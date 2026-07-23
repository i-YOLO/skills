import React from "react";
import {Composition} from "remotion";
import stateJson from "../../production-state.json";
import {VoxCollageVideo} from "./VoxCollageVideo";
import type {ProductionState} from "./types";

const state = stateJson as ProductionState;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="VoxCollageVideo"
    component={VoxCollageVideo}
    durationInFrames={Math.max(1, state.format.duration_frames)}
    fps={state.format.fps}
    width={state.format.width}
    height={state.format.height}
  />
);
