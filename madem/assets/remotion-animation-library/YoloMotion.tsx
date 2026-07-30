import React from "react";
import {
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type YoloFacing = "left" | "right";
export type YoloMotionOutcome = string;
export type YoloMotionSlot = "lower-left" | "lower-right";

type PropTransform = {
  x: number;
  y: number;
  rotation: number;
  opacity: number;
};

type MotionPropTransform = PropTransform & {
  id: string;
};

type MotionFrame = {
  file: string;
  ticks: number;
  prop?: PropTransform;
  props?: MotionPropTransform[];
  sha256: string;
};

type FacingManifest = {
  common: MotionFrame[];
  branches: Record<YoloMotionOutcome, MotionFrame[]>;
};

type MotionManifest = {
  asset_id: string;
  playback_mode: "loop" | "one-shot-with-settled-hold";
  outcomes: YoloMotionOutcome[];
  phases: {
    anticipation_tick: number;
    inspect_tick: number;
    scan_end_tick: number;
    outcome_tick: number;
    settled_tick: number;
    total_ticks: number;
  };
  facings: Record<YoloFacing, FacingManifest>;
};

export type YoloMotionCatalog = {
  source_fps: number;
  production: {
    canvas: [number, number];
    subject_height_px: number;
    foot_anchor: [number, number];
    default_display_height_1080p: number;
    max_display_height_1080p: number;
    content_max_y_1080p: number;
    reserved_slots_1080p: Record<
      YoloMotionSlot,
      {x_min: number; x_max: number; y_min: number; y_max: number}
    >;
  };
  props: {
    [id: string]: {
      file: string;
      canvas: [number, number];
      logical_width: number;
      grip_anchor: Record<YoloFacing, [number, number]>;
      mirror_for_left: boolean;
    };
  };
  motions: MotionManifest[];
};

export type YoloMotionTiming = {
  startFrame: number;
  inspectFrame?: number;
  outcomeFrame?: number;
  settledFrame?: number;
};

export type YoloMotionProps = {
  catalog: YoloMotionCatalog;
  motionId?: string;
  facing: YoloFacing;
  outcome?: YoloMotionOutcome;
  assetBase?: string;
  displayHeight?: number;
  slot?: YoloMotionSlot;
  anchorX?: number;
  bottomY?: number;
  timing?: YoloMotionTiming;
  freezeAtEnd?: boolean;
  zIndex?: number;
};

const clamp = (value: number, minimum: number, maximum: number) =>
  Math.max(minimum, Math.min(maximum, value));

const mapRange = (
  value: number,
  inputStart: number,
  inputEnd: number,
  outputStart: number,
  outputEnd: number,
) => {
  if (inputEnd <= inputStart) return outputEnd;
  const progress = clamp(
    (value - inputStart) / (inputEnd - inputStart),
    0,
    1,
  );
  return outputStart + (outputEnd - outputStart) * progress;
};

const resolveSourceTick = (
  frame: number,
  fps: number,
  sourceFps: number,
  phases: MotionManifest["phases"],
  timing: YoloMotionTiming | undefined,
) => {
  const start = timing?.startFrame ?? 0;
  if (!timing) {
    return Math.floor(Math.max(0, frame - start) * (sourceFps / fps));
  }

  const inspect =
    timing.inspectFrame ??
    start + Math.round((phases.inspect_tick / sourceFps) * fps);
  const outcome =
    timing.outcomeFrame ??
    start + Math.round((phases.outcome_tick / sourceFps) * fps);
  const settled =
    timing.settledFrame ??
    start + Math.round((phases.settled_tick / sourceFps) * fps);

  if (frame <= inspect) {
    return Math.floor(
      mapRange(frame, start, inspect, 0, phases.inspect_tick),
    );
  }
  if (frame <= outcome) {
    return Math.floor(
      mapRange(
        frame,
        inspect,
        outcome,
        phases.inspect_tick,
        phases.outcome_tick,
      ),
    );
  }
  return Math.floor(
    mapRange(
      frame,
      outcome,
      settled,
      phases.outcome_tick,
      phases.settled_tick,
    ),
  );
};

const frameAtTick = (frames: MotionFrame[], tick: number) => {
  let cursor = 0;
  for (const frame of frames) {
    const end = cursor + frame.ticks;
    if (tick < end) return frame;
    cursor = end;
  }
  return frames[frames.length - 1];
};

export const YoloMotion: React.FC<YoloMotionProps> = ({
  catalog,
  motionId = "yolo-verify-source",
  facing,
  outcome,
  assetBase = "assets/ip/yolo-motion-v1",
  displayHeight,
  slot = facing === "right" ? "lower-left" : "lower-right",
  anchorX,
  bottomY,
  timing,
  freezeAtEnd,
  zIndex = 3,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const motion = catalog.motions.find(
    (candidate) => candidate.asset_id === motionId,
  );
  if (!motion) {
    throw new Error(`Unknown YOLO motion asset: ${motionId}`);
  }
  const resolvedOutcome = outcome ?? motion.outcomes[0];
  if (!motion.outcomes.includes(resolvedOutcome)) {
    throw new Error(`Unsupported ${motionId} outcome: ${resolvedOutcome}`);
  }

  const height =
    displayHeight ?? catalog.production.default_display_height_1080p;
  if (height > catalog.production.max_display_height_1080p) {
    throw new Error(
      `YOLO displayHeight ${height}px exceeds ${catalog.production.max_display_height_1080p}px`,
    );
  }

  const facingManifest = motion.facings[facing];
  const frames = [
    ...facingManifest.common,
    ...facingManifest.branches[resolvedOutcome],
  ];
  const rawTick = resolveSourceTick(
    frame,
    fps,
    catalog.source_fps,
    motion.phases,
    timing,
  );
  const shouldFreeze =
    freezeAtEnd ?? motion.playback_mode !== "loop";
  const sourceTick = shouldFreeze
    ? clamp(rawTick, 0, motion.phases.total_ticks - 1)
    : ((rawTick % motion.phases.total_ticks) + motion.phases.total_ticks) %
      motion.phases.total_ticks;
  const current = frameAtTick(frames, sourceTick);

  const [canvasWidth] = catalog.production.canvas;
  const subjectScale = height / catalog.production.subject_height_px;
  const canvasDisplaySize = canvasWidth * subjectScale;
  const [footX, footY] = catalog.production.foot_anchor;
  const reserved = catalog.production.reserved_slots_1080p[slot];
  const resolvedAnchorX =
    anchorX ?? (reserved.x_min + reserved.x_max) / 2;
  const resolvedBottomY =
    bottomY ?? Math.min(reserved.y_max, catalog.production.content_max_y_1080p);
  const left = resolvedAnchorX - footX * subjectScale;
  const top = resolvedBottomY - footY * subjectScale;

  const activeProps: MotionPropTransform[] =
    current.props ??
    (current.prop ? [{id: "magnifier", ...current.prop}] : []);

  return (
    <div
      aria-label={`${motionId}-${facing}-${resolvedOutcome}`}
      style={{
        position: "absolute",
        left,
        top,
        width: canvasDisplaySize,
        height: canvasDisplaySize,
        zIndex,
        pointerEvents: "none",
      }}
    >
      <Img
        src={staticFile(`${assetBase}/${current.file}`)}
        style={{position: "absolute", inset: 0, width: "100%", height: "100%"}}
      />
      {activeProps.map((track, index) => {
        const prop = catalog.props[track.id];
        if (!prop) {
          throw new Error(`Unknown YOLO prop asset: ${track.id}`);
        }
        if (track.opacity <= 0) return null;
        const propWidth = prop.logical_width;
        const [gripX, gripY] = prop.grip_anchor[facing];
        const propLeft = track.x - propWidth * gripX;
        const propTop = track.y - propWidth * gripY;
        const mirror =
          facing === "left" && prop.mirror_for_left ? -1 : 1;
        return (
          <Img
            key={`${track.id}-${index}`}
            src={staticFile(`${assetBase}/${prop.file}`)}
            style={{
              position: "absolute",
              left: propLeft * subjectScale,
              top: propTop * subjectScale,
              width: propWidth * subjectScale,
              height: propWidth * subjectScale,
              opacity: track.opacity,
              transformOrigin: `${gripX * 100}% ${gripY * 100}%`,
              transform: `rotate(${track.rotation}deg) scaleX(${mirror})`,
            }}
          />
        );
      })}
    </div>
  );
};
