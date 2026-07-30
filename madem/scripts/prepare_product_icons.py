#!/usr/bin/env python3
"""Build hash-locked transparent product-icon assets from an explicit catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_png(source: Path, output: Path, size: int) -> dict[str, Any]:
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
        if image.size != (size, size):
            image = image.resize((size, size), Image.Resampling.LANCZOS)
        pixels = image.load()
        for x, y in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
            red, green, blue, _ = pixels[x, y]
            pixels[x, y] = (red, green, blue, 0)
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output, optimize=True)
        alpha = image.getchannel("A")
        return {
            "size": [size, size],
            "mode": "RGBA",
            "alpha_bbox": list(alpha.getbbox() or (0, 0, 0, 0)),
            "corner_alpha": [
                alpha.getpixel((0, 0)),
                alpha.getpixel((size - 1, 0)),
                alpha.getpixel((0, size - 1)),
                alpha.getpixel((size - 1, size - 1)),
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "assets/product-icons/v2/catalog.json",
    )
    parser.add_argument("--update-catalog", action="store_true")
    args = parser.parse_args()

    catalog_path = args.catalog.expanduser().resolve()
    root = catalog_path.parent
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    output_size = int(catalog["raster_contract"]["size"])
    results: list[dict[str, Any]] = []

    for asset in catalog["assets"]:
        source = root / asset["source_file"]
        if not source.is_file():
            raise FileNotFoundError(f"missing source for {asset['asset_id']}: {source}")
        source_hash = sha256(source)
        if asset.get("source_sha256") and source_hash != asset["source_sha256"]:
            raise ValueError(f"source hash mismatch for {asset['asset_id']}")
        asset["source_sha256"] = source_hash
        canonical = root / asset["canonical_file"]
        if source.suffix.lower() == ".svg":
            canonical = source
            details = {"kind": "svg", "size": None, "mode": "vector"}
        else:
            details = normalize_png(source, canonical, output_size)
            details["kind"] = "png"
        canonical_hash = sha256(canonical)
        if asset.get("sha256") and canonical_hash != asset["sha256"]:
            raise ValueError(f"canonical hash mismatch for {asset['asset_id']}")
        asset["sha256"] = canonical_hash
        asset["alpha_bbox"] = details.get("alpha_bbox")
        results.append(
            {
                "asset_id": asset["asset_id"],
                "source_sha256": source_hash,
                "canonical_sha256": canonical_hash,
                **details,
            }
        )

    if args.update_catalog:
        catalog_path.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {"status": "pass", "catalog": str(catalog_path), "assets": results},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
