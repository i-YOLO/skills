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


def stream_md5(video: Path) -> str:
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-map", "0:v:0", "-c", "copy", "-f", "md5", "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().split("=", 1)[1]


def report_check(path: Path, kind: str) -> tuple[str, dict | str]:
    try:
        return "pass", json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        return "fail", f"invalid {kind} report: {error}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--timeline", type=Path)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--visual-qc", type=Path)
    parser.add_argument("--sync-report", type=Path, help="Output of sync-explainer-video validate_sync.py")
    parser.add_argument("--caption-report", type=Path, help="Output of build_captions.py for a burned-caption delivery")
    parser.add_argument("--audio-mix-report", type=Path, help="Output of mix_default_bgm.py for a BGM delivery")
    parser.add_argument("--reference-video", type=Path, help="Captioned source video; required to prove BGM mixing preserved its video stream")
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

    if args.caption_report:
        load_status, caption = report_check(args.caption_report, "caption")
        if load_status == "fail":
            checks.append({"name": "captions", "status": "fail", "detail": caption})
        else:
            assert isinstance(caption, dict)
            status = "pass" if (
                caption.get("status") == "pass"
                and caption.get("text_source") == "approved script"
                and float(caption.get("exact_alignment_coverage", 0)) >= 0.94
                and float(caption.get("timing_coverage_after_interpolation", 0)) >= 0.98
                and int(caption.get("max_lines", 99)) <= 2
                and float(caption.get("max_frame_error", 99)) <= 1e-6
            ) else "fail"
            checks.append({"name": "captions", "status": status, "detail": caption})

    if args.audio_mix_report:
        load_status, mix = report_check(args.audio_mix_report, "audio mix")
        if load_status == "fail":
            checks.append({"name": "audio_mix", "status": "fail", "detail": mix})
        else:
            assert isinstance(mix, dict)
            expected_audio = mix.get("output_audio") or {}
            status = "pass" if (
                mix.get("status") == "pass"
                and expected_audio.get("codec") == "aac"
                and expected_audio.get("sample_rate") == 48000
                and expected_audio.get("channels") == 1
                and mix.get("source_video_stream_md5") == mix.get("output_video_stream_md5")
            ) else "fail"
            checks.append({"name": "audio_mix", "status": status, "detail": mix})

    if args.audio_mix_report and not args.reference_video:
        checks.append({"name": "video_stream_preserved", "status": "fail", "detail": "--reference-video is required with --audio-mix-report"})
    elif args.reference_video:
        if not args.reference_video.exists():
            checks.append({"name": "video_stream_preserved", "status": "fail", "detail": f"reference video not found: {args.reference_video}"})
        else:
            reference_md5 = stream_md5(args.reference_video)
            output_md5 = stream_md5(args.video)
            checks.append({"name": "video_stream_preserved", "status": "pass" if reference_md5 == output_md5 else "fail", "reference_md5": reference_md5, "output_md5": output_md5})

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
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
