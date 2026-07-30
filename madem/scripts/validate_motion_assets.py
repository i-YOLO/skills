#!/usr/bin/env python3
"""Validate YOLO motion manifests, transparent frames, anchors, and safe layout."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition: bool, detail: str, checks: list[dict[str, Any]]) -> None:
    checks.append(
        {
            "status": "pass" if condition else "fail",
            "detail": detail,
        }
    )


def alpha_metrics(path: Path) -> dict[str, Any]:
    with Image.open(path) as source:
        image = source.convert("RGBA")
        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        corners = [
            alpha.getpixel((0, 0)),
            alpha.getpixel((image.width - 1, 0)),
            alpha.getpixel((0, image.height - 1)),
            alpha.getpixel((image.width - 1, image.height - 1)),
        ]
        visible = 0
        green_fringe = 0
        for red, green, blue, opacity in image.get_flattened_data():
            if opacity <= 32:
                continue
            visible += 1
            if green > red + 45 and green > blue + 30:
                green_fringe += 1
    return {
        "size": image.size,
        "mode": image.mode,
        "bbox": bbox,
        "corners": corners,
        "green_fringe_ratio": green_fringe / visible if visible else 1.0,
    }


def collect_frames(motion: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for facing in motion["facings"].values():
        frames.extend(facing["common"])
        for branch in facing["branches"].values():
            frames.extend(branch)
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text())
    root = args.catalog.parent
    checks: list[dict[str, Any]] = []
    check(catalog.get("schema_version") == "1.0", "catalog schema is 1.0", checks)
    check(catalog.get("status") == "candidate", "new motion family remains candidate", checks)
    check(catalog.get("source_fps") == 12, "source animation runs at 12fps", checks)

    production = catalog["production"]
    check(
        production["max_display_height_1080p"] <= 380,
        "maximum 1080p display height does not exceed 380px",
        checks,
    )
    check(
        production["default_display_height_1080p"] == 320,
        "default 1080p display height is 320px",
        checks,
    )
    for name, slot in production["reserved_slots_1080p"].items():
        check(slot["y_max"] <= 820, f"{name} ends before y=820", checks)
        check(slot["y_min"] < slot["y_max"], f"{name} has positive height", checks)

    declared_files: list[tuple[Path, str, tuple[int, int]]] = []
    for identity in catalog["identity"]:
        declared_files.append((root / identity["file"], identity["sha256"], (1024, 1024)))
    for prop in catalog["props"].values():
        declared_files.append((root / prop["file"], prop["sha256"], tuple(prop["canvas"])))
    for motion in catalog["motions"]:
        check(motion["status"] == "candidate", f"{motion['asset_id']} remains candidate", checks)
        phases = motion["phases"]
        ordered = [
            phases["anticipation_tick"],
            phases["inspect_tick"],
            phases["scan_end_tick"],
            phases["outcome_tick"],
            phases["settled_tick"],
            phases["total_ticks"],
        ]
        check(ordered == sorted(ordered), f"{motion['asset_id']} phase ticks are ordered", checks)
        for facing_name, facing in motion["facings"].items():
            check(
                set(facing["branches"]) == set(motion["outcomes"]),
                f"{motion['asset_id']} {facing_name} declares every outcome",
                checks,
            )
            common_ticks = sum(frame["ticks"] for frame in facing["common"])
            for outcome, branch in facing["branches"].items():
                total_ticks = common_ticks + sum(frame["ticks"] for frame in branch)
                check(
                    total_ticks == phases["total_ticks"],
                    f"{motion['asset_id']} {facing_name}/{outcome} totals {phases['total_ticks']} ticks",
                    checks,
                )
        for frame in collect_frames(motion):
            declared_files.append((root / frame["file"], frame["sha256"], (1024, 1024)))
            transforms = frame.get("props")
            if transforms is None:
                transforms = [{"id": "magnifier", **frame["prop"]}] if "prop" in frame else []
            for transform in transforms:
                check(transform.get("id") in catalog["props"], f"{frame['file']} prop id is declared", checks)
                check(0 <= transform["opacity"] <= 1, f"{frame['file']} prop opacity is valid", checks)
                check(0 <= transform["x"] <= 1024, f"{frame['file']} prop x is in canvas", checks)
                check(0 <= transform["y"] <= 1024, f"{frame['file']} prop y is in canvas", checks)

    seen: set[Path] = set()
    frame_bottoms: dict[str, list[int]] = {"left": [], "right": []}
    for path, expected_hash, expected_size in declared_files:
        if path in seen:
            continue
        seen.add(path)
        check(path.is_file(), f"{path.relative_to(root)} exists", checks)
        if not path.is_file():
            continue
        check(expected_hash == sha256(path), f"{path.relative_to(root)} SHA-256 matches", checks)
        metrics = alpha_metrics(path)
        check(metrics["mode"] == "RGBA", f"{path.relative_to(root)} is RGBA", checks)
        check(metrics["size"] == expected_size, f"{path.relative_to(root)} size is {expected_size}", checks)
        check(max(metrics["corners"]) == 0, f"{path.relative_to(root)} corners are transparent", checks)
        check(
            metrics["green_fringe_ratio"] < 0.001,
            f"{path.relative_to(root)} has no visible chroma fringe",
            checks,
        )
        if expected_size == (1024, 1024) and metrics["bbox"]:
            facing = "left" if path.name.startswith("left") or "master-left" in path.name else "right"
            frame_bottoms[facing].append(metrics["bbox"][3])

    for facing, bottoms in frame_bottoms.items():
        check(
            bool(bottoms) and max(bottoms) - min(bottoms) <= 2,
            f"{facing} foot baseline drift is at most 2px",
            checks,
        )

    failures = [item for item in checks if item["status"] == "fail"]
    report = {
        "status": "pass" if not failures else "fail",
        "catalog": str(args.catalog),
        "checks": checks,
        "summary": {
            "checks": len(checks),
            "failures": len(failures),
            "files": len(seen),
        },
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
