#!/usr/bin/env python3
"""Audit a rendered master and export entry/hold/exit visual evidence."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def rational(value: str | None) -> float:
    if not value:
        return 0.0
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator or 1)
    return float(value)


def make_sheet(paths: list[tuple[str, Path]], output: Path, columns: int = 3) -> None:
    cell_w, cell_h, label_h = 480, 300, 30
    rows = math.ceil(len(paths) / columns)
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "#171717")
    draw = ImageDraw.Draw(sheet)
    for index, (label, path) in enumerate(paths):
        x, y = (index % columns) * cell_w, (index // columns) * cell_h
        with Image.open(path) as frame:
            frame = ImageOps.contain(frame.convert("RGB"), (cell_w - 16, cell_h - label_h - 16))
            sheet.paste(frame, (x + (cell_w - frame.width) // 2, y + 8 + (cell_h - label_h - 16 - frame.height) // 2))
        draw.text((x + 8, y + cell_h - label_h + 6), label, fill="#f5eedc")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def display_path(path: Path, project: Path) -> str:
    try:
        return str(path.relative_to(project))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--report", default="reviews/master-audit.json")
    parser.add_argument("--evidence-dir", default="reviews/master-evidence")
    parser.add_argument("--skip-evidence", action="store_true")
    args = parser.parse_args()
    project = args.project_dir.expanduser().resolve()
    video = args.video if args.video.is_absolute() else project / args.video
    video = video.resolve()
    if not video.is_file():
        parser.error(f"成片不存在：{video}")
    for binary in ("ffprobe", "ffmpeg"):
        if not shutil.which(binary):
            parser.error(f"缺少 {binary}")
    state = json.loads((project / "production-state.json").read_text(encoding="utf-8"))
    storyboard = json.loads((project / "storyboard.json").read_text(encoding="utf-8"))
    probe = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)])
    if probe.returncode:
        parser.error(probe.stderr.strip() or "ffprobe 失败")
    media = json.loads(probe.stdout)
    streams = media.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), None)
    errors: list[str] = []
    warnings: list[str] = []
    if not video_stream:
        errors.append("缺少视频流")
    if not audio_stream:
        errors.append("缺少音频流")
    expected = state.get("format", {})
    if video_stream:
        if (video_stream.get("width"), video_stream.get("height")) != (expected.get("width"), expected.get("height")):
            errors.append("视频尺寸与项目格式不一致")
        fps = rational(video_stream.get("avg_frame_rate"))
        if abs(fps - float(expected.get("fps", 0))) > 0.01:
            errors.append(f"视频帧率 {fps:.3f} 与项目帧率不一致")
    video_duration = float(video_stream.get("duration") or media.get("format", {}).get("duration") or 0) if video_stream else 0
    audio_duration = float(audio_stream.get("duration") or media.get("format", {}).get("duration") or 0) if audio_stream else 0
    if video_stream and audio_stream and abs(video_duration - audio_duration) > 1 / float(expected.get("fps", 30)) + 0.002:
        errors.append(f"音视频时长差 {abs(video_duration - audio_duration) * 1000:.1f}ms，超过一帧")

    decode = run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(video), "-f", "null", "-"])
    if decode.returncode:
        errors.append("FFmpeg 完整解码失败：" + decode.stderr.strip()[:300])
    black = run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(video), "-vf", "blackdetect=d=0.25:pic_th=0.98", "-an", "-f", "null", "-"])
    black_hits = [line for line in black.stderr.splitlines() if "black_start:" in line]
    if black_hits:
        warnings.append(f"检测到 {len(black_hits)} 段超过 0.25 秒黑帧；人工确认是否为有意转场")
    freeze = run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(video), "-vf", "freezedetect=n=0.003:d=4", "-an", "-f", "null", "-"])
    freeze_hits = [line for line in freeze.stderr.splitlines() if "freeze_start:" in line]
    if freeze_hits:
        warnings.append(f"检测到 {len(freeze_hits)} 段超过 4 秒静帧；人工确认是否为阅读停留")

    evidence: dict[str, str] = {}
    if not args.skip_evidence and video_stream:
        evidence_arg = Path(args.evidence_dir)
        output_dir = (evidence_arg if evidence_arg.is_absolute() else project / evidence_arg).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        phases: dict[str, list[tuple[str, Path]]] = {"entry": [], "hold": [], "exit": []}
        fps = float(expected.get("fps", 30))
        for scene in storyboard.get("scenes", []):
            start = int(scene.get("from_frame", 0))
            duration = int(scene.get("duration_frames", 1))
            scene_id = scene.get("id", "scene")
            frame_numbers = {
                "entry": start + min(2, max(0, duration - 1)),
                "hold": start + max(0, duration // 2),
                "exit": start + max(0, duration - 2),
            }
            for phase, frame_number in frame_numbers.items():
                target = output_dir / f"{scene_id.lower()}-{phase}.png"
                extract = run([
                    "ffmpeg", "-v", "error", "-nostdin", "-ss", f"{frame_number / fps:.6f}", "-i", str(video),
                    "-frames:v", "1", "-y", str(target),
                ])
                if extract.returncode or not target.is_file():
                    errors.append(f"无法导出 {scene_id} {phase} 证据帧")
                else:
                    phases[phase].append((f"{scene_id} · {frame_number}f", target))
        for phase, frames in phases.items():
            if frames:
                sheet = output_dir / f"{phase}-contact-sheet.png"
                make_sheet(frames, sheet)
                evidence[phase] = display_path(sheet, project)

    report = {
        "generated_at": now(),
        "video": str(video),
        "result": "fail" if errors else "pass",
        "validation": {
            "video_stream": bool(video_stream),
            "audio_stream": bool(audio_stream),
            "video_duration_seconds": video_duration,
            "audio_duration_seconds": audio_duration,
            "duration_delta_ms": abs(video_duration - audio_duration) * 1000,
            "full_ffmpeg_decode": decode.returncode == 0,
            "black_frame_hits": len(black_hits),
            "static_frame_hits": len(freeze_hits),
        },
        "evidence": evidence,
        "warnings": warnings,
        "errors": errors,
    }
    report_arg = Path(args.report)
    report_path = report_arg if report_arg.is_absolute() else project / report_arg
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['result'].upper()}: {report_path}")
    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
