#!/usr/bin/env python3
"""Split a generated contact sheet into independent chroma-key source frames."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--rows", required=True, type=int)
    parser.add_argument("--columns", required=True, type=int)
    parser.add_argument("--count", required=True, type=int)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--inset", type=int, default=6)
    args = parser.parse_args()

    if args.count > args.rows * args.columns:
        raise SystemExit("--count exceeds available cells")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(args.input) as source:
        image = source.convert("RGB")
        outputs = []
        for index in range(args.count):
            row, column = divmod(index, args.columns)
            x0 = round(column * image.width / args.columns) + args.inset
            x1 = round((column + 1) * image.width / args.columns) - args.inset
            y0 = round(row * image.height / args.rows) + args.inset
            y1 = round((row + 1) * image.height / args.rows) - args.inset
            if x0 >= x1 or y0 >= y1:
                raise SystemExit(f"cell {index} collapsed after inset")
            output = args.out_dir / f"{args.prefix}-{index:02d}.png"
            image.crop((x0, y0, x1, y1)).save(output, optimize=True)
            outputs.append(
                {
                    "file": output.name,
                    "crop": [x0, y0, x1, y1],
                    "size": [x1 - x0, y1 - y0],
                }
            )
    print(json.dumps({"status": "pass", "frames": outputs}, indent=2))


if __name__ == "__main__":
    main()
