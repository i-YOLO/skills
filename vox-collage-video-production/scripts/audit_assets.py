#!/usr/bin/env python3
"""Check selected image assets for paths and basic alpha-channel hygiene."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def resolve(project: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else project / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--manifest", default="assets.json")
    parser.add_argument("--report", default="reviews/assets-audit.json")
    args = parser.parse_args()
    project = args.project_dir.expanduser().resolve()
    manifest = json.loads((project / args.manifest).read_text(encoding="utf-8"))
    rows: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []
    for asset in manifest.get("assets", []):
        if asset.get("asset_type") == "code":
            continue
        identifier = asset.get("asset_id", "unknown")
        path = resolve(project, asset.get("render_path") or asset.get("processed_path"))
        result: dict[str, object] = {"asset_id": identifier, "path": str(path) if path else None, "checks": []}
        if not path or not path.is_file():
            errors.append(f"{identifier} 缺少可用的 render_path")
            result["result"] = "fail"
            rows.append(result)
            continue
        try:
            with Image.open(path) as image:
                image.load()
                result["size"] = list(image.size)
                result["mode"] = image.mode
                if image.width < 64 or image.height < 64:
                    warnings.append(f"{identifier} 尺寸过小：{image.width}×{image.height}")
                alpha_required = bool(asset.get("transparency_required"))
                if alpha_required and "A" not in image.getbands():
                    errors.append(f"{identifier} 要求透明通道，但文件没有 alpha")
                elif alpha_required:
                    alpha = image.getchannel("A")
                    corners = [alpha.getpixel(point) for point in ((0, 0), (image.width - 1, 0), (0, image.height - 1), (image.width - 1, image.height - 1))]
                    result["corner_alpha"] = corners
                    if min(corners) > 12:
                        warnings.append(f"{identifier} 四角不透明；确认这不是未抠背景")
                result["result"] = "pass"
        except Exception as exc:  # Pillow errors should become a material audit failure.
            errors.append(f"{identifier} 无法读取：{exc}")
            result["result"] = "fail"
        rows.append(result)
    report = {"generated_at": now(), "result": "fail" if errors else "pass", "errors": errors, "warnings": warnings, "assets": rows}
    output = project / args.report
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['result'].upper()}: {output}")
    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
