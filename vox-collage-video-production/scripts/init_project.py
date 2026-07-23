#!/usr/bin/env python3
"""Initialize a review-gated VOX collage video project."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


PRESETS: dict[str, tuple[int, int]] = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}
STAGES = ["script", "audio", "storyboard", "style", "assets", "scene_animation", "master"]


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_id(title: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return value or "vox-collage-video"


def safe_area(width: int, height: int) -> dict[str, object]:
    left = round(width * 0.07)
    right = left
    top = round(height * 0.07)
    bottom = round(height * 0.065)
    caption_height = round(height * 0.16)
    return {
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom,
        "caption_reserved": {
            "x": left,
            "y": height - bottom - caption_height,
            "width": width - left - right,
            "height": caption_height,
        },
    }


def resolve_format(args: argparse.Namespace) -> tuple[str, int, int]:
    if args.width is not None or args.height is not None:
        if args.width is None or args.height is None:
            raise ValueError("自定义尺寸必须同时提供 --width 与 --height")
        return "custom", args.width, args.height
    if args.format not in PRESETS:
        raise ValueError(f"未知预设：{args.format}")
    width, height = PRESETS[args.format]
    return args.format, width, height


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--format", choices=[*PRESETS, "custom"], default="16:9")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    try:
        format_name, width, height = resolve_format(args)
    except ValueError as exc:
        parser.error(str(exc))
    if width < 320 or height < 320 or width % 2 or height % 2:
        parser.error("宽高必须为不少于 320 的偶数")
    if args.fps not in {24, 25, 30, 50, 60}:
        parser.error("fps 仅支持 24、25、30、50 或 60")

    project_dir = args.project_dir.expanduser().resolve()
    if project_dir.exists() and any(project_dir.iterdir()):
        parser.error(f"目标目录非空，拒绝覆盖：{project_dir}")
    project_dir.mkdir(parents=True, exist_ok=True)
    for relative in (
        "audio/source",
        "audio/transcription",
        "assets/source",
        "assets/transparent",
        "assets/review",
        "design/prompts",
        "design/lookdev",
        "reviews",
        "remotion/public/assets",
        "remotion/public/audio",
    ):
        (project_dir / relative).mkdir(parents=True, exist_ok=True)

    skill_root = Path(__file__).resolve().parents[1]
    template = skill_root / "assets" / "remotion-template"
    if not template.exists():
        raise RuntimeError(f"缺少 Remotion 模板：{template}")
    shutil.copytree(template, project_dir / "remotion", dirs_exist_ok=True)

    fmt = {
        "preset": format_name,
        "width": width,
        "height": height,
        "fps": args.fps,
        "duration_seconds": None,
        "duration_frames": 1,
        "safe_area_px": safe_area(width, height),
    }
    locks = {
        stage: {
            "self_review": "pending",
            "human_approval": "pending",
            "reports": [],
        }
        for stage in STAGES
    }
    state = {
        "schema_version": 1,
        "project_id": project_id(args.title),
        "title": args.title,
        "created_at": now(),
        "format": fmt,
        "current_stage": "script",
        "environment": {},
        "input_fingerprints": {},
        "locks": locks,
        "approval_log": [],
        "invalidations": [],
        "release_blockers": ["等待最终人工确认"],
    }
    storyboard = {
        "schema_version": 1,
        "project_id": state["project_id"],
        "revision": 0,
        "status": "draft",
        "format": fmt,
        "audio": {"path": None, "sha256": None, "canonical_timeline": False},
        "captions": {
            "path": "captions.json",
            "format": "Remotion Caption[]",
            "max_lines": 2,
            "safe_area_px": fmt["safe_area_px"],
        },
        "visual_system": {
            "palette": {
                "paper": "#E9DFC8",
                "paper_light": "#F5EEDC",
                "cobalt": "#174A8B",
                "vermilion": "#C83D2E",
                "ink": "#171717",
            },
            "materials": ["暖米白纸面", "剪切边与撕纸边", "黑白半调", "右下投影"],
            "text_rule": "中文、数字、标签、图表与字幕由 Remotion 绘制；生成图片不得承载关键文字。",
        },
        "scenes": [],
        "review_contract": {"max_primary_focus": 1, "max_secondary_focus": 2, "sync_tolerance_frames": 3},
    }
    assets = {
        "schema_version": 1,
        "project_id": state["project_id"],
        "status": "draft",
        "generation": {"mode": "built-in-imagegen", "max_parallel_jobs": 3, "default_candidates_per_asset": 1},
        "asset_types": ["core", "interaction", "carrier", "support", "foreground", "background", "code"],
        "assets": [],
    }
    (project_dir / "script.md").write_text("# 批准口播文案\n\n", encoding="utf-8")
    write_json(project_dir / "production-state.json", state)
    write_json(project_dir / "storyboard.json", storyboard)
    write_json(project_dir / "assets.json", assets)
    write_json(project_dir / "captions.json", [])
    print(f"已初始化：{project_dir}")
    print(f"格式：{format_name} {width}×{height} @ {args.fps}fps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
