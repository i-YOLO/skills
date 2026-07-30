#!/usr/bin/env python3
"""Audit YOLO keyframe continuity, loop seams, result holds, and facing independence."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageOps, ImageStat

from render_yolo_motion_preview import flatten_frames, render_character_canvas


def mean_difference(first: Image.Image, second: Image.Image) -> float:
    difference = ImageChops.difference(first, second)
    return sum(ImageStat.Stat(difference).mean) / 3


def review_image(root: Path, catalog: dict, entry: dict, facing: str) -> Image.Image:
    logical = render_character_canvas(root, catalog, entry, facing)
    background = Image.new("RGBA", logical.size, (250, 248, 243, 255))
    background.alpha_composite(logical)
    return background.convert("RGB").resize((256, 256), Image.Resampling.LANCZOS)


def check(condition: bool, kind: str, detail: str, checks: list[dict[str, Any]], **extra: Any) -> None:
    checks.append(
        {
            "kind": kind,
            "status": "pass" if condition else "fail",
            "detail": detail,
            **extra,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--maximum-mean-frame-difference", type=float, default=28.0)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text())
    root = args.catalog.parent
    checks: list[dict[str, Any]] = []
    metrics: list[dict[str, Any]] = []
    for motion in catalog["motions"]:
        motion_id = motion["asset_id"]
        for outcome in motion["outcomes"]:
            facing_images: dict[str, list[Image.Image]] = {}
            for facing in ("right", "left"):
                entries = flatten_frames(motion, facing, outcome)
                images = [review_image(root, catalog, entry, facing) for entry in entries]
                facing_images[facing] = images
                differences = [
                    mean_difference(first, second)
                    for first, second in zip(images, images[1:])
                ]
                maximum = max(differences, default=0.0)
                median = statistics.median(differences) if differences else 0.0
                check(
                    len(entries) >= 8,
                    "keyframe-count",
                    f"{motion_id} {facing}/{outcome} has at least 8 independent PNG entries",
                    checks,
                    motion_id=motion_id,
                    facing=facing,
                    outcome=outcome,
                    keyframes=len(entries),
                )
                check(
                    maximum <= args.maximum_mean_frame_difference,
                    "frame-continuity",
                    f"{motion_id} {facing}/{outcome} has no extreme adjacent-frame jump",
                    checks,
                    motion_id=motion_id,
                    facing=facing,
                    outcome=outcome,
                    median_mean_difference=round(median, 4),
                    maximum_mean_difference=round(maximum, 4),
                    threshold=args.maximum_mean_frame_difference,
                )
                if motion["playback_mode"] == "loop":
                    seam = mean_difference(images[-1], images[0])
                    check(
                        seam <= 0.05,
                        "loop-seam",
                        f"{motion_id} {facing}/{outcome} closes on the exact loop pose",
                        checks,
                        motion_id=motion_id,
                        facing=facing,
                        outcome=outcome,
                        seam_mean_difference=round(seam, 4),
                    )
                else:
                    final_ticks = int(entries[-1]["ticks"])
                    check(
                        final_ticks >= catalog["source_fps"],
                        "result-hold",
                        f"{motion_id} {facing}/{outcome} final frame holds at least 1 second",
                        checks,
                        motion_id=motion_id,
                        facing=facing,
                        outcome=outcome,
                        final_ticks=final_ticks,
                        source_fps=catalog["source_fps"],
                    )
                metrics.append(
                    {
                        "motion_id": motion_id,
                        "facing": facing,
                        "outcome": outcome,
                        "keyframes": len(entries),
                        "median_mean_difference": round(median, 4),
                        "maximum_mean_difference": round(maximum, 4),
                    }
                )

            mirrored_right = ImageOps.mirror(facing_images["right"][0])
            facing_difference = mean_difference(mirrored_right, facing_images["left"][0])
            check(
                facing_difference >= 0.25,
                "facing-independence",
                f"{motion_id} {outcome} left facing is not a pixel mirror of right facing",
                checks,
                motion_id=motion_id,
                outcome=outcome,
                mirrored_mean_difference=round(facing_difference, 4),
            )

    failures = [item for item in checks if item["status"] == "fail"]
    report = {
        "status": "pass" if not failures else "fail",
        "catalog": str(args.catalog.resolve()),
        "checks": checks,
        "metrics": metrics,
        "summary": {
            "checks": len(checks),
            "failures": len(failures),
            "motion_outcome_variants": len(metrics),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
