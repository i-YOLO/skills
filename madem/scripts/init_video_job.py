#!/usr/bin/env python3
"""Initialize the auditable files for a silent-first animation job."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def write_json(path: Path, payload: dict, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {path}; pass --force only after review.")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--script", type=Path)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--asset", action="append", default=[])
    parser.add_argument("--source-project", type=Path)
    parser.add_argument("--output", default="out/final.mp4")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--fps", type=float, default=60)
    parser.add_argument(
        "--visual-profile",
        choices=("auto", "warm-knowledge", "ai-tech-dark"),
        default="auto",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = args.project.resolve()
    project.mkdir(parents=True, exist_ok=True)
    audio = str(args.audio.resolve()) if args.audio else None
    phase = "sync-ready" if audio else "silent-production"
    audio_mode = "voiceover" if audio else "silent"
    script_text = (
        args.script.read_text(encoding="utf-8") if args.script and args.script.exists() else ""
    )
    ai_tech = args.visual_profile == "ai-tech-dark" or (
        args.visual_profile == "auto"
        and bool(re.search(r"(?i)\bAI\b|\bAgent\b|\bCodex\b|软件|工作流|自动执行", script_text))
    )
    default_width, default_height = ((1080, 1920) if ai_tech else (1920, 1080))
    width = args.width if args.width is not None else default_width
    height = args.height if args.height is not None else default_height
    if width <= 0 or height <= 0:
        raise ValueError("delivery width and height must be positive")
    visual_system = (
        {
            "profile_id": "madem-ai-tech-dark-v1",
            "background": "#06090D",
            "caption_safe_region_1080p": {
                "x_min": 70,
                "x_max": 1010,
                "y_min": 1660,
                "y_max": 1870,
            },
            "content_max_y_1080p": 1600,
            "render_image_format": "png",
        }
        if ai_tech
        else {
            "profile_id": "madem-warm-knowledge-v1",
            "background": "#FAF8F3",
            "caption_safe_region_1080p": {
                "x_min": 140,
                "x_max": 1780,
                "y_min": 860,
                "y_max": 1040,
            },
            "content_max_y_1080p": 820,
            "render_image_format": "png",
        }
    )
    motion_density = (
        {"profile_id": "dense-tech-v1", "tracks": []} if ai_tech else None
    )

    job = {
        "schema_version": "1.4",
        "phase": phase,
        "inputs": {
            "script": str(args.script.resolve()) if args.script else None,
            "audio": audio,
            "assets": [str(Path(asset).resolve()) for asset in args.asset],
            "source_project": str(args.source_project.resolve()) if args.source_project else None,
        },
        "delivery": {
            "output": args.output,
            "width": width,
            "height": height,
            "fps": args.fps,
            "codec": "h264",
            "audio_mode": audio_mode,
            "visual_system": visual_system,
            "motion_density": motion_density,
            "post_sync_defaults": {
                "captions": {
                    "enabled_for_voiceover_publish": True,
                    "status": "pending-after-sync" if audio else "deferred-until-voiceover",
                    "text_source": "approved-script",
                    "timing_source": "real-word-timeline",
                    "style_profile_id": "madem-caption-white-black10-single-line-v2",
                },
                "background_music": {
                    "enabled_for_voiceover_publish": True,
                    "status": "pending-after-captions" if audio else "deferred-until-voiceover",
                    "profile_id": "madem-default-bgm-v3",
                    "override_requires_user_request": True,
                },
            },
        },
        "scenes": [],
    }
    timeline = {
        "schema_version": "1.4",
        "fps": args.fps,
        "audio": audio,
        "scenes": [],
        "keywords": [],
        "transitions": [],
        "words": [],
        "visual_actions": [],
        "motion_density": motion_density,
        "prelude_events": [],
        "sync_events": [],
    }
    qa = {
        "schema_version": "1.4",
        "status": "not-run",
        "manual_review": "pending",
        "checks": [],
        "issues": [],
    }
    write_json(project / "video-job.json", job, args.force)
    write_json(project / "timeline.json", timeline, args.force)
    write_json(project / "qa-report.json", qa, args.force)
    print(f"Initialized {phase} job in {project}")


if __name__ == "__main__":
    main()
