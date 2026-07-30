#!/usr/bin/env python3
"""Audit semantic pacing, supporting motion tracks, and dense-tech visual continuity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DENSE_PROFILE = "dense-tech-v1"
MIN_DENSITY = 0.55
MAX_DENSITY = 0.85
MAX_UNSUPPORTED_GAP = 3.0
LONG_SCENE_SECONDS = 7.0


def overlap(left_start: float, left_end: float, right_start: float, right_end: float) -> float:
    return max(0.0, min(left_end, right_end) - max(left_start, right_start))


def add_check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    status: str,
    detail: str,
    **extra: Any,
) -> None:
    checks.append({"name": name, "status": status, "detail": detail, **extra})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--visual-qc", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    timeline = json.loads(args.timeline.read_text(encoding="utf-8"))
    scenes = list(timeline.get("scenes") or [])
    semantic_events = [
        event
        for event in timeline.get("sync_events") or []
        if event.get("stage", "semantic") == "semantic"
    ]
    visual_actions = list(timeline.get("visual_actions") or [])
    density_block = timeline.get("motion_density") or {}
    profile_id = density_block.get("profile_id")
    tracks = list(density_block.get("tracks") or [])
    strict_profile = profile_id == DENSE_PROFILE
    duration = max(
        [float(scene.get("end") or 0) for scene in scenes]
        + [float(event.get("visual_time") or 0) for event in semantic_events]
        + [0.0]
    )
    semantic_density = len(semantic_events) / duration if duration else 0.0
    checks: list[dict[str, Any]] = []

    density_status = (
        "pass" if MIN_DENSITY <= semantic_density <= MAX_DENSITY else "warning"
    )
    add_check(
        checks,
        name="semantic-action-density",
        status=density_status,
        detail=f"{semantic_density:.3f} semantic events/second; target is {MIN_DENSITY:.2f}-{MAX_DENSITY:.2f}",
        actual=round(semantic_density, 4),
        minimum=MIN_DENSITY,
        maximum=MAX_DENSITY,
    )

    unsupported_gaps: list[dict[str, Any]] = []
    for scene in scenes:
        if scene.get("hold") or not scene.get("narration_active", True):
            continue
        scene_id = scene.get("id")
        start = float(scene.get("start") or 0)
        end = float(scene.get("end") or start)
        anchors = sorted(
            float(event.get("visual_time") or 0)
            for event in semantic_events
            if event.get("scene_id") == scene_id
        )
        boundaries = [start, *anchors, end]
        for left, right in zip(boundaries, boundaries[1:]):
            if right - left <= MAX_UNSUPPORTED_GAP:
                continue
            supporting = [
                track
                for track in tracks
                if track.get("scene_id") == scene_id
                and track.get("role") in {"state", "ambient"}
                and overlap(
                    left,
                    right,
                    float(track.get("start") or 0),
                    float(track.get("end") or 0),
                )
                >= 0.5
            ]
            if not supporting:
                unsupported_gaps.append(
                    {
                        "scene_id": scene_id,
                        "start": left,
                        "end": right,
                        "seconds": round(right - left, 3),
                    }
                )

    visual_qc = None
    static_candidates: list[Any] = []
    if args.visual_qc:
        visual_qc = json.loads(args.visual_qc.read_text(encoding="utf-8"))
        static_candidates = list(visual_qc.get("static_candidates") or [])
    compatibility_covered = (
        not strict_profile and visual_qc is not None and not static_candidates
    )
    gap_status = "pass" if not unsupported_gaps or compatibility_covered else "fail"
    add_check(
        checks,
        name="unsupported-narration-gaps",
        status=gap_status,
        detail=(
            "No unsupported narration gap exceeds 3 seconds."
            if not unsupported_gaps
            else (
                "Legacy timeline lacks motion tracks, but final encoded video has no static candidates."
                if compatibility_covered
                else "Long narration gaps require a state or ambient motion track."
            )
        ),
        gaps=unsupported_gaps,
        compatibility_mode=compatibility_covered,
    )

    high_actions = [
        action
        for action in visual_actions
        if action.get("attention_level") == "high"
        and action.get("visible_from") is not None
        and action.get("settled_at") is not None
    ]
    collisions: list[dict[str, Any]] = []
    for index, left in enumerate(high_actions):
        for right in high_actions[index + 1 :]:
            if left.get("scene_id") != right.get("scene_id"):
                continue
            amount = overlap(
                float(left["visible_from"]),
                float(left["settled_at"]),
                float(right["visible_from"]),
                float(right["settled_at"]),
            )
            if amount > 0.1:
                collisions.append(
                    {
                        "left": left.get("id"),
                        "right": right.get("id"),
                        "overlap_seconds": round(amount, 3),
                    }
                )
    add_check(
        checks,
        name="primary-attention-collisions",
        status="fail" if collisions else "pass",
        detail="At most one high-attention semantic action may be entering at once.",
        collisions=collisions,
    )

    long_scene_failures: list[dict[str, Any]] = []
    for scene in scenes:
        start = float(scene.get("start") or 0)
        end = float(scene.get("end") or start)
        if end - start <= LONG_SCENE_SECONDS or scene.get("hold"):
            continue
        milestones = sum(
            1 for event in semantic_events if event.get("scene_id") == scene.get("id")
        ) + sum(
            1
            for track in tracks
            if track.get("scene_id") == scene.get("id") and track.get("role") == "state"
        )
        if milestones < 3:
            long_scene_failures.append(
                {
                    "scene_id": scene.get("id"),
                    "duration": round(end - start, 3),
                    "milestones": milestones,
                }
            )
    add_check(
        checks,
        name="long-scene-state-milestones",
        status="fail" if long_scene_failures else "pass",
        detail="Scenes longer than 7 seconds require at least three semantic/state milestones.",
        scenes=long_scene_failures,
    )

    loop_warnings = [
        {
            "track_id": track.get("id"),
            "loop_period_seconds": track.get("loop_period_seconds"),
        }
        for track in tracks
        if track.get("role") == "ambient"
        and track.get("loop_period_seconds") is not None
        and not 1.6 <= float(track["loop_period_seconds"]) <= 2.5
    ]
    add_check(
        checks,
        name="ambient-loop-periods",
        status="warning" if loop_warnings else "pass",
        detail="Dense-tech ambient loops should usually repeat every 1.6-2.5 seconds.",
        tracks=loop_warnings,
    )

    add_check(
        checks,
        name="encoded-video-static-candidates",
        status="fail" if static_candidates else ("pass" if visual_qc is not None else "warning"),
        detail=(
            "Final encoded video has no unexplained static candidates."
            if visual_qc is not None and not static_candidates
            else (
                "Final encoded video contains static candidates."
                if static_candidates
                else "No visual-QC report was supplied."
            )
        ),
        candidates=static_candidates,
    )

    failures = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warning"]
    result = {
        "status": "fail" if failures else "pass",
        "profile_id": profile_id or "legacy-unregistered",
        "strict_profile": strict_profile,
        "timeline": str(args.timeline.resolve()),
        "visual_qc": str(args.visual_qc.resolve()) if args.visual_qc else None,
        "metrics": {
            "duration_seconds": round(duration, 3),
            "semantic_event_count": len(semantic_events),
            "semantic_events_per_second": round(semantic_density, 4),
            "motion_track_count": len(tracks),
        },
        "summary": {
            "check_count": len(checks),
            "failure_count": len(failures),
            "warning_count": len(warnings),
        },
        "checks": checks,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
