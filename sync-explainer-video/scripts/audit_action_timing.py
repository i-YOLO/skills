#!/usr/bin/env python3
"""Audit semantic coverage, prelude timing, settled holds, and concept ownership."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SEMANTIC_STAGE = "semantic"
HOLD_DEFAULT_TYPES = {"card", "label", "node", "title", "highlight", "cta"}
ELEMENT_TYPES = HOLD_DEFAULT_TYPES | {"connection"}
PRELUDE_KINDS = {"container", "outline", "muted-label"}
CONCEPT_ROLES = {"owner", "context"}


def schema_at_least(value: Any, minimum: tuple[int, int]) -> bool:
    try:
        major, minor = (int(part) for part in str(value).split(".", maxsplit=1))
    except (TypeError, ValueError):
        return False
    return (major, minor) >= minimum


def severity_status(checks: list[dict[str, Any]], *, needs_evidence: bool = False) -> str:
    statuses = {item["status"] for item in checks}
    if "fail" in statuses:
        return "fail"
    if needs_evidence:
        return "needs-evidence"
    if "warning" in statuses:
        return "warning"
    return "pass"


def audit_timeline(
    timeline: dict[str, Any],
    fps: float,
    *,
    max_prelude_seconds: float = 0.75,
    default_min_hold_seconds: float = 1.0,
    require_manifest: bool = False,
) -> dict[str, Any]:
    """Return a machine-readable audit without writing files."""
    checks: list[dict[str, Any]] = []
    scenes = {scene.get("id"): scene for scene in timeline.get("scenes", []) if scene.get("id")}
    all_events = timeline.get("sync_events", [])
    semantic_events = [event for event in all_events if event.get("stage", SEMANTIC_STAGE) == SEMANTIC_STAGE]
    event_by_id: dict[str, dict[str, Any]] = {}
    for event in semantic_events:
        event_id = event.get("id")
        if not event_id:
            checks.append({"kind": "semantic-event-id", "status": "fail", "detail": "sync_events semantic entry is missing id"})
        elif event_id in event_by_id:
            checks.append({"kind": "semantic-event-id", "status": "fail", "event_id": event_id, "detail": "duplicate semantic event id"})
        else:
            event_by_id[event_id] = event

    visual_actions = timeline.get("visual_actions")
    manifest_mode = "explicit" if isinstance(visual_actions, list) else "legacy-sync-events"
    strict_settle_contract = require_manifest and schema_at_least(timeline.get("schema_version"), (1, 2))
    if manifest_mode == "explicit":
        actions = visual_actions
    else:
        actions = [
            {
                "id": event.get("id"),
                "scene_id": event.get("scene_id"),
                "label": event.get("label"),
                "sync_required": True,
                "sync_event_id": event.get("id"),
            }
            for event in semantic_events
        ]
        if require_manifest:
            checks.append({"kind": "action-manifest", "status": "fail", "detail": "visual_actions is required for new word-timed work"})

    action_ids = Counter()
    required_actions = []
    action_by_event: dict[str, dict[str, Any]] = {}
    for action in actions:
        action_id = action.get("id")
        if not action_id:
            checks.append({"kind": "action-id", "status": "fail", "detail": "visual_actions entry is missing id"})
            continue
        action_ids[action_id] += 1
        scene_id = action.get("scene_id")
        if scene_id not in scenes:
            checks.append({"kind": "action-scene", "status": "fail", "action_id": action_id, "scene_id": scene_id, "detail": "unknown scene"})
        if manifest_mode == "explicit":
            if action.get("element_type") not in ELEMENT_TYPES:
                checks.append({"kind": "action-type", "status": "fail", "action_id": action_id, "detail": f"element_type must be one of {sorted(ELEMENT_TYPES)}"})
            if "sync_required" not in action:
                checks.append({"kind": "action-sync-required", "status": "fail", "action_id": action_id, "detail": "visual action must state sync_required"})
            if action.get("concept_id") and action.get("concept_role") not in CONCEPT_ROLES:
                checks.append({"kind": "concept-role", "status": "fail", "action_id": action_id, "detail": f"concept_role must be one of {sorted(CONCEPT_ROLES)}"})
            if strict_settle_contract:
                for field in ("visible_from", "settled_at", "min_settled_seconds"):
                    if field not in action:
                        checks.append({"kind": "settle-contract", "status": "fail", "action_id": action_id, "detail": f"schema 1.2 action requires {field}"})
        if action.get("sync_required", False):
            required_actions.append(action)
            event_id = action.get("sync_event_id", action_id)
            event = event_by_id.get(event_id)
            if not event:
                checks.append({"kind": "action-coverage", "status": "fail", "action_id": action_id, "event_id": event_id, "detail": "sync-required action has no semantic sync event"})
                continue
            action_by_event[event_id] = action
            if scene_id and event.get("scene_id") and scene_id != event.get("scene_id"):
                checks.append({"kind": "action-scene", "status": "fail", "action_id": action_id, "event_id": event_id, "detail": "action and sync event belong to different scenes"})
            try:
                error = abs(float(event["visual_time"]) - float(event["audio_time"])) * fps
            except (KeyError, TypeError, ValueError):
                checks.append({"kind": "semantic-time", "status": "fail", "event_id": event_id, "detail": "semantic event needs numeric audio_time and visual_time"})
                continue
            state = "pass" if error <= 0.5 else ("warning" if error <= 1 else "fail")
            checks.append({"kind": "semantic-time", "status": state, "event_id": event_id, "error_frames": error})
            if action.get("visible_from") is not None:
                try:
                    visible_from = float(action["visible_from"])
                except (TypeError, ValueError):
                    checks.append({"kind": "future-state", "status": "fail", "action_id": action_id, "detail": "visible_from must be numeric"})
                else:
                    if visible_from < float(event["visual_time"]):
                        checks.append({
                            "kind": "future-state",
                            "status": "fail",
                            "action_id": action_id,
                            "visible_from": visible_from,
                            "semantic_time": float(event["visual_time"]),
                            "detail": "semantic element becomes visible before its spoken event",
                        })

    for action_id, count in action_ids.items():
        if count > 1:
            checks.append({"kind": "action-id", "status": "fail", "action_id": action_id, "detail": "duplicate visual action id"})

    # Optional ordering is explicit: only check a declared sequence, never list order.
    ordered = [action for action in required_actions if action.get("order") is not None]
    for previous, current in zip(sorted(ordered, key=lambda item: item["order"]), sorted(ordered, key=lambda item: item["order"])[1:]):
        previous_event = event_by_id.get(previous.get("sync_event_id", previous["id"]))
        current_event = event_by_id.get(current.get("sync_event_id", current["id"]))
        if previous_event and current_event and float(previous_event["audio_time"]) > float(current_event["audio_time"]):
            checks.append({"kind": "semantic-order", "status": "fail", "previous": previous["id"], "current": current["id"], "detail": "declared action order contradicts spoken order"})

    preludes = timeline.get("prelude_events", [])
    prelude_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prelude in preludes:
        target_id = prelude.get("for_event_id")
        target = event_by_id.get(target_id)
        if not target:
            checks.append({"kind": "prelude-target", "status": "fail", "prelude_id": prelude.get("id"), "target_id": target_id, "detail": "prelude must reference a semantic sync event"})
            continue
        kind = prelude.get("kind")
        if kind not in PRELUDE_KINDS:
            checks.append({"kind": "prelude-kind", "status": "fail", "prelude_id": prelude.get("id"), "detail": f"kind must be one of {sorted(PRELUDE_KINDS)}"})
        try:
            lead = float(target["audio_time"]) - float(prelude["visual_time"])
        except (KeyError, TypeError, ValueError):
            checks.append({"kind": "prelude-time", "status": "fail", "prelude_id": prelude.get("id"), "detail": "prelude needs numeric visual_time"})
            continue
        state = "pass" if 0 < lead <= max_prelude_seconds else "fail"
        checks.append({"kind": "prelude-time", "status": state, "prelude_id": prelude.get("id"), "target_id": target_id, "lead_seconds": lead, "max_prelude_seconds": max_prelude_seconds})
        if prelude.get("scene_id") and target.get("scene_id") and prelude["scene_id"] != target["scene_id"]:
            checks.append({"kind": "prelude-scene", "status": "fail", "prelude_id": prelude.get("id"), "detail": "prelude and target must be in the same scene"})
        prelude_by_target[target_id].append(prelude)

    if manifest_mode == "explicit":
        for scene_id, scene in scenes.items():
            if strict_settle_contract and "visual_exit_start" not in scene:
                checks.append({"kind": "scene-exit-contract", "status": "fail", "scene_id": scene_id, "detail": "schema 1.2 scene requires visual_exit_start"})
                continue
            if "visual_exit_start" in scene:
                try:
                    exit_start = float(scene["visual_exit_start"])
                    scene_start = float(scene["start"])
                    scene_end = float(scene["end"])
                except (KeyError, TypeError, ValueError):
                    checks.append({"kind": "scene-exit-contract", "status": "fail", "scene_id": scene_id, "detail": "scene start/end/visual_exit_start must be numeric"})
                else:
                    if not scene_start <= exit_start <= scene_end:
                        checks.append({"kind": "scene-exit-contract", "status": "fail", "scene_id": scene_id, "detail": "visual_exit_start must fall inside the scene"})

        for action in required_actions:
            event_id = action.get("sync_event_id", action.get("id"))
            event = event_by_id.get(event_id)
            scene = scenes.get(action.get("scene_id"))
            if not event or not scene:
                continue
            default_hold = default_min_hold_seconds if action.get("element_type") in HOLD_DEFAULT_TYPES else 0.0
            min_hold = float(action.get("min_visible_seconds", default_hold))
            if min_hold <= 0:
                continue
            end = float(action.get("visible_until", scene["end"]))
            if end > float(scene["end"]) or end < float(event["visual_time"]):
                checks.append({"kind": "visible-range", "status": "fail", "action_id": action.get("id"), "detail": "visible_until must fall between the semantic action and its scene end"})
                continue
            semantic_visible = end - float(event["visual_time"])
            prelude_visible = max((end - float(item["visual_time"]) for item in prelude_by_target.get(event_id, [])), default=0.0)
            if semantic_visible < min_hold and prelude_visible < min_hold:
                checks.append({"kind": "flash-risk", "status": "fail", "action_id": action.get("id"), "semantic_visible_seconds": semantic_visible, "prelude_visible_seconds": prelude_visible, "minimum_seconds": min_hold, "detail": "move the scene boundary, extend the action, or add a compliant prelude"})

        sequence_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for action in actions:
            action_id = action.get("id")
            scene = scenes.get(action.get("scene_id"))
            if not action_id or not scene or action.get("settled_at") is None:
                continue
            try:
                settled_at = float(action["settled_at"])
                visible_from = float(action.get("visible_from", scene["start"]))
                exit_start = float(scene.get("visual_exit_start", scene["end"]))
                min_settled = float(action.get("min_settled_seconds", default_min_hold_seconds))
            except (KeyError, TypeError, ValueError):
                checks.append({"kind": "settle-contract", "status": "fail", "action_id": action_id, "detail": "settled timing fields must be numeric"})
                continue
            if min_settled < 0:
                checks.append({"kind": "settle-contract", "status": "fail", "action_id": action_id, "detail": "min_settled_seconds cannot be negative"})
                continue
            if not float(scene["start"]) <= visible_from <= settled_at <= float(scene["end"]):
                checks.append({"kind": "settle-contract", "status": "fail", "action_id": action_id, "detail": "expected scene.start <= visible_from <= settled_at <= scene.end"})
                continue
            settled_hold = exit_start - settled_at
            status = "pass" if settled_hold >= min_settled else "fail"
            checks.append({
                "kind": "settled-hold",
                "status": status,
                "action_id": action_id,
                "settled_at": settled_at,
                "visual_exit_start": exit_start,
                "settled_hold_seconds": settled_hold,
                "minimum_seconds": min_settled,
                "detail": None if status == "pass" else "animation is not fully settled long enough before visual exit",
            })
            group_id = action.get("sequence_group_id")
            if group_id is not None:
                sequence_groups[str(group_id)].append(action)

        for group_id, group in sequence_groups.items():
            try:
                ordered_group = sorted(group, key=lambda item: float(item["sequence_index"]))
                indexes = [float(item["sequence_index"]) for item in ordered_group]
                settled_times = [float(item["settled_at"]) for item in ordered_group]
            except (KeyError, TypeError, ValueError):
                checks.append({"kind": "sequence-completion", "status": "fail", "sequence_group_id": group_id, "detail": "sequence actions require numeric sequence_index and settled_at"})
                continue
            if len(indexes) != len(set(indexes)):
                checks.append({"kind": "sequence-completion", "status": "fail", "sequence_group_id": group_id, "detail": "sequence_index values must be unique"})
            if settled_times != sorted(settled_times):
                checks.append({"kind": "sequence-completion", "status": "fail", "sequence_group_id": group_id, "detail": "settled_at must follow sequence_index order"})
            final_action = ordered_group[-1]
            final_scene = scenes.get(final_action.get("scene_id"))
            if final_scene:
                final_hold = float(final_scene.get("visual_exit_start", final_scene["end"])) - float(final_action["settled_at"])
                minimum = float(final_action.get("min_settled_seconds", default_min_hold_seconds))
                checks.append({
                    "kind": "sequence-completion",
                    "status": "pass" if final_hold >= minimum else "fail",
                    "sequence_group_id": group_id,
                    "final_action_id": final_action.get("id"),
                    "final_settled_at": float(final_action["settled_at"]),
                    "settled_hold_seconds": final_hold,
                    "minimum_seconds": minimum,
                })

        concepts: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for action in actions:
            concept = action.get("concept_id")
            if concept:
                concepts[concept].append(action)
        for concept, claimed in concepts.items():
            owners = [item for item in claimed if item.get("concept_role") == "owner"]
            if len(owners) != 1:
                checks.append({"kind": "concept-ownership", "status": "fail", "concept_id": concept, "owners": [item.get("id") for item in owners], "detail": "a registered concept must have exactly one owner action/scene"})

    coverage = {
        "registered_actions": len(actions),
        "sync_required_actions": len(required_actions),
        "semantic_events": len(semantic_events),
        "covered_actions": sum(1 for action in required_actions if action.get("sync_event_id", action.get("id")) in event_by_id),
        "prelude_events": len(preludes),
    }
    needs_evidence = not semantic_events or (manifest_mode == "explicit" and not required_actions)
    return {
        "status": severity_status(checks, needs_evidence=needs_evidence),
        "fps": fps,
        "manifest_mode": manifest_mode,
        "compatibility_note": "legacy sync_events used as implicit action manifest" if manifest_mode == "legacy-sync-events" else None,
        "coverage": coverage,
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--max-prelude-seconds", type=float, default=0.75)
    parser.add_argument("--default-min-hold-seconds", type=float, default=1.0)
    parser.add_argument("--require-manifest", action="store_true")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    timeline = json.loads(args.timeline.read_text())
    report = audit_timeline(
        timeline,
        args.fps or float(timeline.get("fps", 60)),
        max_prelude_seconds=args.max_prelude_seconds,
        default_min_hold_seconds=args.default_min_hold_seconds,
        require_manifest=args.require_manifest,
    )
    report["timeline"] = str(args.timeline.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
