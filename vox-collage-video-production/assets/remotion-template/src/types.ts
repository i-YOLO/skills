export type Bounds = {
  x: number;
  y: number;
  width: number;
  height: number;
  z_index: number;
  rotate?: number;
  opacity?: number;
};

export type MotionState = {
  start_frame: number;
  end_frame: number;
  x?: number;
  y?: number;
  scale?: number;
  rotate?: number;
  opacity?: number;
};

export type Layer = {
  id: string;
  asset_id: string;
  asset_type: "core" | "interaction" | "carrier" | "support" | "foreground" | "background" | "code";
  purpose: string;
  focus_tier: "primary" | "secondary" | "tertiary" | "ambient";
  final_bounds: Bounds;
  motion: {enter?: MotionState; exit?: MotionState};
  code_text?: string;
};

export type Scene = {
  id: string;
  from_frame: number;
  duration_frames: number;
  layers: Layer[];
};

export type ProductionState = {
  format: {
    width: number;
    height: number;
    fps: number;
    duration_frames: number;
    safe_area_px: {caption_reserved: {x: number; y: number; width: number; height: number}};
  };
};

export type Storyboard = {scenes: Scene[]};

export type Asset = {asset_id: string; render_path?: string; code_text?: string};
export type AssetManifest = {assets: Asset[]};
