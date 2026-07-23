#!/usr/bin/env python3
"""Fingerprint an input and invalidate its dependent approval locks."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


STAGES = ["script", "audio", "storyboard", "style", "assets", "scene_animation", "master"]
START_STAGE = {"format": "storyboard", **{stage: stage for stage in STAGES}}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--stage", choices=sorted(START_STAGE), required=True)
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = args.project_dir.expanduser().resolve()
    state_path = project / "production-state.json"
    source = args.path if args.path.is_absolute() else project / args.path
    source = source.resolve()
    if not source.is_file():
        parser.error(f"输入文件不存在：{source}")
    state = load_json(state_path)
    digest = sha256(source)
    previous = state.setdefault("input_fingerprints", {}).get(args.stage, {}).get("sha256")
    if previous == digest and not args.force:
        print("输入指纹未变化；未取消任何闸门。")
        return 0

    try:
        display_path = str(source.relative_to(project))
    except ValueError:
        display_path = str(source)
    state["input_fingerprints"][args.stage] = {
        "path": display_path,
        "sha256": digest,
        "updated_at": now(),
    }
    first = STAGES.index(START_STAGE[args.stage])
    invalidated = STAGES[first:]
    for stage in invalidated:
        state["locks"][stage] = {"self_review": "pending", "human_approval": "pending", "reports": []}
    state["current_stage"] = STAGES[first]
    state.setdefault("invalidations", []).append({
        "at": now(),
        "input_stage": args.stage,
        "reason": args.reason,
        "invalidated_stages": invalidated,
    })
    if "master" in invalidated:
        state["release_blockers"] = ["等待最终人工确认"]
    save_json(state_path, state)
    print("已取消闸门：" + "、".join(invalidated))
    return 0


if __name__ == "__main__":
    sys.exit(main())
