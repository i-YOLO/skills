#!/usr/bin/env python3
"""Probe media and optionally validate delivery dimensions, fps, and codec."""

from __future__ import annotations

import argparse
import json
import subprocess
from fractions import Fraction
from pathlib import Path


def probe(path: Path) -> dict:
    command = ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    raw = json.loads(result.stdout)
    video = next((stream for stream in raw.get("streams", []) if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in raw.get("streams", []) if stream.get("codec_type") == "audio"), None)
    frame_rate = None
    if video and video.get("avg_frame_rate") not in (None, "0/0"):
        frame_rate = float(Fraction(video["avg_frame_rate"]))
    return {
        "path": str(path.resolve()),
        "duration": float(raw.get("format", {}).get("duration") or 0),
        "format": raw.get("format", {}).get("format_name"),
        "video": None if not video else {
            "codec": video.get("codec_name"), "width": video.get("width"), "height": video.get("height"), "fps": frame_rate,
        },
        "audio": None if not audio else {"codec": audio.get("codec_name"), "sample_rate": audio.get("sample_rate"), "channels": audio.get("channels")},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--codec")
    parser.add_argument("--require-audio", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = probe(args.media)
    checks: list[dict] = []
    video = report["video"]
    for field, expected in (("width", args.width), ("height", args.height), ("fps", args.fps)):
        if expected is not None:
            actual = video.get(field) if video else None
            checks.append({"check": field, "expected": expected, "actual": actual, "pass": actual is not None and abs(float(actual) - expected) < 0.02})
    if args.codec:
        actual_codec = video.get("codec") if video else None
        checks.append({"check": "codec", "expected": args.codec, "actual": actual_codec, "pass": actual_codec == args.codec})
    if args.require_audio:
        checks.append({"check": "audio", "expected": True, "actual": report["audio"] is not None, "pass": report["audio"] is not None})
    report["checks"] = checks
    report["status"] = "pass" if all(check["pass"] for check in checks) else ("fail" if checks else "probed")
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n")
    print(payload)


if __name__ == "__main__":
    main()
