#!/usr/bin/env python3
"""Extract 1 fps baseline frames plus scene, keyword, and transition evidence frames."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from collections import defaultdict
from fractions import Fraction
from pathlib import Path


def media_info(video: Path) -> tuple[float, float]:
    command = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    raw = json.loads(result.stdout)
    stream = next(item for item in raw["streams"] if item.get("codec_type") == "video")
    fps = float(Fraction(stream.get("avg_frame_rate", "0/0")))
    duration = float(raw["format"]["duration"])
    return duration, fps


def load_timeline(path: Path | None) -> dict:
    if not path:
        return {}
    return json.loads(path.read_text())


def add(events: dict[float, set[str]], time: float, last_frame_time: float, reason: str) -> None:
    if 0 <= time <= last_frame_time:
        events[round(time, 4)].add(reason)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--timeline", type=Path)
    parser.add_argument("--captions", type=Path, help="Caption JSON emitted by build_captions.py; adds start/middle/end evidence frames")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--jpeg-quality", type=int, default=2)
    args = parser.parse_args()

    duration, fps = media_info(args.video)
    step = 1 / fps
    last_frame_time = max(0.0, duration - step)
    timeline = load_timeline(args.timeline)
    evidence: dict[float, set[str]] = defaultdict(set)
    for second in range(max(1, math.floor(duration))):
        add(evidence, float(second), last_frame_time, "baseline-1fps")

    for scene in timeline.get("scenes", []):
        start, end = float(scene["start"]), float(scene["end"])
        scene_id = scene.get("id", "scene")
        add(evidence, start, last_frame_time, f"{scene_id}:start")
        add(evidence, (start + end) / 2, last_frame_time, f"{scene_id}:middle")
        add(evidence, max(start, end - step), last_frame_time, f"{scene_id}:end")
    for keyword in timeline.get("keywords", []):
        time = float(keyword["time"])
        label = keyword.get("text", "keyword")
        for offset, phase in ((-step, "before"), (0, "at"), (step, "after")):
            add(evidence, time + offset, last_frame_time, f"keyword:{label}:{phase}")
    for event in timeline.get("sync_events", []):
        if event.get("stage", "semantic") != "semantic":
            continue
        time = float(event["visual_time"])
        label = event.get("label", event.get("id", "action"))
        for offset, phase in ((-step, "before"), (0, "at"), (step, "after")):
            add(evidence, time + offset, last_frame_time, f"action:{label}:{phase}")
    for prelude in timeline.get("prelude_events", []):
        time = float(prelude["visual_time"])
        label = prelude.get("id", "prelude")
        for offset, phase in ((-step, "before"), (0, "at"), (step, "after")):
            add(evidence, time + offset, last_frame_time, f"prelude:{label}:{phase}")
    if args.captions:
        captions = json.loads(args.captions.read_text())
        for index, caption in enumerate(captions, start=1):
            start = float(caption["startMs"]) / 1000
            end = float(caption["endMs"]) / 1000
            label = str(caption.get("text", "caption")).replace("\n", " ")[:24]
            add(evidence, start, last_frame_time, f"caption:{index}:{label}:start")
            add(evidence, (start + end) / 2, last_frame_time, f"caption:{index}:{label}:middle")
            add(evidence, max(start, end - step), last_frame_time, f"caption:{index}:{label}:end")
    for transition in timeline.get("transitions", []):
        time = float(transition["time"])
        label = transition.get("id", "transition")
        for offset, phase in ((-step, "before"), (0, "at"), (step, "after")):
            add(evidence, time + offset, last_frame_time, f"transition:{label}:{phase}")

    args.out.mkdir(parents=True, exist_ok=True)
    frames = []
    for number, (time, reasons) in enumerate(sorted(evidence.items()), start=1):
        target = args.out / f"frame_{number:05d}_{time:010.4f}s.jpg"
        command = [
            "ffmpeg", "-y", "-v", "error", "-ss", f"{time:.4f}", "-i", str(args.video),
            "-frames:v", "1", "-q:v", str(args.jpeg_quality), str(target),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode or not target.is_file() or target.stat().st_size == 0:
            raise RuntimeError(result.stderr.strip() or f"failed to extract {time}")
        frames.append({"time": time, "path": target.name, "reasons": sorted(reasons)})

    index = {
        "video": str(args.video.resolve()),
        "duration": duration,
        "fps": fps,
        "frame_count": len(frames),
        "frames": frames,
        "review_note": "Normal entrance and exit animation is allowed. Visually inspect all frames for overlap, clipping, readability, layout, blur, caption obstruction, and semantic correctness.",
    }
    (args.out / "frame-index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
