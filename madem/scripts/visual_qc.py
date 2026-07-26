#!/usr/bin/env python3
"""Flag unannotated long static regions from 1 fps low-resolution visual differences."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def video_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def raw_samples(video: Path, size: int) -> list[bytes]:
    command = ["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps=1,scale={size}:{size},format=gray", "-f", "rawvideo", "-"]
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace").strip() or "ffmpeg sampling failed")
    frame_bytes = size * size
    return [result.stdout[index:index + frame_bytes] for index in range(0, len(result.stdout), frame_bytes) if len(result.stdout[index:index + frame_bytes]) == frame_bytes]


def difference(a: bytes, b: bytes) -> float:
    return sum(abs(left - right) for left, right in zip(a, b)) / len(a)


def in_declared_hold(start: float, end: float, scenes: list[dict]) -> bool:
    relevant = [scene for scene in scenes if float(scene.get("start", -1)) <= start and float(scene.get("end", -1)) >= end]
    return bool(relevant) and all(scene.get("hold") is True for scene in relevant)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--timeline", type=Path)
    parser.add_argument("--audio", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--change-threshold", type=float, default=2.0)
    parser.add_argument("--min-static-samples", type=int, default=3)
    args = parser.parse_args()

    timeline = json.loads(args.timeline.read_text()) if args.timeline else {}
    samples = raw_samples(args.video, args.size)
    differences = [difference(samples[index - 1], sample) for index, sample in enumerate(samples[1:], start=1)]
    narration_duration = video_duration(args.audio) if args.audio else None
    candidates = []
    run_start = None
    for index, value in enumerate(differences, start=1):
        static = value <= args.change_threshold
        if static and run_start is None:
            run_start = index - 1
        if run_start is not None and (not static or index == len(differences)):
            end_index = index if static and index == len(differences) else index - 1
            sample_count = end_index - run_start + 1
            start, end = float(run_start), float(end_index + 1)
            if sample_count >= args.min_static_samples:
                narration_active = narration_duration is not None and start < narration_duration
                exempt = in_declared_hold(start, end, timeline.get("scenes", []))
                candidates.append({
                    "start": start, "end": end, "sample_count": sample_count,
                    "narration_active": narration_active, "declared_hold": exempt,
                    "requires_repair": narration_active and not exempt,
                })
            run_start = None

    report = {
        "video": str(args.video.resolve()),
        "sampling": {"fps": 1, "size": args.size, "change_threshold": args.change_threshold},
        "differences": differences,
        "static_candidates": candidates,
        "note": "This is a visual-change heuristic. Inspect review frames for overlap, readability, blur, bad placement, and semantic errors.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
