#!/usr/bin/env python3
"""Build proofread, frame-locked captions from an approved script and word timings."""

from __future__ import annotations

import argparse
import difflib
import json
from bisect import bisect_left
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PUNCTUATION = set("，。！？；：、,.!?;:")


@dataclass(frozen=True)
class TimedChar:
    char: str
    start: float
    end: float


@dataclass(frozen=True)
class CaptionCue:
    text: str
    start: float
    end: float


def visible_units(text: str) -> float:
    units, in_ascii = 0.0, False
    for char in text:
        if char.isspace():
            continue
        if char.isascii() and char.isalnum():
            units += 0.52 + (0.35 if not in_ascii else 0.0)
            in_ascii = True
        else:
            units += 1.0
            in_ascii = False
    return units


def normalise(char: str) -> str | None:
    if "\u4e00" <= char <= "\u9fff":
        return char
    if char.isascii() and char.isalnum():
        return char.lower()
    return None


def approved_script(path: Path) -> str:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    text = "\n".join(
        line
        for line in lines
        if line and not line.startswith(("#", ">"))
    )
    if not text:
        raise ValueError("approved script has no spoken text")
    return text


def timing_map(script: str, words: list[dict[str, Any]]) -> tuple[dict[int, tuple[float, float]], float, float]:
    script_chars = [(index, normalised) for index, char in enumerate(script) if (normalised := normalise(char))]
    spoken_chars = [
        TimedChar(normalised, float(word["start"]), float(word["end"]))
        for word in words
        if "start" in word and "end" in word
        for char in str(word.get("text", ""))
        if (normalised := normalise(char))
    ]
    if not script_chars or not spoken_chars:
        raise ValueError("approved script and timeline.words must both contain spoken characters")

    matcher = difflib.SequenceMatcher(
        a=[char for _, char in script_chars],
        b=[item.char for item in spoken_chars],
        autojunk=False,
    )
    mapped: dict[int, tuple[float, float]] = {}
    for tag, left_start, left_end, right_start, right_end in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(left_end - left_start):
                mapped[script_chars[left_start + offset][0]] = (
                    spoken_chars[right_start + offset].start,
                    spoken_chars[right_start + offset].end,
                )
    exact_coverage = len(mapped) / len(script_chars)
    known = sorted(mapped)
    if not known:
        raise ValueError("no approved-script characters matched the word timeline")
    for index, _ in script_chars:
        if index in mapped:
            continue
        right_at = bisect_left(known, index)
        left = known[right_at - 1] if right_at else None
        right = known[right_at] if right_at < len(known) else None
        if left is None:
            mapped[index] = mapped[right]  # type: ignore[index]
        elif right is None:
            mapped[index] = mapped[left]
        else:
            left_end = mapped[left][1]
            right_start = mapped[right][0]
            ratio = (index - left) / (right - left)
            instant = left_end + (right_start - left_end) * ratio
            mapped[index] = (instant, instant)
    coverage = len(mapped) / len(script_chars)
    return mapped, exact_coverage, coverage


def clauses(script: str) -> list[tuple[int, int]]:
    result, start = [], 0
    for index, char in enumerate(script):
        if char in PUNCTUATION:
            result.append((start, index + 1))
            start = index + 1
        elif char == "\n":
            if start < index:
                result.append((start, index))
            start = index + 1
    if start < len(script):
        result.append((start, len(script)))
    return [(left, right) for left, right in result if script[left:right].strip()]


def single_line(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def split_display(
    text: str,
    start_index: int,
    max_units: float,
) -> list[tuple[str, int, int]]:
    if visible_units(text) <= max_units:
        return [(text, start_index, start_index + len(text))]
    result, current, current_start = [], "", start_index
    for index, char in enumerate(text, start=start_index):
        if current and visible_units(current + char) > max_units:
            result.append((current, current_start, index))
            current, current_start = char, index
        else:
            current += char
    if current:
        result.append((current, current_start, start_index + len(text)))
    return result


def raw_captions(
    script: str,
    timing: dict[int, tuple[float, float]],
    max_units: float,
) -> list[CaptionCue]:
    pieces: list[tuple[str, float, float]] = []
    for start, end in clauses(script):
        excerpt = script[start:end]
        text = single_line(excerpt).strip()
        offset = len(excerpt) - len(excerpt.lstrip())
        actual_start = start + offset
        for part, part_start, part_end in split_display(
            text,
            actual_start,
            max_units,
        ):
            values = [timing[index] for index in range(part_start, part_end) if index in timing]
            if values:
                pieces.append((part, values[0][0], values[-1][1]))

    result: list[CaptionCue] = []
    pending: list[tuple[str, float, float]] = []
    for piece in pieces:
        combined = "".join(item[0] for item in pending) + piece[0]
        start = pending[0][1] if pending else piece[1]
        duration = piece[2] - start
        pending_duration = pending[-1][2] - pending[0][1] if pending else 0.0
        previous_sentence_end = bool(pending) and pending[-1][0].rstrip().endswith(("。", "！", "？", ".", "!", "?"))
        join = (
            bool(pending)
            and not previous_sentence_end
            and visible_units(combined) <= max_units
            and (duration <= 3.6 or (pending_duration < 1.15 and duration <= 4.2))
        )
        if pending and not join:
            result.append(
                CaptionCue(
                    single_line("".join(item[0] for item in pending)),
                    pending[0][1],
                    pending[-1][2],
                )
            )
            pending = []
        pending.append(piece)
    if pending:
        result.append(
            CaptionCue(
                single_line("".join(item[0] for item in pending)),
                pending[0][1],
                pending[-1][2],
            )
        )
    return result


def lock_to_frames(captions: list[CaptionCue], fps: float) -> list[CaptionCue]:
    held: list[CaptionCue] = []
    for index, cue in enumerate(captions):
        next_start = captions[index + 1].start if index + 1 < len(captions) else cue.end + 0.8
        end = min(next_start - 0.04, max(cue.end, cue.start + 0.8))
        if end > cue.start:
            held.append(CaptionCue(cue.text, cue.start, end))
    result: list[CaptionCue] = []
    for index, cue in enumerate(held):
        start = round(cue.start * fps) / fps
        next_start = round(held[index + 1].start * fps) / fps if index + 1 < len(held) else None
        end = round(cue.end * fps) / fps
        if next_start is not None:
            end = min(end, next_start - 1 / fps)
        end = max(end, start + 1 / fps)
        result.append(CaptionCue(cue.text, start, end))
    return result


def srt_time(seconds: float) -> str:
    milliseconds = round(max(0, seconds) * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def ass_time(seconds: float) -> str:
    centiseconds = round(max(0, seconds) * 100)
    hours, centiseconds = divmod(centiseconds, 360_000)
    minutes, centiseconds = divmod(centiseconds, 6_000)
    seconds, centiseconds = divmod(centiseconds, 100)
    return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"


def write_outputs(captions: list[CaptionCue], out_dir: Path, prefix: str, report: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    srt, ass, remotion = [], [], []
    for number, cue in enumerate(captions, start=1):
        srt.extend([str(number), f"{srt_time(cue.start)} --> {srt_time(cue.end)}", cue.text, ""])
        escaped = cue.text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
        ass.append(f"Dialogue: 0,{ass_time(cue.start)},{ass_time(cue.end)},Captions,,0,0,0,,{escaped}")
        remotion.append({"text": cue.text, "startMs": round(cue.start * 1000), "endMs": round(cue.end * 1000)})
    style = report["style"]
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {style["frame_width"]}
PlayResY: {style["frame_height"]}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Captions,PingFang SC Semibold,{style["font_size"]},&H00FFFFFF,&H00000000,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{style["stroke_width"]},0,2,{style["margin_left"]},{style["margin_right"]},{style["margin_bottom"]},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    (out_dir / f"{prefix}.srt").write_text("\n".join(srt), encoding="utf-8")
    (out_dir / f"{prefix}.ass").write_text(header + "\n".join(ass) + "\n", encoding="utf-8")
    (out_dir / f"{prefix}.json").write_text(json.dumps(remotion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / f"{prefix}-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--fps", type=float, default=60)
    parser.add_argument("--prefix", default="captions")
    parser.add_argument("--frame-width", type=int, default=1920)
    parser.add_argument("--frame-height", type=int, default=1080)
    parser.add_argument("--font-size", type=float, default=49)
    parser.add_argument("--min-font-size", type=float, default=36)
    parser.add_argument("--max-width", type=float)
    args = parser.parse_args()
    if args.fps <= 0:
        raise ValueError("--fps must be positive")
    if args.frame_width <= 0 or args.frame_height <= 0:
        raise ValueError("frame dimensions must be positive")
    if args.min_font_size <= 0 or args.font_size < args.min_font_size:
        raise ValueError("font sizes must be positive and --font-size must be >= --min-font-size")
    portrait = args.frame_height > args.frame_width
    reference_height = 1920 if portrait else 1080
    scale = args.frame_height / reference_height
    horizontal_margin = (70 if portrait else 140) * scale
    bottom_margin = 86 * scale
    max_width = (
        args.max_width
        if args.max_width is not None
        else min(
            args.frame_width - 2 * horizontal_margin,
            (940 if portrait else 1540) * scale,
        )
    )
    if max_width <= 0:
        raise ValueError("caption width is not positive")
    max_units = (max_width - 40 * scale) / (args.min_font_size * scale)
    script = approved_script(args.script)
    timeline = json.loads(args.timeline.read_text(encoding="utf-8"))
    timing, exact, filled = timing_map(script, list(timeline.get("words") or []))
    captions = lock_to_frames(raw_captions(script, timing, max_units), args.fps)
    max_lines = max((cue.text.count("\n") + 1 for cue in captions), default=0)
    estimated_font_sizes = [
        min(
            args.font_size,
            (max_width / scale - 40) / max(1, visible_units(cue.text)),
        )
        for cue in captions
    ]
    minimum_estimated_font_size = min(estimated_font_sizes, default=args.font_size)
    frame_errors = [abs(value * args.fps - round(value * args.fps)) for cue in captions for value in (cue.start, cue.end)]
    status = (
        "pass"
        if exact >= 0.94
        and filled >= 0.98
        and max_lines <= 1
        and minimum_estimated_font_size >= args.min_font_size - 0.01
        and max(frame_errors, default=0.0) < 1e-6
        else "needs-review"
    )
    report = {
        "status": status,
        "text_source": "approved script",
        "timing_source": "timeline.json words (Faster-Whisper or approved word timeline)",
        "exact_alignment_coverage": round(exact, 4),
        "timing_coverage_after_interpolation": round(filled, 4),
        "caption_count": len(captions),
        "caption_frame_rate": args.fps,
        "max_frame_error": round(max(frame_errors, default=0.0), 6),
        "max_lines": max_lines,
        "minimum_estimated_font_size": round(minimum_estimated_font_size, 3),
        "minimum_hold_seconds": 0.8,
        "placement": "bottom-center / forced single line / white text / 10px pure-black outline / no shadow or opaque panel",
        "style": {
            "frame_width": args.frame_width,
            "frame_height": args.frame_height,
            "font_size": args.font_size,
            "dynamic_min_font_size": args.min_font_size,
            "font_color": "#FFFFFF",
            "stroke_width": 10,
            "stroke_color": "#000000",
            "shadow": 0,
            "margin_left": round(horizontal_margin, 3),
            "margin_right": round(horizontal_margin, 3),
            "margin_bottom": round(bottom_margin, 3),
            "max_width": round(max_width, 3),
        },
        "captions": [asdict(cue) for cue in captions],
    }
    write_outputs(captions, args.out, args.prefix, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
