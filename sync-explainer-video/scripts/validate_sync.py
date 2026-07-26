#!/usr/bin/env python3
"""Validate strict semantic anchors and action-manifest evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_action_timing import audit_timeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--require-manifest", action="store_true")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    timeline = json.loads(args.timeline.read_text())
    fps = args.fps or float(timeline.get("fps", 60))
    events = []
    for event in timeline.get("sync_events", []):
        if event.get("stage", "semantic") != "semantic":
            continue
        error = abs(float(event["visual_time"]) - float(event["audio_time"])) * fps
        events.append({**event, "error_frames": error})
    if not events:
        status, maximum = "needs-evidence", None
    else:
        maximum = max(event["error_frames"] for event in events)
        status = "pass" if maximum <= 0.5 else ("warning" if maximum <= 1 else "fail")
    action_audit = audit_timeline(timeline, fps, require_manifest=args.require_manifest)
    if action_audit["status"] == "fail":
        status = "fail"
    elif action_audit["status"] == "needs-evidence":
        status = "needs-evidence"
    elif status == "pass" and action_audit["status"] == "warning":
        status = "warning"
    report = {
        "status": status,
        "fps": fps,
        "max_error_frames": maximum,
        "events": events,
        "action_audit": action_audit,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
