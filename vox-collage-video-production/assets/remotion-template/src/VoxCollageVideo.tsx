import type {Caption} from "@remotion/captions";
import React from "react";
import {Audio, Easing, Img, interpolate, staticFile, useCurrentFrame} from "remotion";
import assetsJson from "../../assets.json";
import captionsJson from "../../captions.json";
import stateJson from "../../production-state.json";
import storyboardJson from "../../storyboard.json";
import {CaptionLayer} from "./Captions";
import type {Asset, AssetManifest, Bounds, Layer, MotionState, ProductionState, Storyboard} from "./types";

const state = stateJson as ProductionState;
const storyboard = storyboardJson as Storyboard;
const manifest = assetsJson as AssetManifest;
const captions = captionsJson as Caption[];
const assetById = new Map<string, Asset>(manifest.assets.map((asset) => [asset.asset_id, asset]));

const ease = Easing.bezier(0.16, 1, 0.3, 1);

const blend = (frame: number, state: MotionState | undefined, final: number, key: "x" | "y" | "rotate" | "opacity", fallback: number) => {
  if (!state) return final;
  const start = state[key] ?? fallback;
  const p = interpolate(frame, [state.start_frame, state.end_frame], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease});
  return interpolate(p, [0, 1], [start, final]);
};
const moveTo = (frame: number, state: MotionState | undefined, current: number, key: "x" | "y" | "rotate" | "opacity", fallback: number) => {
  if (!state) return current;
  const target = state[key] ?? fallback;
  const p = interpolate(frame, [state.start_frame, state.end_frame], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease});
  return interpolate(p, [0, 1], [current, target]);
};

const layerStyle = (frame: number, layer: Layer): React.CSSProperties => {
  const final = layer.final_bounds;
  const enter = layer.motion.enter;
  const exit = layer.motion.exit;
  let x = blend(frame, enter, final.x, "x", final.x);
  let y = blend(frame, enter, final.y, "y", final.y);
  let rotate = blend(frame, enter, final.rotate ?? 0, "rotate", final.rotate ?? 0);
  let opacity = blend(frame, enter, final.opacity ?? 1, "opacity", 0);
  let scale = enter ? interpolate(frame, [enter.start_frame, enter.end_frame], [enter.scale ?? 0.92, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease}) : 1;
  if (exit) {
    x = moveTo(frame, exit, x, "x", x);
    y = moveTo(frame, exit, y, "y", y);
    rotate = moveTo(frame, exit, rotate, "rotate", rotate);
    opacity = moveTo(frame, exit, opacity, "opacity", opacity);
    scale = interpolate(frame, [exit.start_frame, exit.end_frame], [scale, exit.scale ?? scale], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease});
  }
  return {position: "absolute", left: x, top: y, width: final.width, height: final.height, zIndex: final.z_index, opacity, transform: `rotate(${rotate}deg) scale(${scale})`, transformOrigin: "center"};
};

const ImageLayer: React.FC<{layer: Layer; frame: number}> = ({layer, frame}) => {
  const asset = assetById.get(layer.asset_id);
  if (!asset?.render_path) return null;
  return <Img src={staticFile(asset.render_path)} style={{...layerStyle(frame, layer), objectFit: "contain"}} />;
};

const CodeLayer: React.FC<{layer: Layer; frame: number}> = ({layer, frame}) => {
  const copy = layer.code_text ?? assetById.get(layer.asset_id)?.code_text ?? "";
  return <div style={{...layerStyle(frame, layer), display: "grid", placeItems: "center", background: "#174A8B", color: "#F5EEDC", borderLeft: "8px solid #C83D2E", fontFamily: '"PingFang SC", "Microsoft YaHei", sans-serif', fontSize: Math.max(18, layer.final_bounds.height * 0.18), fontWeight: 800, textAlign: "center", padding: "0.3em", boxSizing: "border-box"}}>{copy}</div>;
};

export const VoxCollageVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const scene = storyboard.scenes.find((item) => frame >= item.from_frame && frame < item.from_frame + item.duration_frames);
  const {width, height, fps, safe_area_px: safeArea} = state.format;
  return (
    <div style={{width, height, overflow: "hidden", position: "relative", background: "#E9DFC8", backgroundImage: "radial-gradient(rgba(23,74,139,0.08) 0.7px, transparent 0.7px)", backgroundSize: "7px 7px"}}>
      <Audio src={staticFile("audio/narration.wav")} />
      {scene?.layers.map((layer) => layer.asset_type === "code" ? <CodeLayer key={layer.id} layer={layer} frame={frame} /> : <ImageLayer key={layer.id} layer={layer} frame={frame} />)}
      <CaptionLayer captions={captions} fps={fps} area={safeArea.caption_reserved} />
    </div>
  );
};
