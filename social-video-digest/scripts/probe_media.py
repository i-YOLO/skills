#!/usr/bin/env python3
"""Probe a media file with ffprobe and emit compact JSON."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_ffprobe(path: Path) -> dict:
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
    return json.loads(completed.stdout or "{}")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: probe_media.py <media-file>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1]).expanduser().resolve()
    result: dict = {
        "path": str(path),
        "exists": path.exists(),
        "ok": False,
        "has_video": False,
        "has_audio": False,
        "streams": [],
        "format": {},
    }

    if not path.exists():
        result["error"] = "file not found"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    try:
        data = run_ffprobe(path)
    except Exception as exc:  # noqa: BLE001 - CLI should report any probe failure
        result["error"] = str(exc)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    streams = data.get("streams", [])
    result["streams"] = streams
    result["format"] = data.get("format", {})
    result["has_video"] = any(stream.get("codec_type") == "video" for stream in streams)
    result["has_audio"] = any(stream.get("codec_type") == "audio" for stream in streams)
    result["ok"] = bool(streams)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
