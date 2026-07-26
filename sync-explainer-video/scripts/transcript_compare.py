#!/usr/bin/env python3
"""Compare the real ASR text with a supplied script and flag candidates for review."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path


def normalized(text: str) -> str:
    return re.sub(r"[\W_]", "", text, flags=re.UNICODE).casefold()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    timeline = json.loads(args.timeline.read_text())
    words = timeline.get("words", [])
    observed = "".join(item.get("text", "") for item in words)
    expected = args.script.read_text()
    observed_clean, expected_clean = normalized(observed), normalized(expected)
    matcher = difflib.SequenceMatcher(a=expected_clean, b=observed_clean, autojunk=False)
    differences = [
        {"kind": tag, "script": expected_clean[i1:i2], "spoken": observed_clean[j1:j2]}
        for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"
    ]
    repeats = []
    for previous, current in zip(words, words[1:]):
        if normalized(previous.get("text", "")) and normalized(previous.get("text", "")) == normalized(current.get("text", "")):
            repeats.append({"first": previous, "second": current, "reason": "adjacent repeated ASR token; confirm by listening"})
    report = {
        "script": str(args.script.resolve()), "timeline": str(args.timeline.resolve()),
        "observed_text": observed, "differences": differences, "possible_repeats": repeats,
        "note": "ASR differences are candidates only. Confirm pauses, repeats, misreads, and unspoken text against the audio before editing.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
