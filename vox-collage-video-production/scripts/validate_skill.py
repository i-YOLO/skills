#!/usr/bin/env python3
"""Dependency-free structural validation for this skill package."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "scripts/init_project.py",
    "scripts/check_environment.py",
    "scripts/update_input.py",
    "scripts/record_gate.py",
    "scripts/validate_project.py",
    "scripts/audit_assets.py",
    "scripts/build_contact_sheet.py",
    "scripts/audit_master.py",
    "references/production-contract.md",
    "references/environment.md",
    "references/asset-contract.md",
    "references/imagegen-prompts.md",
    "references/remotion-contract.md",
    "references/review-checklist.md",
    "assets/remotion-template/package.json",
    "assets/remotion-template/src/Root.tsx",
    "assets/remotion-template/src/VoxCollageVideo.tsx",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", type=Path)
    args = parser.parse_args()
    root = args.skill_dir.expanduser().resolve()
    errors: list[str] = []
    for relative in REQUIRED:
        if not (root / relative).is_file():
            errors.append(f"缺少：{relative}")
    skill = (root / "SKILL.md").read_text(encoding="utf-8") if (root / "SKILL.md").is_file() else ""
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill, flags=re.S)
    if not frontmatter:
        errors.append("SKILL.md 缺少 YAML frontmatter")
    else:
        fields = frontmatter.group(1)
        if not re.search(r"^name:\s*vox-collage-video-production\s*$", fields, flags=re.M):
            errors.append("SKILL.md name 不匹配")
        if not re.search(r"^description:\s*.+", fields, flags=re.M):
            errors.append("SKILL.md 缺少 description")
    external_workflow_name = "-".join(["xingchen", "vox", "collage"])
    if external_workflow_name in skill:
        errors.append("SKILL.md 不得提及其他具体 Skill")
    interface = (root / "agents/openai.yaml").read_text(encoding="utf-8") if (root / "agents/openai.yaml").is_file() else ""
    for field in ("display_name", "short_description", "default_prompt"):
        if not re.search(rf"^\s*{field}:\s*\".+\"\s*$", interface, flags=re.M):
            errors.append(f"openai.yaml 缺少带引号的 {field}")
    if "$vox-collage-video-production" not in interface:
        errors.append("openai.yaml 的 default_prompt 必须显式引用 Skill")
    for required_text in ("核心素材", "辅助素材", "9:16", "环境预检", "最终人工确认"):
        if required_text not in skill:
            errors.append(f"SKILL.md 缺少关键生产约束：{required_text}")
    for message in errors:
        print(f"ERROR: {message}")
    print("PASS" if not errors else f"FAIL ({len(errors)} errors)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
