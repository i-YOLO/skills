#!/usr/bin/env python3
"""Validate project contracts before asset, animation, or master work."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ASSET_TYPES = {"core", "interaction", "carrier", "support", "foreground", "background", "code"}
STAGES = ["script", "audio", "storyboard", "style", "assets", "scene_animation", "master"]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def require_keys(errors: list[str], value: dict, keys: list[str], label: str) -> None:
    for key in keys:
        if key not in value or value[key] in (None, "", []):
            error(errors, f"{label} 缺少 {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--stage", choices=["design", "pre-assets", "pre-animation", "pre-master", "master"], default="design")
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()
    project = args.project_dir.expanduser().resolve()
    required = [project / name for name in ("production-state.json", "storyboard.json", "assets.json", "captions.json")]
    errors: list[str] = []
    warnings: list[str] = []
    for path in required:
        if not path.is_file():
            error(errors, f"缺少项目文件：{path.name}")
    if errors:
        return report(errors, warnings)

    state, storyboard, assets, captions = map(read_json, required)
    fmt = state.get("format", {})
    require_keys(errors, fmt, ["width", "height", "fps", "safe_area_px"], "production-state.format")
    if isinstance(fmt.get("width"), int) and (fmt["width"] < 320 or fmt["width"] % 2):
        error(errors, "format.width 必须为不少于 320 的偶数")
    if isinstance(fmt.get("height"), int) and (fmt["height"] < 320 or fmt["height"] % 2):
        error(errors, "format.height 必须为不少于 320 的偶数")
    if fmt.get("fps") not in {24, 25, 30, 50, 60}:
        error(errors, "format.fps 必须为 24、25、30、50 或 60")
    if storyboard.get("format", {}).get("width") != fmt.get("width") or storyboard.get("format", {}).get("height") != fmt.get("height"):
        error(errors, "storyboard.format 与 production-state.format 尺寸不一致")
    if storyboard.get("format", {}).get("fps") != fmt.get("fps"):
        error(errors, "storyboard.format 与 production-state.format 帧率不一致")

    if not isinstance(captions, list):
        error(errors, "captions.json 必须为 Caption[] 数组")
    else:
        last_end = -1
        for index, caption in enumerate(captions):
            require_keys(errors, caption, ["text", "startMs", "endMs", "timestampMs"], f"caption[{index}]")
            if isinstance(caption.get("startMs"), (int, float)) and isinstance(caption.get("endMs"), (int, float)):
                if caption["endMs"] <= caption["startMs"]:
                    error(errors, f"caption[{index}] 的 endMs 必须大于 startMs")
                if caption["startMs"] < last_end:
                    warnings.append(f"caption[{index}] 与上一条字幕重叠；确认这是有意的。")
                last_end = max(last_end, caption["endMs"])

    scenes = storyboard.get("scenes", [])
    if not scenes:
        if not args.allow_draft:
            error(errors, "storyboard.json 尚无场景")
    else:
        expected_start = 0
        scene_ids: set[str] = set()
        for scene in scenes:
            label = f"scene[{scene.get('id', '?')}]"
            require_keys(errors, scene, ["id", "from_frame", "duration_frames", "narration", "knowledge_change", "visual_proposition", "focus_order", "shot_card", "layers", "beats"], label)
            scene_id = scene.get("id")
            if scene_id in scene_ids:
                error(errors, f"重复 scene id：{scene_id}")
            scene_ids.add(scene_id)
            if scene.get("from_frame") != expected_start:
                error(errors, f"{label} 应从第 {expected_start} 帧开始，当前为 {scene.get('from_frame')}")
            if not isinstance(scene.get("duration_frames"), int) or scene.get("duration_frames", 0) <= 0:
                error(errors, f"{label} 的 duration_frames 必须为正整数")
                continue
            expected_start += scene["duration_frames"]
            shot = scene.get("shot_card", {})
            require_keys(errors, shot, ["subject_scale", "facing", "common_ground", "occlusion_order", "subtitle_safe_lane"], f"{label}.shot_card")
            primary_count = 0
            secondary_count = 0
            layer_ids: set[str] = set()
            for layer in scene.get("layers", []):
                layer_label = f"{label}.layer[{layer.get('id', '?')}]"
                require_keys(errors, layer, ["id", "asset_id", "asset_type", "purpose", "focus_tier", "final_bounds", "motion"], layer_label)
                if layer.get("id") in layer_ids:
                    error(errors, f"{label} 存在重复 layer id：{layer.get('id')}")
                layer_ids.add(layer.get("id"))
                if layer.get("asset_type") not in ASSET_TYPES:
                    error(errors, f"{layer_label} 的 asset_type 不合法")
                if layer.get("focus_tier") == "primary":
                    primary_count += 1
                if layer.get("focus_tier") == "secondary":
                    secondary_count += 1
                bounds = layer.get("final_bounds", {})
                require_keys(errors, bounds, ["x", "y", "width", "height", "z_index"], f"{layer_label}.final_bounds")
            if primary_count > 1:
                error(errors, f"{label} 同屏主焦点超过 1 个")
            if secondary_count > 2:
                error(errors, f"{label} 同屏次焦点超过 2 个")
            for overlap in scene.get("intentional_overlaps", []):
                require_keys(errors, overlap, ["front_layer", "back_layer", "reason"], f"{label}.intentional_overlaps")
            for beat in scene.get("beats", []):
                require_keys(errors, beat, ["trigger", "target_frame", "visual_action"], f"{label}.beat")
        if fmt.get("duration_frames", 1) not in (None, 1) and expected_start != fmt.get("duration_frames"):
            error(errors, f"场景总帧数 {expected_start} 与 format.duration_frames {fmt.get('duration_frames')} 不一致")

    asset_rows = assets.get("assets", [])
    asset_ids: set[str] = set()
    for asset in asset_rows:
        label = f"asset[{asset.get('asset_id', '?')}]"
        require_keys(errors, asset, ["asset_id", "asset_type", "scene_ids", "purpose", "transparency_required", "status"], label)
        if asset.get("asset_id") in asset_ids:
            error(errors, f"重复 asset_id：{asset.get('asset_id')}")
        asset_ids.add(asset.get("asset_id"))
        if asset.get("asset_type") not in ASSET_TYPES:
            error(errors, f"{label} 的 asset_type 不合法")
        if asset.get("asset_type") != "code":
            require_keys(errors, asset, ["prompt_path"], label)

    required_locks = {
        "pre-assets": ["script", "audio", "storyboard", "style"],
        "pre-animation": ["script", "audio", "storyboard", "style", "assets"],
        "pre-master": ["script", "audio", "storyboard", "style", "assets", "scene_animation"],
        "master": STAGES[:-1],
    }.get(args.stage, [])
    for stage in required_locks:
        if state.get("locks", {}).get(stage, {}).get("human_approval") != "approved":
            error(errors, f"{args.stage} 前需要人工批准：{stage}")
    required_environment = {
        "pre-assets": ["audio", "assets"],
        "pre-animation": ["assets", "animation"],
        "pre-master": ["animation", "master"],
        "master": ["animation", "master"],
    }.get(args.stage, [])
    for environment_stage in required_environment:
        environment = state.get("environment", {})
        result = environment.get(environment_stage, {}).get("result") or environment.get("all", {}).get("result")
        if result != "pass":
            error(errors, f"{args.stage} 前环境预检未通过：{environment_stage}（当前：{result or '未记录'}）")
    if args.stage in {"pre-animation", "pre-master", "master"}:
        for asset in asset_rows:
            if asset.get("asset_type") == "code":
                continue
            if asset.get("status") != "approved":
                error(errors, f"{asset.get('asset_id')} 尚未批准")
            render_path = asset.get("render_path")
            if not render_path:
                error(errors, f"{asset.get('asset_id')} 缺少 render_path")
            elif not (project / render_path).is_file():
                error(errors, f"{asset.get('asset_id')} 的 render_path 不存在：{render_path}")
    return report(errors, warnings)


def report(errors: list[str], warnings: list[str]) -> int:
    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}")
    if errors:
        print(f"FAIL ({len(errors)} errors, {len(warnings)} warnings)")
        return 1
    print(f"PASS ({len(warnings)} warnings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
