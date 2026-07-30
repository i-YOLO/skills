#!/usr/bin/env python3
"""Render YOLO motion catalog entries as review stills and 60 fps MP4 files."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


BACKGROUND = "#FAF8F3"
INK = "#203148"
MUTED = "#6E7B8F"
ACCENT = "#D9E9FF"
CANVAS_1080P = (1920, 1080)


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def find_motion(catalog: dict, asset_id: str) -> dict:
    for motion in catalog["motions"]:
        if motion["asset_id"] == asset_id:
            return motion
    raise ValueError(f"motion not found: {asset_id}")


def flatten_frames(motion: dict, facing: str, outcome: str) -> list[dict]:
    facing_data = motion["facings"][facing]
    return [*facing_data["common"], *facing_data["branches"][outcome]]


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def set_opacity(image: Image.Image, opacity: float) -> Image.Image:
    if opacity >= 1:
        return image
    result = image.copy()
    alpha = result.getchannel("A").point(lambda value: round(value * opacity))
    result.putalpha(alpha)
    return result


def add_prop(
    logical: Image.Image,
    prop_source: Image.Image,
    prop_config: dict,
    prop_track: dict,
    facing: str,
) -> Image.Image:
    opacity = float(prop_track.get("opacity", 1))
    if opacity <= 0:
        return logical

    width = int(prop_config["logical_width"])
    prop = ImageOps.contain(prop_source, (width, width), Image.Resampling.LANCZOS)
    if facing == "left" and prop_config.get("mirror_for_left"):
        prop = ImageOps.mirror(prop)
    prop = set_opacity(prop, opacity)

    anchor_norm = prop_config["grip_anchor"][facing]
    grip_x = anchor_norm[0] * prop.width
    grip_y = anchor_norm[1] * prop.height
    target_x = float(prop_track["x"])
    target_y = float(prop_track["y"])

    prop_layer = Image.new("RGBA", logical.size, (0, 0, 0, 0))
    prop_layer.alpha_composite(
        prop,
        (
            round(target_x - grip_x),
            round(target_y - grip_y),
        ),
    )
    rotation = float(prop_track.get("rotation", 0))
    if rotation:
        prop_layer = prop_layer.rotate(
            -rotation,
            resample=Image.Resampling.BICUBIC,
            center=(target_x, target_y),
        )
    return Image.alpha_composite(logical, prop_layer)


def render_character_canvas(
    root: Path,
    catalog: dict,
    frame: dict,
    facing: str,
) -> Image.Image:
    production = catalog["production"]
    canvas = tuple(production["canvas"])
    logical = Image.new("RGBA", canvas, (0, 0, 0, 0))
    logical.alpha_composite(load_rgba(root / frame["file"]))
    tracks = frame.get("props")
    if tracks is None:
        tracks = [{"id": "magnifier", **frame["prop"]}] if "prop" in frame else []
    for track in tracks:
        prop_config = catalog["props"][track["id"]]
        prop_source = load_rgba(root / prop_config["file"])
        logical = add_prop(logical, prop_source, prop_config, track, facing)
    return logical


def compose_1080p(
    root: Path,
    catalog: dict,
    frame: dict,
    facing: str,
    display_height: int,
    show_guides: bool = False,
) -> Image.Image:
    production = catalog["production"]
    slot_name = "lower-left" if facing == "right" else "lower-right"
    slot = production["reserved_slots_1080p"][slot_name]
    foot_anchor_x, foot_anchor_y = production["foot_anchor"]
    subject_height = production["subject_height_px"]
    scale = display_height / subject_height

    logical = render_character_canvas(root, catalog, frame, facing)
    logical = logical.resize(
        (round(logical.width * scale), round(logical.height * scale)),
        Image.Resampling.LANCZOS,
    )
    foot_target_x = (slot["x_min"] + slot["x_max"]) / 2
    foot_target_y = production["content_max_y_1080p"]
    paste_x = round(foot_target_x - foot_anchor_x * scale)
    paste_y = round(foot_target_y - foot_anchor_y * scale)

    result = Image.new("RGBA", CANVAS_1080P, BACKGROUND)
    if show_guides:
        draw = ImageDraw.Draw(result)
        draw.rounded_rectangle(
            (slot["x_min"], slot["y_min"], slot["x_max"], slot["y_max"]),
            radius=18,
            fill="#F2F5F8",
            outline="#C8D2DE",
            width=2,
        )
        safe = production["caption_safe_region_1080p"]
        draw.rectangle(
            (safe["x_min"], safe["y_min"], safe["x_max"], safe["y_max"]),
            fill="#FFF1DB",
            outline="#E3B96E",
            width=2,
        )
        draw.line(
            (0, foot_target_y, CANVAS_1080P[0], foot_target_y),
            fill="#E3B96E",
            width=2,
        )
    result.alpha_composite(logical, (paste_x, paste_y))
    return result.convert("RGB")


def render_card_background(facing: str) -> Image.Image:
    result = Image.new("RGBA", CANVAS_1080P, BACKGROUND)
    draw = ImageDraw.Draw(result)
    card_x = 500 if facing == "right" else 180
    card_w = 920
    draw.rounded_rectangle(
        (card_x, 150, card_x + card_w, 720),
        radius=38,
        fill="#FFFFFF",
        outline="#DFE4EA",
        width=3,
    )
    draw.rounded_rectangle(
        (card_x + 70, 235, card_x + 365, 276),
        radius=18,
        fill=ACCENT,
    )
    draw.rounded_rectangle(
        (card_x + 70, 320, card_x + card_w - 70, 346),
        radius=13,
        fill="#D7DDE5",
    )
    draw.rounded_rectangle(
        (card_x + 70, 380, card_x + card_w - 190, 406),
        radius=13,
        fill="#E4E8ED",
    )
    draw.rounded_rectangle(
        (card_x + 70, 440, card_x + card_w - 290, 466),
        radius=13,
        fill="#E4E8ED",
    )
    return result


def composite_scene(
    root: Path,
    catalog: dict,
    frame: dict,
    facing: str,
    display_height: int,
) -> Image.Image:
    base = render_card_background(facing)
    character = compose_1080p(root, catalog, frame, facing, display_height)
    mask = Image.new("L", CANVAS_1080P, 0)
    slot_name = "lower-left" if facing == "right" else "lower-right"
    slot = catalog["production"]["reserved_slots_1080p"][slot_name]
    ImageDraw.Draw(mask).rectangle(
        (slot["x_min"] - 120, slot["y_min"] - 180, slot["x_max"] + 120, slot["y_max"]),
        fill=255,
    )
    return Image.composite(character, base.convert("RGB"), mask)


def write_size_review(
    root: Path,
    catalog: dict,
    motion: dict,
    output: Path,
) -> None:
    panel_w, panel_h = 960, 540
    review = Image.new("RGB", (panel_w * 3, panel_h * 2), BACKGROUND)
    draw = ImageDraw.Draw(review)
    title_font = load_font(30)
    small_font = load_font(23)
    sizes = (280, 320, 380)
    outcomes = ("not-found", "verified")
    for row, outcome in enumerate(outcomes):
        for col, display_height in enumerate(sizes):
            frame = flatten_frames(motion, "right", outcome)[-1]
            scene = composite_scene(root, catalog, frame, "right", display_height)
            scene = scene.resize((panel_w, panel_h), Image.Resampling.LANCZOS)
            review.paste(scene, (col * panel_w, row * panel_h))
            draw.rounded_rectangle(
                (col * panel_w + 24, row * panel_h + 20, col * panel_w + 330, row * panel_h + 78),
                radius=16,
                fill="#FFFFFFE8",
                outline="#D5DCE4",
                width=2,
            )
            draw.text(
                (col * panel_w + 44, row * panel_h + 31),
                f"{outcome} · {display_height}px",
                font=small_font,
                fill=INK,
            )
    draw.text((38, 1012), "YOLO verify-source · #FAF8F3 · 1080p placement review", font=title_font, fill=MUTED)
    output.parent.mkdir(parents=True, exist_ok=True)
    review.save(output, optimize=True)


def write_contact_sheet(
    root: Path,
    catalog: dict,
    motion: dict,
    facing: str,
    outcome: str,
    output: Path,
) -> None:
    entries = flatten_frames(motion, facing, outcome)
    thumb_w, thumb_h = 320, 360
    columns = 4
    rows = (len(entries) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_w, rows * thumb_h + 70), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = load_font(22)
    draw.text((24, 20), f"{motion['asset_id']} · {facing} · {outcome}", font=font, fill=INK)
    for index, entry in enumerate(entries):
        logical = render_character_canvas(root, catalog, entry, facing)
        bbox = logical.getbbox()
        subject = logical.crop(bbox) if bbox else logical
        subject.thumbnail((260, 285), Image.Resampling.LANCZOS)
        x0 = (index % columns) * thumb_w
        y0 = 70 + (index // columns) * thumb_h
        sheet.paste(
            Image.new("RGB", (thumb_w - 12, thumb_h - 12), "#FFFFFF"),
            (x0 + 6, y0 + 6),
        )
        x = x0 + (thumb_w - subject.width) // 2
        y = y0 + 18 + (285 - subject.height)
        sheet.paste(subject, (x, y), subject)
        draw.text(
            (x0 + 18, y0 + 314),
            f"{index:02d} · {entry['ticks']} tick",
            font=font,
            fill=MUTED,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)


def render_video(
    root: Path,
    catalog: dict,
    motion: dict,
    facing: str,
    outcome: str,
    output: Path,
    display_height: int,
) -> None:
    source_fps = int(catalog["source_fps"])
    output_fps = int(catalog["production"]["output_video_fps"])
    if output_fps % source_fps:
        raise ValueError("output fps must be an integer multiple of source fps")
    repeat = output_fps // source_fps
    entries = flatten_frames(motion, facing, outcome)
    cycles = 2 if motion.get("playback_mode") == "loop" else 1
    with tempfile.TemporaryDirectory(prefix="yolo-motion-preview-") as temp_name:
        temp = Path(temp_name)
        frame_index = 0
        for _ in range(cycles):
            for entry in entries:
                scene = composite_scene(root, catalog, entry, facing, display_height)
                repeats = int(entry["ticks"]) * repeat
                for _ in range(repeats):
                    scene.save(temp / f"frame-{frame_index:04d}.png", compress_level=2)
                    frame_index += 1
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-framerate",
                str(output_fps),
                "-i",
                str(temp / "frame-%04d.png"),
                "-c:v",
                "libx264",
                "-crf",
                "17",
                "-preset",
                "medium",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output),
            ],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--motion-id", default="all")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--display-height", type=int, default=320)
    args = parser.parse_args()

    catalog_path = args.catalog.resolve()
    root = catalog_path.parent
    output_dir = (args.output_dir or root / "previews").resolve()
    catalog = json.loads(catalog_path.read_text())
    motions = (
        catalog["motions"]
        if args.motion_id == "all"
        else [find_motion(catalog, args.motion_id)]
    )

    video_count = 0
    sheet_count = 0
    for motion in motions:
        if motion["asset_id"] == "yolo-verify-source":
            write_size_review(root, catalog, motion, output_dir / "verify-source-size-review.png")
        motion_stem = motion["asset_id"].removeprefix("yolo-")
        for facing in ("right", "left"):
            for outcome in motion["outcomes"]:
                stem = f"{motion_stem}-{facing}-{outcome}"
                write_contact_sheet(
                    root,
                    catalog,
                    motion,
                    facing,
                    outcome,
                    output_dir / f"{stem}-contact-sheet.png",
                )
                sheet_count += 1
                render_video(
                    root,
                    catalog,
                    motion,
                    facing,
                    outcome,
                    output_dir / f"{stem}-60fps.mp4",
                    args.display_height,
                )
                video_count += 1

    print(
        json.dumps(
            {
                "status": "pass",
                "motions": [motion["asset_id"] for motion in motions],
                "output_dir": str(output_dir),
                "display_height": args.display_height,
                "videos": video_count,
                "contact_sheets": sheet_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
