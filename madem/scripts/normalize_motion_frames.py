#!/usr/bin/env python3
"""Normalize transparent motion keyframes to one fixed canvas and anchor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def alpha_bbox(path: Path) -> tuple[int, int, int, int]:
    with Image.open(path) as source:
        image = source.convert("RGBA")
        bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"{path} has no visible pixels")
    return bbox


def union_bbox(paths: list[Path]) -> tuple[int, int, int, int]:
    boxes = [alpha_bbox(path) for path in paths]
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def normalize_group(
    paths: list[Path],
    output_dir: Path,
    *,
    canvas_size: int,
    subject_height: int,
    anchor_x: int,
    anchor_y: int,
) -> dict[str, object]:
    boxes = {path: alpha_bbox(path) for path in paths}
    tallest_height = max(box[3] - box[1] for box in boxes.values())
    scale = subject_height / tallest_height

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, object]] = []
    for path in paths:
        source_bbox = boxes[path]
        source_width = source_bbox[2] - source_bbox[0]
        source_height = source_bbox[3] - source_bbox[1]
        scaled_width = max(1, round(source_width * scale))
        scaled_height = max(1, round(source_height * scale))
        left = round(anchor_x - scaled_width / 2)
        top = anchor_y - scaled_height
        if (
            left < 0
            or top < 0
            or left + scaled_width > canvas_size
            or anchor_y > canvas_size
        ):
            raise ValueError(
                "normalized subject does not fit canvas: "
                f"file={path}, bbox={source_bbox}, scale={scale:.4f}, "
                f"paste={(left, top, scaled_width, scaled_height)}"
            )
        with Image.open(path) as source:
            image = source.convert("RGBA")
            crop = image.crop(source_bbox)
            resized = crop.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        canvas.alpha_composite(resized, dest=(left, top))
        output = output_dir / path.name
        canvas.save(output, optimize=True)
        frame_bbox = canvas.getchannel("A").getbbox()
        outputs.append({"file": output.name, "bbox": list(frame_bbox) if frame_bbox else None})

    return {
        "canvas": [canvas_size, canvas_size],
        "subject_height": subject_height,
        "anchor": [anchor_x, anchor_y],
        "source_union_bbox": list(union_bbox(paths)),
        "source_frame_bboxes": {
            path.name: list(box) for path, box in boxes.items()
        },
        "scale_basis": "tallest-frame",
        "scale": scale,
        "frames": outputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--glob", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--canvas-size", type=int, default=1024)
    parser.add_argument("--subject-height", type=int, default=900)
    parser.add_argument("--anchor-x", type=int, default=512)
    parser.add_argument("--anchor-y", type=int, default=970)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    paths = sorted(args.input_dir.glob(args.glob))
    if not paths:
        raise SystemExit(f"no files matched {args.input_dir / args.glob}")
    report = normalize_group(
        paths,
        args.out_dir,
        canvas_size=args.canvas_size,
        subject_height=args.subject_height,
        anchor_x=args.anchor_x,
        anchor_y=args.anchor_y,
    )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
