#!/usr/bin/env python3
"""Produce a scene-level sync plan from explicit silent and audio scene ranges."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--threshold", type=float, default=0.20)
    args = parser.parse_args()

    timeline = json.loads(args.timeline.read_text())
    recommendations = []
    for scene in timeline.get("scenes", []):
        scene_id = scene.get("id", "unnamed-scene")
        required = ("start", "end", "audio_start", "audio_end")
        missing = [name for name in required if scene.get(name) is None]
        if missing:
            recommendations.append({"scene": scene_id, "status": "needs-mapping", "missing": missing})
            continue
        silent_duration = float(scene["end"]) - float(scene["start"])
        audio_duration = float(scene["audio_end"]) - float(scene["audio_start"])
        if silent_duration <= 0 or audio_duration <= 0:
            recommendations.append({"scene": scene_id, "status": "invalid", "silent_duration": silent_duration, "audio_duration": audio_duration})
            continue
        delta_ratio = (audio_duration - silent_duration) / silent_duration
        if abs(delta_ratio) <= args.threshold:
            strategy = "retime-within-tolerance"
            instruction = "Adjust holds, transitions, and motion pacing; add visual content if the result looks unnatural."
        elif audio_duration > silent_duration:
            strategy = "add-explanatory-visuals"
            instruction = "Add meaningful cards, media, or a visual beat. Do not stretch motion into slow motion."
        else:
            strategy = "compress-or-remove-nonessential-visuals"
            instruction = "Remove or compress nonessential visual beats while preserving concept order."
        recommendations.append({
            "scene": scene_id, "status": "planned", "silent_duration": silent_duration,
            "audio_duration": audio_duration, "delta_ratio": delta_ratio,
            "retime_speed_factor": silent_duration / audio_duration,
            "strategy": strategy, "instruction": instruction,
        })
    report = {"timeline": str(args.timeline.resolve()), "threshold": args.threshold, "recommendations": recommendations}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
