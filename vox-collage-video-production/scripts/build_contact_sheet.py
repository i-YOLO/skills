#!/usr/bin/env python3
"""Build a checkerboard contact sheet from selected project image assets."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def checkerboard(size: tuple[int, int], step: int = 20) -> Image.Image:
    image = Image.new("RGB", size, "#e5e5e5")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], step):
        for x in range(0, size[0], step):
            if (x // step + y // step) % 2:
                draw.rectangle((x, y, x + step, y + step), fill="#c8c8c8")
    return image


def resolve(project: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else project / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--manifest", default="assets.json")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scene")
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--cell-width", type=int, default=360)
    parser.add_argument("--cell-height", type=int, default=260)
    args = parser.parse_args()
    if args.columns < 1 or args.cell_width < 80 or args.cell_height < 80:
        parser.error("网格参数过小")
    project = args.project_dir.expanduser().resolve()
    manifest = json.loads((project / args.manifest).read_text(encoding="utf-8"))
    rows = []
    for asset in manifest.get("assets", []):
        if asset.get("asset_type") == "code":
            continue
        if args.scene and args.scene not in asset.get("scene_ids", []):
            continue
        path = resolve(project, asset.get("render_path") or asset.get("processed_path"))
        if path and path.is_file():
            rows.append((asset, path))
    if not rows:
        parser.error("没有找到可放入联系表的图片素材")
    label_height = 34
    padding = 12
    rows_count = math.ceil(len(rows) / args.columns)
    sheet = Image.new("RGB", (args.columns * args.cell_width, rows_count * args.cell_height), "#171717")
    draw = ImageDraw.Draw(sheet)
    for index, (asset, path) in enumerate(rows):
        x = (index % args.columns) * args.cell_width
        y = (index // args.columns) * args.cell_height
        preview = checkerboard((args.cell_width - padding * 2, args.cell_height - label_height - padding * 2)).convert("RGBA")
        with Image.open(path) as source:
            source = source.convert("RGBA")
            fitted = ImageOps.contain(source, preview.size)
            target_x = (preview.width - fitted.width) // 2
            target_y = (preview.height - fitted.height) // 2
            preview.alpha_composite(fitted, (target_x, target_y))
        sheet.paste(preview.convert("RGB"), (x + padding, y + padding))
        label = f"{asset.get('asset_id', '?')} · {asset.get('asset_type', '?')}"
        draw.text((x + padding, y + args.cell_height - label_height + 8), label, fill="#f5eedc")
    output = args.output if args.output.is_absolute() else project / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
