#!/usr/bin/env python3
"""Transcribe real audio with Faster-Whisper and preserve word-level timestamps."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from faster_whisper import WhisperModel


def selected_device(value: str) -> str:
    if value != "auto":
        return value
    return "cuda" if shutil.which("nvidia-smi") else "cpu"


def selected_compute_type(device: str, value: str) -> str:
    if value != "auto":
        return value
    return "float16" if device == "cuda" else "int8"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--merge-into", type=Path)
    parser.add_argument("--model", default="large-v3")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--compute-type", default="auto")
    parser.add_argument("--pause-seconds", type=float, default=0.45)
    parser.add_argument("--beam-size", type=int, default=5)
    args = parser.parse_args()
    if bool(args.out) == bool(args.merge_into):
        parser.error("provide exactly one of --out or --merge-into")

    device = selected_device(args.device)
    compute_type = selected_compute_type(device, args.compute_type)
    model = WhisperModel(args.model, device=device, compute_type=compute_type)
    segments, info = model.transcribe(
        str(args.audio), language=args.language, beam_size=args.beam_size,
        word_timestamps=True, vad_filter=True,
    )
    words, segment_records = [], []
    for segment_number, segment in enumerate(segments):
        segment_words = []
        for word_number, word in enumerate(segment.words or []):
            record = {
                "id": f"s{segment_number}-w{word_number}", "text": word.word,
                "start": word.start, "end": word.end, "probability": getattr(word, "probability", None),
            }
            words.append(record)
            segment_words.append(record["id"])
        segment_records.append({"start": segment.start, "end": segment.end, "text": segment.text, "word_ids": segment_words})
    pauses = []
    for previous, current in zip(words, words[1:]):
        gap = current["start"] - previous["end"]
        if gap >= args.pause_seconds:
            pauses.append({"after_word": previous["id"], "before_word": current["id"], "start": previous["end"], "end": current["start"], "duration": gap})

    transcription = {
        "engine": "faster-whisper", "model": args.model, "language": info.language,
        "language_probability": info.language_probability, "device": device, "compute_type": compute_type,
    }
    if args.merge_into:
        payload = json.loads(args.merge_into.read_text())
        payload.update({"audio": str(args.audio.resolve()), "words": words, "pauses": pauses, "segments": segment_records, "transcription": transcription})
        target = args.merge_into
    else:
        payload = {
            "schema_version": "1.1", "audio": str(args.audio.resolve()),
            "words": words, "pauses": pauses, "segments": segment_records,
            "visual_actions": [], "prelude_events": [], "sync_events": [],
            "transcription": transcription,
        }
        target = args.out
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"timeline": str(target), "word_count": len(words), "pause_count": len(pauses), "transcription": transcription}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
