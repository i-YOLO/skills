#!/usr/bin/env python3
"""Merge video and audio streams without re-encoding, then verify tracks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def probe(path: Path) -> dict:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate,duration",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "ffprobe failed")
    data = json.loads(completed.stdout or "{}")
    streams = data.get("streams", [])
    return {
        "path": str(path),
        "has_video": any(stream.get("codec_type") == "video" for stream in streams),
        "has_audio": any(stream.get("codec_type") == "audio" for stream in streams),
        "streams": streams,
        "format": data.get("format", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge separate video and audio files.")
    parser.add_argument("video", help="Video input")
    parser.add_argument("audio", help="Audio input")
    parser.add_argument("output", help="Merged MP4 output")
    parser.add_argument("--force", action="store_true", help="Overwrite output if it exists")
    args = parser.parse_args()

    video = Path(args.video).expanduser().resolve()
    audio = Path(args.audio).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()

    for path in (video, audio):
        if not path.exists():
            print(f"Input not found: {path}", file=sys.stderr)
            return 1
    if output.exists() and not args.force:
        print(f"Output exists, pass --force to overwrite: {output}", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y" if args.force else "-n",
        "-i",
        str(video),
        "-i",
        str(audio),
        "-c",
        "copy",
        "-shortest",
        str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        print(completed.stderr.strip(), file=sys.stderr)
        return completed.returncode

    result = probe(output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not (result["has_video"] and result["has_audio"]):
        print("Merged output does not contain both video and audio streams", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
