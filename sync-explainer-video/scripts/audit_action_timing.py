#!/usr/bin/env python3
"""Audit semantic coverage, prelude timing, settled holds, and concept ownership."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SEMANTIC_STAGE = "semantic"
HOLD_DEFAULT_TYPES = {"card", "label", "node", "title", "highlight", "cta", "character-motion"}
ELEMENT_TYPES = HOLD_DEFAULT_TYPES | {"connection"}
PRELUDE_KINDS = {"container", "outline", "muted-label"}
CONCEPT_ROLES = {"owner", "context"}
MOTION_PHASES = {"idle", "prepare", "key-action", "outcome", "settled"}
MOTION_PHASE_ORDER = {"idle": 0, "prepare": 1, "key-action": 2, "outcome": 3, "settled": 4}
MOTION_FACINGS = {"left", "right"}
MOTION_REQUIRED_FIELDS = {
    "motion_asset_id",
    "motion_variant",
    "motion_phase",
    "facing",
    "occupied_rect_1080p",
}
YOLO_SLOTS_1080P = (
    {"x_min": 80, "x_max": 460, "y_min": 440, "y_max": 820},
    {"x_min": 1460, "x_max": 1840, "y_min": 440, "y_max": 820},
)


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
    strict_motion_contract = schema_at_least(timeline.get("schema_version"), (1, 3))
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
            if action.get("element_type") == "character-motion" and strict_motion_contract:
                missing = sorted(field for field in MOTION_REQUIRED_FIELDS if field not in action)
                if missing:
                    checks.append({
                        "kind": "character-motion-contract",
                        "status": "fail",
                        "action_id": action_id,
                        "detail": f"schema 1.3 character-motion requires {', '.join(missing)}",
                    })
                if not isinstance(action.get("motion_asset_id"), str) or not action.get("motion_asset_id", "").strip():
                    checks.append({"kind": "character-motion-contract", "status": "fail", "action_id": action_id, "detail": "motion_asset_id must be a non-empty string"})
                if not isinstance(action.get("motion_variant"), str) or not action.get("motion_variant", "").strip():
                    checks.append({"kind": "character-motion-contract", "status": "fail", "action_id": action_id, "detail": "motion_variant must be a non-empty string"})
                phase = action.get("motion_phase")
                if phase not in MOTION_PHASES:
                    checks.append({"kind": "character-motion-phase", "status": "fail", "action_id": action_id, "detail": f"motion_phase must be one of {sorted(MOTION_PHASES)}"})
                elif phase == "idle" and action.get("sync_required"):
                    checks.append({"kind": "character-motion-phase", "status": "fail", "action_id": action_id, "detail": "idle character presence must be non-synchronous"})
                elif phase != "idle" and not action.get("sync_required"):
                    checks.append({"kind": "character-motion-phase", "status": "fail", "action_id": action_id, "detail": "prepare, key-action, outcome, and settled phases require a real word sync event"})
                if action.get("facing") not in MOTION_FACINGS:
                    checks.append({"kind": "character-motion-facing", "status": "fail", "action_id": action_id, "detail": f"facing must be one of {sorted(MOTION_FACINGS)}"})
                rect = action.get("occupied_rect_1080p")
                if not isinstance(rect, dict) or any(field not in rect for field in ("x_min", "x_max", "y_min", "y_max")):
                    checks.append({"kind": "character-motion-layout", "status": "fail", "action_id": action_id, "detail": "occupied_rect_1080p must contain x_min, x_max, y_min, and y_max"})
                else:
                    try:
                        numeric_rect = {field: float(rect[field]) for field in ("x_min", "x_max", "y_min", "y_max")}
                    except (TypeError, ValueError):
                        checks.append({"kind": "character-motion-layout", "status": "fail", "action_id": action_id, "detail": "occupied_rect_1080p values must be numeric"})
                    else:
                        has_area = (
                            numeric_rect["x_min"] < numeric_rect["x_max"]
                            and numeric_rect["y_min"] < numeric_rect["y_max"]
                        )
                        fits_slot = any(
                            numeric_rect["x_min"] >= slot["x_min"]
                            and numeric_rect["x_max"] <= slot["x_max"]
                            and numeric_rect["y_min"] >= slot["y_min"]
                            and numeric_rect["y_max"] <= slot["y_max"]
                            for slot in YOLO_SLOTS_1080P
                        )
                        if not has_area or not fits_slot:
                            checks.append({
                                "kind": "character-motion-layout",
                                "status": "fail",
                                "action_id": action_id,
                                "detail": "character motion must stay inside a reserved lower-left or lower-right slot and end at or before y=820",
                            })
                if phase in {"outcome", "settled"}:
                    try:
                        result_hold = float(action.get("min_settled_seconds", 0))
                    except (TypeError, ValueError):
                        result_hold = 0
                    if result_hold < 1.0:
                        checks.append({
                            "kind": "character-motion-result-hold",
                            "status": "fail",
                            "action_id": action_id,
                            "minimum_seconds": 1.0,
                            "detail": "outcome and settled character frames must hold for at least 1 second",
                        })
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
        target_action = action_by_event.get(target_id)
        if target_action and target_action.get("element_type") == "character-motion":
            checks.append({
                "kind": "character-motion-prelude",
                "status": "fail",
                "prelude_id": prelude.get("id"),
                "action_id": target_action.get("id"),
                "detail": "early static character presence must be a non-synchronous idle action, not a prelude",
            })
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

            motion_group = [
                item
                for item in ordered_group
                if item.get("element_type") == "character-motion"
            ]
            if motion_group:
                phases = [item.get("motion_phase") for item in motion_group]
                valid_phases = all(phase in MOTION_PHASE_ORDER for phase in phases)
                phase_indexes = [MOTION_PHASE_ORDER[phase] for phase in phases] if valid_phases else []
                if not valid_phases or phase_indexes != sorted(phase_indexes):
                    checks.append({
                        "kind": "character-motion-sequence",
                        "status": "fail",
                        "sequence_group_id": group_id,
                        "phases": phases,
                        "detail": "character motion phases must progress from prepare to key-action to outcome to settled",
                    })
                elif "outcome" not in phases or "settled" not in phases:
                    checks.append({
                        "kind": "character-motion-sequence",
                        "status": "fail",
                        "sequence_group_id": group_id,
                        "phases": phases,
                        "detail": "synchronous character motion sequences require outcome and settled phases",
                    })
                else:
                    checks.append({
                        "kind": "character-motion-sequence",
                        "status": "pass",
                        "sequence_group_id": group_id,
                        "phases": phases,
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
