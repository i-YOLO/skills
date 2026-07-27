#!/usr/bin/env python3
"""Initialize the auditable files for a silent-first animation job."""

from __future__ import annotations

import argparse
import json
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
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=float, default=60)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = args.project.resolve()
    project.mkdir(parents=True, exist_ok=True)
    audio = str(args.audio.resolve()) if args.audio else None
    phase = "sync-ready" if audio else "silent-production"
    audio_mode = "voiceover" if audio else "silent"

    job = {
        "schema_version": "1.2",
        "phase": phase,
        "inputs": {
            "script": str(args.script.resolve()) if args.script else None,
            "audio": audio,
            "assets": [str(Path(asset).resolve()) for asset in args.asset],
            "source_project": str(args.source_project.resolve()) if args.source_project else None,
        },
        "delivery": {
            "output": args.output,
            "width": args.width,
            "height": args.height,
            "fps": args.fps,
            "codec": "h264",
            "audio_mode": audio_mode,
            "visual_system": {
                "profile_id": "madem-warm-knowledge-v1",
                "background": "#FAF8F3",
                "caption_safe_region_1080p": {"x_min": 140, "x_max": 1780, "y_min": 860, "y_max": 1040},
                "content_max_y_1080p": 820,
            },
            "post_sync_defaults": {
                "captions": {
                    "enabled_for_voiceover_publish": True,
                    "status": "pending-after-sync" if audio else "deferred-until-voiceover",
                    "text_source": "approved-script",
                    "timing_source": "real-word-timeline",
                    "style_profile_id": "madem-caption-white-black10-v1",
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
        "schema_version": "1.2",
        "fps": args.fps,
        "audio": audio,
        "scenes": [],
        "keywords": [],
        "transitions": [],
        "words": [],
        "visual_actions": [],
        "prelude_events": [],
        "sync_events": [],
    }
    qa = {
        "schema_version": "1.2",
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
