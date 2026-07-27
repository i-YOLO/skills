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


if __name__ == "__main__":
    unittest.main()
