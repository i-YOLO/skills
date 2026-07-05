#!/usr/bin/env python3
"""Extract 16 kHz mono WAV audio for ASR."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Whisper-ready WAV audio.")
    parser.add_argument("input", help="Input video/audio file")
    parser.add_argument("output", help="Output .wav path")
    parser.add_argument("--force", action="store_true", help="Overwrite output if it exists")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    dst = Path(args.output).expanduser().resolve()

    if not src.exists():
        print(f"Input not found: {src}", file=sys.stderr)
        return 1
    if dst.exists() and not args.force:
        print(f"Output exists, pass --force to overwrite: {dst}", file=sys.stderr)
        return 1

    dst.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y" if args.force else "-n",
        "-i",
        str(src),
        "-vn",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(dst),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        print(completed.stderr.strip(), file=sys.stderr)
        return completed.returncode

    print(str(dst))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
