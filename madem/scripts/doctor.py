#!/usr/bin/env python3
"""Report video-skill prerequisites without installing anything."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_RUNTIME = Path("/Users/shike/.codex/runtimes/video-skills-py311")


def run(command: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=12)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    text = (result.stdout or result.stderr).strip().splitlines()
    return result.returncode == 0, text[0] if text else ""


def command_check(name: str, arguments: list[str] | None = None) -> dict:
    location = shutil.which(name)
    if not location:
        return {"status": "missing", "path": None, "detail": "command not found"}
    ok, version = run([location, *(arguments or ["--version"])])
    return {"status": "ok" if ok else "warning", "path": location, "detail": version}


def module_check(python: Path, module: str) -> dict:
    if not python.exists():
        return {"status": "missing", "detail": f"runtime missing: {python}"}
    code = (
        "import importlib.util; import sys; "
        f"spec=importlib.util.find_spec({module!r}); "
        "print('ok' if spec else 'missing'); sys.exit(0 if spec else 1)"
    )
    ok, detail = run([str(python), "-c", code])
    return {"status": "ok" if ok else "missing", "detail": detail or module}


def browser_check() -> dict:
    candidates = [
        Path("/Applications/Google Chrome.app"),
        Path("/Applications/Chromium.app"),
        Path("/Applications/Google Chrome Canary.app"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return {"status": "ok", "path": str(candidate), "detail": "browser app found"}
    for name in ("google-chrome", "chromium", "chromium-browser"):
        location = shutil.which(name)
        if location:
            return {"status": "ok", "path": location, "detail": "browser command found"}
    return {"status": "missing", "path": None, "detail": "no supported browser found"}


def font_check(font: str) -> dict:
    matcher = shutil.which("fc-match")
    if matcher:
        ok, detail = run([matcher, "--format=%{family}", font])
        exact = font.casefold() in detail.casefold()
        return {"status": "ok" if ok and exact else "warning", "detail": detail or "font substitution"}
    if platform.system() == "Darwin":
        ok, detail = run(["system_profiler", "SPFontsDataType"])
        return {"status": "ok" if ok and font.casefold() in detail.casefold() else "warning", "detail": "manual font verification required"}
    return {"status": "warning", "detail": "no font checker available"}


def project_check(project: Path) -> dict:
    result: dict[str, object] = {"path": str(project), "status": "ok", "checks": {}}
    if not project.exists():
        result["status"] = "missing"
        result["checks"] = {"project": "directory not found"}
        return result
    package_file = project / "package.json"
    if package_file.exists():
        try:
            package = json.loads(package_file.read_text())
            dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
            result["checks"]["remotion"] = "ok" if "remotion" in dependencies else "missing"
        except (OSError, json.JSONDecodeError) as exc:
            result["checks"]["package_json"] = f"invalid: {exc}"
            result["status"] = "warning"
    else:
        result["checks"]["remotion"] = "not checked: package.json missing"
    locks = [name for name in ("package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock") if (project / name).exists()]
    result["checks"]["lockfile"] = locks or "missing"
    if not locks:
        result["status"] = "warning"
    return result


def model_check(model: str) -> dict:
    cache_root = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    candidates = list(cache_root.glob(f"*{model.replace('-', '_')}*")) + list(cache_root.glob(f"*{model}*"))
    return {"status": "ok" if candidates else "missing", "detail": [str(path) for path in candidates] or "download on first approved transcription"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--font", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    runtime_python = args.runtime / "bin" / "python"
    report: dict[str, object] = {
        "platform": platform.platform(),
        "runtime": str(args.runtime),
        "checks": {
            "node": command_check("node"),
            "npm": command_check("npm"),
            "npx": command_check("npx"),
            "ffmpeg": command_check("ffmpeg", ["-version"]),
            "ffprobe": command_check("ffprobe", ["-version"]),
            "browser": browser_check(),
            "faster_whisper": module_check(runtime_python, "faster_whisper"),
            "manim": module_check(runtime_python, "manim"),
            "model": model_check(args.model),
        },
    }
    if args.project:
        report["project"] = project_check(args.project)
    if args.font:
        report["fonts"] = {font: font_check(font) for font in args.font}

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n")
    print(payload)


if __name__ == "__main__":
    main()
