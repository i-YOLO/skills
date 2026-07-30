#!/usr/bin/env python3
"""Register the first six YOLO motion actions in the shared candidate catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ACTION_SPECS = (
    {
        "asset_id": "yolo-quiet-observe",
        "role": "quiet-observe",
        "playback_mode": "loop",
        "outcome": "loop",
        "ticks": [2, 2, 2, 2, 2, 2, 2, 2],
        "phases": [2, 6, 10, 12, 14, 16],
        "loop_range_ticks": [0, 16],
        "settled_frame_index": 7,
        "suitable_for": ["listening", "quiet observation", "light idle presence"],
        "not_suitable_for": ["semantic result emphasis", "risk warning"],
    },
    {
        "asset_id": "yolo-chin-think",
        "role": "chin-think",
        "playback_mode": "loop",
        "outcome": "loop",
        "ticks": [2, 2, 2, 3, 3, 3, 2, 3],
        "phases": [2, 6, 12, 15, 17, 20],
        "loop_range_ticks": [0, 20],
        "settled_frame_index": 7,
        "suitable_for": ["reasoning", "comparison", "question framing"],
        "not_suitable_for": ["final approval", "urgent warning"],
    },
    {
        "asset_id": "yolo-point-tap",
        "role": "point-tap",
        "playback_mode": "one-shot-with-settled-hold",
        "outcome": "default",
        "ticks": [2, 2, 2, 2, 2, 2, 2, 12],
        "phases": [2, 6, 8, 10, 14, 26],
        "loop_range_ticks": None,
        "settled_frame_index": 7,
        "suitable_for": ["pointing to a card", "light UI tap", "keyword emphasis"],
        "not_suitable_for": ["large hero gestures", "multiple simultaneous targets"],
    },
    {
        "asset_id": "yolo-catch-card",
        "role": "catch-card-slot",
        "playback_mode": "one-shot-with-settled-hold",
        "outcome": "default",
        "ticks": [2, 2, 3, 3, 3, 3, 3, 12],
        "phases": [2, 7, 10, 13, 19, 31],
        "loop_range_ticks": None,
        "settled_frame_index": 7,
        "suitable_for": ["receiving information", "filing a card", "moving an item into a system"],
        "not_suitable_for": ["background decoration", "scenes without prop clearance"],
    },
    {
        "asset_id": "yolo-risk-reminder",
        "role": "palm-risk-reminder",
        "playback_mode": "one-shot-with-settled-hold",
        "outcome": "default",
        "ticks": [2, 2, 2, 2, 2, 2, 2, 12],
        "phases": [2, 6, 8, 10, 14, 26],
        "loop_range_ticks": None,
        "settled_frame_index": 7,
        "suitable_for": ["risk reminder", "permission boundary", "human confirmation"],
        "not_suitable_for": ["alarm or panic", "celebration"],
    },
)


def prop_track(prop_id: str, x: int, y: int, rotation: float, opacity: float) -> dict[str, Any]:
    return {
        "id": prop_id,
        "x": x,
        "y": y,
        "rotation": rotation,
        "opacity": opacity,
    }


def catch_tracks(facing: str) -> list[list[dict[str, Any]]]:
    right_card = [
        (720, 180, -8, 0.0),
        (720, 260, -6, 0.6),
        (690, 370, -4, 1.0),
        (650, 470, 0, 1.0),
        (615, 520, 0, 1.0),
        (650, 630, 4, 1.0),
        (690, 720, 8, 0.9),
        (700, 760, 0, 0.0),
    ]
    if facing == "left":
        cards = [(1024 - x, y, -rotation, opacity) for x, y, rotation, opacity in right_card]
        slot_x = 324
    else:
        cards = right_card
        slot_x = 700
    return [
        [
            prop_track("slot", slot_x, 760, 0, 0.65 if index == 0 else 1.0),
            prop_track("card", x, y, rotation, opacity),
        ]
        for index, (x, y, rotation, opacity) in enumerate(cards)
    ]


def action_directory(asset_id: str) -> str:
    return asset_id.removeprefix("yolo-")


def make_motion(spec: dict[str, Any]) -> dict[str, Any]:
    phases = spec["phases"]
    motion = {
        "asset_id": spec["asset_id"],
        "role": spec["role"],
        "status": "candidate",
        "playback_mode": spec["playback_mode"],
        "outcomes": [spec["outcome"]],
        "suitable_for": spec["suitable_for"],
        "not_suitable_for": spec["not_suitable_for"],
        "loop_range_ticks": spec["loop_range_ticks"],
        "settled_frame_index": spec["settled_frame_index"],
        "phases": {
            "anticipation_tick": phases[0],
            "inspect_tick": phases[1],
            "scan_end_tick": phases[2],
            "outcome_tick": phases[3],
            "settled_tick": phases[4],
            "total_ticks": phases[5],
        },
        "facings": {},
        "evidence": {
            "generation_method": "built-in image generation with per-frame chroma-key extraction",
            "manual_visual_review": "pass",
            "manual_visual_review_report": "reports/manual-visual-review.json",
            "project_validation": None,
        },
    }
    directory = action_directory(spec["asset_id"])
    for facing in ("right", "left"):
        frame_props = catch_tracks(facing) if spec["asset_id"] == "yolo-catch-card" else [[] for _ in spec["ticks"]]
        common = []
        for index, (ticks, props) in enumerate(zip(spec["ticks"], frame_props, strict=True)):
            common.append(
                {
                    "file": f"actions/{directory}/keyframes/{facing}/{facing}-{index:02d}.png",
                    "ticks": ticks,
                    "props": props,
                    "sha256": "",
                }
            )
        motion["facings"][facing] = {
            "common": common,
            "branches": {spec["outcome"]: []},
        }
    return motion


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text())
    catalog["validation_reports"] = {
        "asset_contract": "reports/asset-validation.json",
        "continuity": "reports/continuity-validation.json",
        "manual_visual_review": "reports/manual-visual-review.json",
    }
    catalog["props"]["card"] = {
        "file": "props/card.png",
        "canvas": [512, 512],
        "logical_width": 180,
        "grip_anchor": {"right": [0.5, 0.5], "left": [0.5, 0.5]},
        "mirror_for_left": False,
        "sha256": "",
    }
    catalog["props"]["slot"] = {
        "file": "props/slot.png",
        "canvas": [512, 512],
        "logical_width": 320,
        "grip_anchor": {"right": [0.5, 0.53], "left": [0.5, 0.53]},
        "mirror_for_left": False,
        "sha256": "",
    }
    replacement_ids = {spec["asset_id"] for spec in ACTION_SPECS}
    catalog["motions"] = [
        motion
        for motion in catalog["motions"]
        if motion.get("asset_id") not in replacement_ids
    ]
    catalog["motions"].extend(make_motion(spec) for spec in ACTION_SPECS)
    for motion in catalog["motions"]:
        if motion.get("asset_id") == "yolo-verify-source":
            motion["evidence"] = {
                "generation_method": "built-in image generation with per-frame chroma-key extraction",
                "manual_visual_review": "pass",
                "manual_visual_review_report": "reports/manual-visual-review.json",
                "project_validation": None,
            }
    args.catalog.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "pass", "registered": sorted(replacement_ids)}, indent=2))


if __name__ == "__main__":
    main()
