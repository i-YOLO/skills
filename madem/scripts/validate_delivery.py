#!/usr/bin/env python3
"""Validate decode, delivery spec, visual-QC evidence, and recorded sync events."""

from __future__ import annotations

import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path


def probe(path: Path) -> dict:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    raw = json.loads(result.stdout)
    video = next((item for item in raw["streams"] if item.get("codec_type") == "video"), None)
    audio = next((item for item in raw["streams"] if item.get("codec_type") == "audio"), None)
    return {
        "duration": float(raw["format"].get("duration") or 0),
        "video": None if not video else {
            "codec": video.get("codec_name"), "width": video.get("width"), "height": video.get("height"),
            "fps": float(Fraction(video.get("avg_frame_rate", "0/0"))),
        },
        "audio": audio is not None,
    }


def check_decode(video: Path) -> tuple[bool, str]:
    result = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(video), "-f", "null", "-"], capture_output=True, text=True)
    return result.returncode == 0, (result.stderr.strip() or "fully decoded")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--timeline", type=Path)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--visual-qc", type=Path)
    parser.add_argument("--sync-report", type=Path, help="Output of sync-explainer-video validate_sync.py")
    parser.add_argument("--manual-review", choices=("pending", "pass", "fail"), default="pending")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=float, default=60)
    parser.add_argument("--codec", default="h264")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    info = probe(args.video)
    decoded, decode_detail = check_decode(args.video)
    checks = [
        {"name": "complete_decode", "status": "pass" if decoded else "fail", "detail": decode_detail},
        {"name": "width", "status": "pass" if info["video"] and info["video"]["width"] == args.width else "fail", "actual": info["video"] and info["video"]["width"], "expected": args.width},
        {"name": "height", "status": "pass" if info["video"] and info["video"]["height"] == args.height else "fail", "actual": info["video"] and info["video"]["height"], "expected": args.height},
        {"name": "fps", "status": "pass" if info["video"] and abs(info["video"]["fps"] - args.fps) < 0.02 else "fail", "actual": info["video"] and info["video"]["fps"], "expected": args.fps},
        {"name": "codec", "status": "pass" if info["video"] and info["video"]["codec"] == args.codec else "fail", "actual": info["video"] and info["video"]["codec"], "expected": args.codec},
        {"name": "manual_frame_review", "status": args.manual_review, "detail": "Review every 1fps and event frame before passing."},
    ]
    if args.audio:
        checks.append({"name": "reference_audio", "status": "pass" if args.audio.exists() else "fail", "detail": str(args.audio)})

    if args.visual_qc:
        visual = json.loads(args.visual_qc.read_text())
        unresolved = [item for item in visual.get("static_candidates", []) if item.get("requires_repair")]
        checks.append({"name": "unexplained_long_static", "status": "fail" if unresolved else "pass", "candidates": unresolved})

    sync = {"status": "not-applicable", "events": [], "max_error_frames": None}
    if args.audio:
        sync = {"status": "needs-evidence", "events": [], "max_error_frames": None}
        if args.sync_report and args.sync_report.exists():
            sync = json.loads(args.sync_report.read_text())
        elif args.sync_report:
            sync = {"status": "fail", "events": [], "max_error_frames": None, "detail": f"sync report not found: {args.sync_report}"}
    checks.append({"name": "sync", "status": sync["status"], "detail": sync})

    statuses = [check["status"] for check in checks]
    if "fail" in statuses or args.manual_review == "fail":
        status = "fail"
    elif "pending" in statuses or "needs-evidence" in statuses or "warning" in statuses:
        status = "needs-review"
    else:
        status = "pass"
    report = {"status": status, "video": str(args.video.resolve()), "media": info, "checks": checks, "sync": sync, "manual_review": args.manual_review}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
