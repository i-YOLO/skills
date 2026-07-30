#!/usr/bin/env python3
"""Refresh SHA-256 values for every file declared in a YOLO motion catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh_entry(root: Path, entry: dict[str, Any]) -> None:
    file = entry.get("file")
    if file:
        path = root / file
        if not path.is_file():
            raise FileNotFoundError(path)
        entry["sha256"] = digest(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text())
    root = args.catalog.parent
    for entry in catalog.get("identity", []):
        refresh_entry(root, entry)
    for prop in catalog.get("props", {}).values():
        refresh_entry(root, prop)
    for motion in catalog.get("motions", []):
        for facing in motion.get("facings", {}).values():
            for frame in facing.get("common", []):
                refresh_entry(root, frame)
            for branch in facing.get("branches", {}).values():
                for frame in branch:
                    refresh_entry(root, frame)

    args.catalog.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    print(args.catalog)


if __name__ == "__main__":
    main()
