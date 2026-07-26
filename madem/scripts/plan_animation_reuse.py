#!/usr/bin/env python3
"""Suggest reusable animation patterns for narration units; require semantic review before reuse."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PATTERNS = [
    {
        "id": "pipeline-flow",
        "component": "PipelineFlow",
        "keywords": ("先", "再", "然后", "最后", "步骤", "流程", "进入"),
        "minimum_hits": 2,
        "reason": "包含明确先后顺序的生产或教学链路",
    },
    {
        "id": "contrast-cards",
        "component": "ContrastCards",
        "keywords": ("不是", "而是", "对比", "区别", "旧规则", "新规则", "优点", "缺点"),
        "minimum_hits": 1,
        "reason": "包含两种方案、状态或观点的对照",
    },
    {
        "id": "cycle-flow",
        "component": "CycleFlow",
        "keywords": ("循环", "迭代", "复盘", "再执行", "反复", "持续改进"),
        "minimum_hits": 1,
        "reason": "包含回到起点的重复改进关系",
    },
    {
        "id": "layer-cards",
        "component": "LayerCards",
        "keywords": ("拆成", "图层", "分层", "分别", "模块", "素材", "背景"),
        "minimum_hits": 2,
        "reason": "包含可独立修改、可并列管理的层或模块",
    },
    {
        "id": "timeline-anchor",
        "component": "TimelineAnchor",
        "keywords": ("时间轴", "关键词", "停顿", "帧位", "说到", "出现", "转场"),
        "minimum_hits": 2,
        "reason": "包含语音、事件或动作的时间锚点",
    },
    {
        "id": "compounding-flywheel",
        "component": "CompoundingFlywheel",
        "keywords": ("飞轮", "复利", "积累", "每次", "判断库", "越转"),
        "minimum_hits": 2,
        "reason": "包含循环带来持续累积的机制",
    },
    {
        "id": "sequential-chips",
        "component": "SequentialChips",
        "keywords": ("、", "以及", "并且", "同时", "再验证"),
        "minimum_hits": 1,
        "reason": "包含可拆为短词或短动作的并列结构",
    },
]


def split_units(text: str) -> list[str]:
    units = []
    for block in re.split(r"\n\s*\n", text):
        cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)、])\s*", "", block.strip())
        if not cleaned or cleaned.startswith("#") or cleaned.startswith("|"):
            continue
        units.extend(part.strip() for part in re.split(r"(?<=[。！？；])", cleaned) if part.strip())
    return units


def candidates(unit: str) -> list[dict[str, object]]:
    matches = []
    for pattern in PATTERNS:
        hits = [keyword for keyword in pattern["keywords"] if keyword in unit]
        if len(hits) >= pattern["minimum_hits"]:
            matches.append({
                "id": pattern["id"],
                "component": pattern["component"],
                "score": len(hits),
                "matched_cues": hits,
                "reason": pattern["reason"],
            })
    return sorted(matches, key=lambda item: (-int(item["score"]), str(item["id"])))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    text = args.script.read_text(encoding="utf-8")
    plan = []
    for index, unit in enumerate(split_units(text), start=1):
        options = candidates(unit)
        plan.append({
            "unit": index,
            "text": unit,
            "candidates": options,
            "decision": "semantic-review-required" if options else "new-animation-needed",
        })
    result = {
        "script": str(args.script.resolve()),
        "units": plan,
        "note": "Candidates are structural hints, not automatic choices. Reuse only when the animation expresses the narration's actual relationship.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
