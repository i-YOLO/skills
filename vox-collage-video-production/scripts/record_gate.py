#!/usr/bin/env python3
"""Record an agent self-review or explicit human gate for a video project."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


STAGES = ["script", "audio", "storyboard", "style", "assets", "scene_animation", "master"]


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--kind", choices=["self", "human"], required=True)
    parser.add_argument("--result", choices=["pass", "fail", "approved", "rejected"], required=True)
    parser.add_argument("--report")
    parser.add_argument("--statement")
    parser.add_argument("--explicit-final-approval", action="store_true")
    args = parser.parse_args()

    valid = {"self": {"pass", "fail"}, "human": {"approved", "rejected"}}
    if args.result not in valid[args.kind]:
        parser.error(f"{args.kind} 仅接受：{', '.join(sorted(valid[args.kind]))}")
    if args.kind == "self" and not args.report:
        parser.error("自检必须提供 --report")
    if args.kind == "human" and not args.statement:
        parser.error("人工闸门必须原样记录 --statement")
    if args.explicit_final_approval and not (args.stage == "master" and args.kind == "human" and args.result == "approved"):
        parser.error("--explicit-final-approval 只可用于 master 的人工批准")
    if args.stage == "master" and args.kind == "human" and args.result == "approved" and not args.explicit_final_approval:
        parser.error("成片终审必须添加 --explicit-final-approval，且只能在用户明确终审后执行")

    project = args.project_dir.expanduser().resolve()
    state_path = project / "production-state.json"
    state = load(state_path)
    lock = state["locks"][args.stage]
    at = now()
    if args.kind == "self":
        lock["self_review"] = args.result
        lock.setdefault("reports", []).append({"kind": "self", "result": args.result, "path": args.report, "at": at})
        if args.result == "fail":
            state["current_stage"] = args.stage
    else:
        if args.result == "approved":
            if lock.get("self_review") != "pass":
                parser.error("人工批准前必须记录本阶段自检通过")
            stage_index = STAGES.index(args.stage)
            if stage_index and state["locks"][STAGES[stage_index - 1]].get("human_approval") != "approved":
                parser.error("前一阶段尚未获人工批准")
        lock["human_approval"] = args.result
        lock.setdefault("reports", []).append({"kind": "human", "result": args.result, "statement": args.statement, "at": at})
        if args.result == "approved":
            next_index = STAGES.index(args.stage) + 1
            state["current_stage"] = STAGES[next_index] if next_index < len(STAGES) else "master"
            if args.stage == "master":
                state["release_blockers"] = []
        else:
            state["current_stage"] = args.stage
    state.setdefault("approval_log", []).append({
        "stage": args.stage,
        "kind": args.kind,
        "result": args.result,
        "at": at,
        "report": args.report,
        "statement": args.statement,
    })
    save(state_path, state)
    print(f"已记录：{args.stage} / {args.kind} / {args.result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
