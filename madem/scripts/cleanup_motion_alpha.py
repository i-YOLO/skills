#!/usr/bin/env python3
"""Remove detached chroma artifacts while retaining the main subject component."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

from PIL import Image


def components(alpha: Image.Image, threshold: int) -> list[list[tuple[int, int]]]:
    width, height = alpha.size
    pixels = alpha.load()
    visited: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for y in range(height):
        for x in range(width):
            if pixels[x, y] <= threshold or (x, y) in visited:
                continue
            queue = deque([(x, y)])
            visited.add((x, y))
            component: list[tuple[int, int]] = []
            while queue:
                current_x, current_y = queue.popleft()
                component.append((current_x, current_y))
                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if (
                        0 <= next_x < width
                        and 0 <= next_y < height
                        and (next_x, next_y) not in visited
                        and pixels[next_x, next_y] > threshold
                    ):
                        visited.add((next_x, next_y))
                        queue.append((next_x, next_y))
            found.append(component)
    return found


def clean(path: Path, output: Path, threshold: int, minimum_ratio: float) -> dict:
    with Image.open(path) as source:
        image = source.convert("RGBA")
    alpha = image.getchannel("A")
    found = components(alpha, threshold)
    if not found:
        raise ValueError(f"{path} contains no opaque component")
    largest = max(len(component) for component in found)
    keep = {
        point
        for component in found
        if len(component) >= largest * minimum_ratio
        for point in component
    }
    pixels = image.load()
    removed = 0
    for y in range(image.height):
        for x in range(image.width):
            if pixels[x, y][3] > 0 and (x, y) not in keep:
                pixels[x, y] = (0, 0, 0, 0)
                removed += 1
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, optimize=True)
    return {
        "file": output.name,
        "components": len(found),
        "largest_pixels": largest,
        "removed_pixels": removed,
        "bbox": list(image.getchannel("A").getbbox() or ()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--glob", default="*.png")
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--threshold", type=int, default=32)
    parser.add_argument("--minimum-ratio", type=float, default=0.03)
    args = parser.parse_args()
    paths = sorted(args.input_dir.glob(args.glob))
    if not paths:
        raise SystemExit("no matching input images")
    reports = [
        clean(path, args.out_dir / path.name, args.threshold, args.minimum_ratio)
        for path in paths
    ]
    print(json.dumps({"status": "pass", "files": reports}, indent=2))


if __name__ == "__main__":
    main()
