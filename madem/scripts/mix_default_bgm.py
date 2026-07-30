#!/usr/bin/env python3
"""Mix the approved MADEM background track under a captioned voiceover video."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
PROFILE_PATH = SKILL_DIR / "assets" / "audio" / "default-bgm-profile.json"


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=capture)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict[str, Any]:
    result = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], capture=True)
    raw = json.loads(result.stdout)
    audio = next((item for item in raw["streams"] if item.get("codec_type") == "audio"), None)
    video = next((item for item in raw["streams"] if item.get("codec_type") == "video"), None)
    return {
        "format_duration": float(raw["format"].get("duration") or 0),
        "audio": None if not audio else {
            "duration": float(audio.get("duration") or raw["format"].get("duration") or 0),
            "codec": audio.get("codec_name"),
            "sample_rate": int(audio.get("sample_rate") or 0),
            "channels": int(audio.get("channels") or 0),
        },
        "video": None if not video else {"codec": video.get("codec_name")},
    }


def stream_md5(path: Path, stream: str) -> str:
    result = run(["ffmpeg", "-v", "error", "-i", str(path), "-map", stream, "-c", "copy", "-f", "md5", "-"], capture=True)
    return result.stdout.strip().split("=", 1)[1]


def loop_count(track_seconds: float, target_seconds: float, crossfade_seconds: float) -> int:
    if track_seconds <= crossfade_seconds:
        raise ValueError("background track must be longer than the loop crossfade")
    count = 1
    while count * track_seconds - (count - 1) * crossfade_seconds < target_seconds:
        count += 1
    return count


def audio_filter(profile: dict[str, Any], loops: int, track_seconds: float, target_seconds: float) -> str:
    crossfade = float(profile["loop_crossfade_seconds"])
    parts = [f"[{index + 1}:a]atrim=0:{track_seconds:.6f},asetpts=N/SR/TB[m{index}]" for index in range(loops)]
    current = "m0"
    for index in range(1, loops):
        next_label = f"loop{index}"
        parts.append(f"[{current}][m{index}]acrossfade=d={crossfade}:c1=qsin:c2=qsin[{next_label}]")
        current = next_label
    fade_in = min(float(profile["fade_in_seconds"]), target_seconds)
    fade_out = min(float(profile["fade_out_seconds"]), target_seconds)
    fade_out_start = max(0.0, target_seconds - fade_out)
    sidechain = profile["sidechain"]
    parts.extend([
        f"[{current}]atrim=duration={target_seconds:.6f},afade=t=in:st=0:d={fade_in:.6f},afade=t=out:st={fade_out_start:.6f}:d={fade_out:.6f},volume={float(profile['base_volume']):.6f}[bgm_base]",
        "[0:a]asplit=2[voice][voice_key]",
        f"[bgm_base][voice_key]sidechaincompress=threshold={float(sidechain['threshold']):.6f}:ratio={float(sidechain['ratio']):.6f}:attack={int(sidechain['attack_ms'])}:release={int(sidechain['release_ms'])}:makeup={float(sidechain['makeup']):.6f}[bgm_ducked]",
        f"[voice][bgm_ducked]amix=inputs=2:duration=first:normalize=0,alimiter=limit={float(profile['limiter']):.6f}[mixed_raw]",
        f"[mixed_raw]apad=pad_len=2048,atrim=duration={target_seconds:.6f}[mixed]",
    ])
    return ";".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path, help="Captioned video containing the original voiceover audio")
    parser.add_argument("--project", required=True, type=Path, help="Project directory; the selected track is copied below public/audio")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--music", type=Path, help="Custom music only when explicitly approved")
    parser.add_argument("--allow-custom-music", action="store_true")
    args = parser.parse_args()

    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    default_asset = PROFILE_PATH.parent / profile["asset"]
    music = args.music.resolve() if args.music else default_asset
    if args.music and not args.allow_custom_music:
        raise ValueError("custom music requires --allow-custom-music after explicit user approval")
    if not music.is_file():
        raise FileNotFoundError(f"music not found: {music}")
    music_hash = sha256(music)
    if not args.music and music_hash != profile["sha256"]:
        raise ValueError("default BGM fingerprint mismatch; do not mix an unverified replacement")

    source = args.video.resolve()
    source_info = probe(source)
    if not source_info["video"] or not source_info["audio"]:
        raise ValueError("--video must contain both captioned video and the original voiceover audio")
    target_seconds = float(source_info["audio"]["duration"])
    if target_seconds <= 0:
        raise ValueError("voiceover audio duration is invalid")
    track_seconds = float(probe(music)["format_duration"])
    loops = loop_count(track_seconds, target_seconds, float(profile["loop_crossfade_seconds"]))

    project_audio = args.project.resolve() / "public" / "audio"
    project_audio.mkdir(parents=True, exist_ok=True)
    copied_music = project_audio / music.name
    if music.resolve() != copied_music.resolve():
        shutil.copy2(music, copied_music)
    if sha256(copied_music) != music_hash:
        raise RuntimeError("copied BGM fingerprint mismatch")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-y", "-i", str(source)]
    for _ in range(loops):
        command.extend(["-i", str(copied_music)])
    command.extend([
        "-filter_complex", audio_filter(profile, loops, track_seconds, target_seconds),
        "-map", "0:v:0", "-map", "[mixed]", "-c:v", "copy",
        "-c:a", profile["output_audio"]["codec"], "-b:a", profile["output_audio"]["bitrate"],
        "-ar", str(profile["output_audio"]["sample_rate"]), "-ac", str(profile["output_audio"]["channels"]),
        "-movflags", "+faststart", "-metadata", f"title={profile['title']}",
        "-metadata", "comment=MADEM default BGM profile mixed under original voiceover.", str(args.out),
    ])
    run(command)
    run(["ffmpeg", "-v", "error", "-xerror", "-i", str(args.out), "-f", "null", "-"])

    output_info = probe(args.out)
    output_audio = output_info["audio"]
    if not output_audio:
        raise RuntimeError("mixed output has no audio stream")
    expected = profile["output_audio"]
    if output_audio["codec"] != expected["codec"] or output_audio["sample_rate"] != expected["sample_rate"] or output_audio["channels"] != expected["channels"]:
        raise RuntimeError("mixed output audio specification does not match the default profile")
    source_md5 = stream_md5(source, "0:v:0")
    output_md5 = stream_md5(args.out, "0:v:0")
    if source_md5 != output_md5:
        raise RuntimeError("BGM mixing changed the encoded video stream")
    duration_error = abs(float(output_info["format_duration"]) - target_seconds)
    duration_tolerance = max(0.001, 1 / expected["sample_rate"] + 1e-6)
    if duration_error > duration_tolerance:
        raise RuntimeError("mixed output duration does not match the original voiceover duration")

    report = {
        "status": "pass",
        "profile_id": profile["id"] if not args.music else "custom-user-approved",
        "source_video": str(source),
        "output_video": str(args.out.resolve()),
        "source_video_stream_md5": source_md5,
        "output_video_stream_md5": output_md5,
        "voiceover_duration_seconds": target_seconds,
        "output_duration_seconds": output_info["format_duration"],
        "duration_error_seconds": duration_error,
        "duration_tolerance_seconds": duration_tolerance,
        "duration_note": "MP4/AAC timestamps may round to millisecond container precision.",
        "music": {"path": str(copied_music), "sha256": music_hash, "duration_seconds": track_seconds, "loop_count": loops},
        "mix": {key: profile[key] for key in ("base_volume", "base_gain_db", "fade_in_seconds", "fade_out_seconds", "loop_crossfade_seconds", "sidechain", "limiter")},
        "output_audio": output_audio,
        "checks": {
            "decode": True,
            "video_stream_unchanged": source_md5 == output_md5,
            "audio_codec": output_audio["codec"] == expected["codec"],
            "audio_sample_rate": output_audio["sample_rate"] == expected["sample_rate"],
            "audio_channels": output_audio["channels"] == expected["channels"],
            "duration_within_container_timebase": duration_error <= duration_tolerance,
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
