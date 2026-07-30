#!/usr/bin/env python3
"""Regression tests for semantic, settled-state, and transition timing."""

from __future__ import annotations

import copy
import unittest

from audit_action_timing import audit_timeline


def valid_timeline() -> dict:
    actions = []
    events = []
    for index, (label, visible, settled) in enumerate(
        [("读取", 1.0, 1.3), ("搜索", 1.6, 1.9), ("创建", 2.2, 2.5)]
    ):
        action_id = f"step-{index}"
        actions.append(
            {
                "id": action_id,
                "scene_id": "scene-01",
                "label": label,
                "element_type": "card",
                "sync_required": True,
                "sync_event_id": action_id,
                "visible_from": visible,
                "settled_at": settled,
                "min_visible_seconds": 1.0,
                "min_settled_seconds": 1.0,
                "sequence_group_id": "task-flow",
                "sequence_index": index,
            }
        )
        events.append(
            {
                "id": action_id,
                "scene_id": "scene-01",
                "label": label,
                "stage": "semantic",
                "audio_time": visible,
                "visual_time": visible,
            }
        )
    return {
        "schema_version": "1.2",
        "fps": 60,
        "scenes": [
            {
                "id": "scene-01",
                "start": 0.0,
                "end": 5.0,
                "visual_exit_start": 4.0,
            }
        ],
        "visual_actions": actions,
        "sync_events": events,
        "prelude_events": [],
    }


def valid_character_motion_timeline() -> dict:
    phases = [
        ("prepare", 1.0, 1.2, 0.0),
        ("key-action", 2.0, 2.2, 0.0),
        ("outcome", 3.0, 3.2, 1.0),
        ("settled", 3.6, 3.8, 1.0),
    ]
    actions = []
    events = []
    for index, (phase, visible, settled, minimum) in enumerate(phases):
        action_id = f"verify-{phase}"
        actions.append(
            {
                "id": action_id,
                "scene_id": "scene-motion",
                "label": phase,
                "element_type": "character-motion",
                "motion_asset_id": "yolo-verify-source",
                "motion_variant": "verified",
                "motion_phase": phase,
                "facing": "right",
                "occupied_rect_1080p": {
                    "x_min": 80,
                    "x_max": 460,
                    "y_min": 440,
                    "y_max": 820,
                },
                "sync_required": True,
                "sync_event_id": action_id,
                "visible_from": visible,
                "settled_at": settled,
                "min_visible_seconds": 0.0,
                "min_settled_seconds": minimum,
                "sequence_group_id": "verify-source-sequence",
                "sequence_index": index,
            }
        )
        events.append(
            {
                "id": action_id,
                "scene_id": "scene-motion",
                "label": phase,
                "stage": "semantic",
                "audio_time": visible,
                "visual_time": visible,
            }
        )
    return {
        "schema_version": "1.3",
        "fps": 60,
        "scenes": [
            {
                "id": "scene-motion",
                "start": 0.0,
                "end": 6.0,
                "visual_exit_start": 5.0,
            }
        ],
        "visual_actions": actions,
        "sync_events": events,
        "prelude_events": [],
    }


class AuditActionTimingTest(unittest.TestCase):
    def test_complete_sequence_holds_before_exit(self) -> None:
        report = audit_timeline(valid_timeline(), 60, require_manifest=True)
        self.assertEqual(report["status"], "pass")
        sequence = [item for item in report["checks"] if item["kind"] == "sequence-completion"]
        self.assertTrue(sequence)
        self.assertEqual(sequence[-1]["final_action_id"], "step-2")

    def test_transition_rejects_unfinished_hold(self) -> None:
        timeline = valid_timeline()
        timeline["scenes"][0]["visual_exit_start"] = 3.0
        report = audit_timeline(timeline, 60, require_manifest=True)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(
            any(item["kind"] == "settled-hold" and item["status"] == "fail" for item in report["checks"])
        )

    def test_future_state_rejects_early_visibility(self) -> None:
        timeline = valid_timeline()
        timeline["visual_actions"][1]["visible_from"] = 1.2
        report = audit_timeline(timeline, 60, require_manifest=True)
        self.assertTrue(
            any(item["kind"] == "future-state" and item["status"] == "fail" for item in report["checks"])
        )

    def test_sequence_order_rejects_early_final_state(self) -> None:
        timeline = copy.deepcopy(valid_timeline())
        timeline["visual_actions"][1]["settled_at"] = 2.4
        timeline["visual_actions"][2]["settled_at"] = 2.3
        report = audit_timeline(timeline, 60, require_manifest=True)
        self.assertTrue(
            any(item["kind"] == "sequence-completion" and item["status"] == "fail" for item in report["checks"])
        )

    def test_schema_12_requires_exit_and_settle_fields(self) -> None:
        timeline = valid_timeline()
        del timeline["scenes"][0]["visual_exit_start"]
        del timeline["visual_actions"][0]["settled_at"]
        report = audit_timeline(timeline, 60, require_manifest=True)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(item["kind"] == "scene-exit-contract" for item in report["checks"]))
        self.assertTrue(any(item["kind"] == "settle-contract" for item in report["checks"]))

    def test_schema_13_character_motion_contract_passes(self) -> None:
        report = audit_timeline(valid_character_motion_timeline(), 60, require_manifest=True)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(
            any(item["kind"] == "character-motion-sequence" and item["status"] == "pass" for item in report["checks"])
        )

    def test_schema_13_rejects_missing_motion_fields_and_unsafe_rect(self) -> None:
        timeline = valid_character_motion_timeline()
        action = timeline["visual_actions"][0]
        del action["motion_variant"]
        action["occupied_rect_1080p"]["y_max"] = 900
        report = audit_timeline(timeline, 60, require_manifest=True)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(item["kind"] == "character-motion-contract" for item in report["checks"]))
        self.assertTrue(any(item["kind"] == "character-motion-layout" for item in report["checks"]))

    def test_schema_13_rejects_short_result_hold(self) -> None:
        timeline = valid_character_motion_timeline()
        timeline["visual_actions"][2]["min_settled_seconds"] = 0.5
        report = audit_timeline(timeline, 60, require_manifest=True)
        self.assertTrue(
            any(item["kind"] == "character-motion-result-hold" and item["status"] == "fail" for item in report["checks"])
        )

    def test_character_motion_uses_idle_instead_of_prelude(self) -> None:
        timeline = valid_character_motion_timeline()
        timeline["prelude_events"] = [
            {
                "id": "verify-shell",
                "for_event_id": "verify-prepare",
                "scene_id": "scene-motion",
                "visual_time": 0.5,
                "kind": "container",
            }
        ]
        report = audit_timeline(timeline, 60, require_manifest=True)
        self.assertTrue(
            any(item["kind"] == "character-motion-prelude" and item["status"] == "fail" for item in report["checks"])
        )


if __name__ == "__main__":
    unittest.main()
