#!/usr/bin/env python3
"""Check stage-specific runtime requirements without installing anything."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGES = ("script", "audio", "assets", "animation", "master", "all")


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def command_version(command: str, args: list[str] | None = None) -> str | None:
    path = shutil.which(command)
    if not path:
        return None
    try:
        result = subprocess.run([command, *(args or ["--version"])], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=8, check=False)
        first_line = result.stdout.strip().splitlines()
        return f"{path} · {first_line[0]}" if first_line else path
    except Exception:
        return path


def item(identifier: str, status: str, detail: str, remedy: str | None = None) -> dict[str, str]:
    result = {"id": identifier, "status": status, "detail": detail}
    if remedy:
        result["remedy"] = remedy
    return result


def require_command(checks: list[dict[str, str]], command: str, label: str, remedy: str) -> None:
    version = command_version(command)
    if version:
        checks.append(item(label, "pass", version))
    else:
        checks.append(item(label, "blocked", f"未找到命令：{command}", remedy))


def require_python(checks: list[dict[str, str]], require_pillow: bool) -> None:
    if sys.version_info >= (3, 10):
        checks.append(item("python", "pass", f"{sys.executable} · Python {sys.version.split()[0]}"))
    else:
        checks.append(item("python", "blocked", f"Python {sys.version.split()[0]} 低于 3.10", "切换到 Python 3.10 或更高版本后重试。"))
    if require_pillow:
        try:
            import PIL  # noqa: F401
            checks.append(item("pillow", "pass", "Pillow 可用于透明通道检查和联系表。"))
        except ImportError:
            checks.append(item("pillow", "blocked", "当前 Python 环境缺少 Pillow。", "在已选择的项目 Python 环境中安装 Pillow；不要修改系统环境后静默继续。"))


def require_node(checks: list[dict[str, str]], project: Path | None) -> None:
    version = command_version("node", ["--version"])
    if not version:
        checks.append(item("node", "blocked", "未找到 Node.js。", "安装 Node.js 18 或更高版本后重试。"))
    else:
        text = version.rsplit("·", 1)[-1].strip().lstrip("v")
        try:
            major = int(text.split(".", 1)[0])
        except ValueError:
            major = 0
        if major >= 18:
            checks.append(item("node", "pass", version))
        else:
            checks.append(item("node", "blocked", f"{version}；Remotion 模板需要 Node.js 18 或更高版本。", "升级 Node.js 后重试。"))
    require_command(checks, "npm", "npm", "安装与 Node.js 匹配的 npm 后重试。")
    if project:
        remotion = project / "remotion"
        package = remotion / "package.json"
        installed = remotion / "node_modules" / "remotion"
        if not package.is_file():
            checks.append(item("remotion-template", "blocked", "项目中不存在 remotion/package.json。", "重新运行 init_project.py，或确认 project_dir。"))
        elif not installed.exists():
            checks.append(item("remotion-dependencies", "blocked", "Remotion 依赖尚未安装。", "在项目 remotion/ 目录人工确认后运行 npm install。"))
        else:
            checks.append(item("remotion-dependencies", "pass", "检测到项目本地 Remotion 依赖。"))


def require_transcriber(checks: list[dict[str, str]], caption_source: str) -> None:
    if caption_source == "approved-captions":
        checks.append(item("transcriber", "pass", "使用人工提供或已审核的 Caption[]；无需本地转录器。"))
        return
    for command in ("whisper", "whisperx", "whisper-cli"):
        found = command_version(command, ["--help"])
        if found:
            checks.append(item("transcriber", "pass", f"本地转录器可用：{found}"))
            return
    checks.append(item("transcriber", "blocked", "未找到本地 Whisper/WhisperX 转录器。", "安装本地转录器，或由人工提供已审核的 Caption[] 后使用 --caption-source approved-captions。"))


def require_imagegen_confirmation(checks: list[dict[str, str]], confirmed: bool) -> None:
    if confirmed:
        checks.append(item("imagegen", "pass", "Agent 已确认内置 ImageGen 工具在当前线程可用。"))
    else:
        checks.append(item("imagegen", "manual", "内置 ImageGen 是 Agent 工具，shell 无法自行探测。", "Agent 必须先确认当前线程具备内置 ImageGen，再以 --confirm-imagegen 重跑；不得改用 CLI/API。"))


def checks_for(stage: str, project: Path | None, caption_source: str, imagegen_confirmed: bool) -> list[dict[str, str]]:
    selected = ("script", "audio", "assets", "animation", "master") if stage == "all" else (stage,)
    checks: list[dict[str, str]] = []
    if "script" in selected:
        require_python(checks, require_pillow=False)
    if "audio" in selected:
        require_python(checks, require_pillow=False)
        require_command(checks, "ffmpeg", "ffmpeg", "安装 FFmpeg 后重试。")
        require_command(checks, "ffprobe", "ffprobe", "安装 FFmpeg（含 ffprobe）后重试。")
        require_transcriber(checks, caption_source)
    if "assets" in selected:
        require_python(checks, require_pillow=True)
        require_imagegen_confirmation(checks, imagegen_confirmed)
    if "animation" in selected:
        require_node(checks, project)
    if "master" in selected:
        require_python(checks, require_pillow=True)
        require_command(checks, "ffmpeg", "ffmpeg", "安装 FFmpeg 后重试。")
        require_command(checks, "ffprobe", "ffprobe", "安装 FFmpeg（含 ffprobe）后重试。")
    return checks


def write_project_record(project: Path, stage: str, record: dict[str, Any]) -> None:
    state_path = project / "production-state.json"
    if not state_path.is_file():
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))
    environment = state.setdefault("environment", {})
    environment[stage] = record
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--project-dir", type=Path)
    parser.add_argument("--caption-source", choices=["local-asr", "approved-captions"], default="local-asr")
    parser.add_argument("--confirm-imagegen", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    project = args.project_dir.expanduser().resolve() if args.project_dir else None
    if project and not project.is_dir():
        parser.error(f"项目目录不存在：{project}")
    checks = checks_for(args.stage, project, args.caption_source, args.confirm_imagegen)
    blockers = [check for check in checks if check["status"] == "blocked"]
    manual = [check for check in checks if check["status"] == "manual"]
    overall = "blocked" if blockers else "needs_agent_confirmation" if manual else "pass"
    record: dict[str, Any] = {
        "checked_at": now(),
        "stage": args.stage,
        "caption_source": args.caption_source,
        "imagegen_confirmed": args.confirm_imagegen,
        "result": overall,
        "checks": checks,
    }
    if args.json_out:
        output = args.json_out if args.json_out.is_absolute() else (project or Path.cwd()) / args.json_out
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if project:
        write_project_record(project, args.stage, record)
    for check in checks:
        prefix = check["status"].upper()
        print(f"{prefix}: {check['id']} — {check['detail']}")
        if check.get("remedy"):
            print(f"  处理：{check['remedy']}")
    print(f"RESULT: {overall}")
    return 1 if blockers else 2 if manual else 0


if __name__ == "__main__":
    sys.exit(main())
