#!/usr/bin/env python3
"""Build a side-by-side 60 fps review reel from YOLO motion previews."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SCENES = (
    (
        "来源核验 · verified",
        "verify-source-right-verified-60fps.mp4",
        "verify-source-left-verified-60fps.mp4",
    ),
    (
        "来源核验 · not-found",
        "verify-source-right-not-found-60fps.mp4",
        "verify-source-left-not-found-60fps.mp4",
    ),
    (
        "安静观察循环",
        "quiet-observe-right-loop-60fps.mp4",
        "quiet-observe-left-loop-60fps.mp4",
    ),
    (
        "托腮思考循环",
        "chin-think-right-loop-60fps.mp4",
        "chin-think-left-loop-60fps.mp4",
    ),
    (
        "抬手指向 / 轻点",
        "point-tap-right-default-60fps.mp4",
        "point-tap-left-default-60fps.mp4",
    ),
    (
        "接住卡片 / 放入槽位",
        "catch-card-right-default-60fps.mp4",
        "catch-card-left-default-60fps.mp4",
    ),
    (
        "掌心轻挡 / 风险提醒",
        "risk-reminder-right-default-60fps.mp4",
        "risk-reminder-left-default-60fps.mp4",
    ),
)


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def video_duration(path: Path) -> float:
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    return float(json.loads(output)["format"]["duration"])


def label_overlay(title: str, output: Path) -> None:
    image = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    title_font = font(38)
    facing_font = font(27)

    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_left = round((1920 - title_width) / 2) - 34
    draw.rounded_rectangle(
        (title_left, 38, title_left + title_width + 68, 102),
        radius=24,
        fill=(255, 255, 255, 238),
        outline=(213, 220, 228, 255),
        width=2,
    )
    draw.text(
        ((1920 - title_width) / 2, 48),
        title,
        font=title_font,
        fill="#203148",
    )

    for text, center_x in (("右朝向", 170), ("左朝向", 1750)):
        bbox = draw.textbbox((0, 0), text, font=facing_font)
        width = bbox[2] - bbox[0]
        draw.rounded_rectangle(
            (center_x - width / 2 - 22, 45, center_x + width / 2 + 22, 96),
            radius=18,
            fill=(255, 255, 255, 225),
            outline=(213, 220, 228, 255),
            width=2,
        )
        draw.text(
            (center_x - width / 2, 54),
            text,
            font=facing_font,
            fill="#6E7B8F",
        )
    image.save(output, optimize=True)


def render_scene(
    right_video: Path,
    left_video: Path,
    overlay: Path,
    output: Path,
) -> float:
    duration = min(video_duration(right_video), video_duration(left_video))
    fade_out = max(0.0, duration - 0.12)
    filters = (
        "[0:v]crop=960:1080:0:0,setpts=PTS-STARTPTS[right];"
        "[1:v]crop=960:1080:960:0,setpts=PTS-STARTPTS[left];"
        "[right][left]hstack=inputs=2[paired];"
        "[paired][2:v]overlay=0:0:format=auto,"
        "fade=t=in:st=0:d=0.12:color=0xFAF8F3,"
        f"fade=t=out:st={fade_out:.6f}:d=0.12:color=0xFAF8F3,"
        "format=yuv420p[out]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(right_video),
            "-i",
            str(left_video),
            "-loop",
            "1",
            "-i",
            str(overlay),
            "-filter_complex",
            filters,
            "-map",
            "[out]",
            "-an",
            "-r",
            "60",
            "-t",
            f"{duration:.6f}",
            "-c:v",
            "libx264",
            "-crf",
            "17",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ],
        check=True,
    )
    return duration


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    preview_dir = args.preview_dir.resolve()
    output = args.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    durations: list[float] = []

    with tempfile.TemporaryDirectory(prefix="yolo-motion-showreel-") as temp_name:
        temp = Path(temp_name)
        scene_files: list[Path] = []
        for index, (title, right_name, left_name) in enumerate(SCENES):
            right_video = preview_dir / right_name
            left_video = preview_dir / left_name
            if not right_video.is_file() or not left_video.is_file():
                raise FileNotFoundError(f"missing preview pair: {right_video}, {left_video}")
            overlay = temp / f"label-{index:02d}.png"
            scene = temp / f"scene-{index:02d}.mp4"
            label_overlay(title, overlay)
            durations.append(
                render_scene(right_video, left_video, overlay, scene)
            )
            scene_files.append(scene)

        concat_list = temp / "concat.txt"
        concat_list.write_text(
            "".join(f"file '{path}'\n" for path in scene_files)
        )
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output),
            ],
            check=True,
        )

    print(
        json.dumps(
            {
                "status": "pass",
                "output": str(output),
                "scenes": len(SCENES),
                "duration_seconds": round(sum(durations), 3),
                "fps": 60,
                "resolution": [1920, 1080],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
