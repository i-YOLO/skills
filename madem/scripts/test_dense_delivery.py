#!/usr/bin/env python3
"""Regression tests for dense-motion auditing and forced single-line captions."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True)


class DenseMotionAuditTest(unittest.TestCase):
    def write_case(
        self,
        root: Path,
        *,
        static_candidates: list[dict] | None = None,
        collide: bool = False,
        supported: bool = True,
    ) -> tuple[Path, Path, Path]:
        actions = [
            {
                "id": "a1",
                "scene_id": "S01",
                "visible_from": 0.5,
                "settled_at": 0.9 if not collide else 1.8,
                "attention_level": "high",
            },
            {
                "id": "a2",
                "scene_id": "S01",
                "visible_from": 1.7,
                "settled_at": 2.1,
                "attention_level": "high",
            },
            {
                "id": "a3",
                "scene_id": "S01",
                "visible_from": 3.0,
                "settled_at": 3.4,
                "attention_level": "high",
            },
        ]
        timeline = {
            "schema_version": "1.4",
            "fps": 60,
            "scenes": [
                {
                    "id": "S01",
                    "start": 0.0,
                    "end": 4.0 if supported else 8.0,
                    "hold": False,
                    "narration_active": True,
                }
            ],
            "sync_events": [
                {"id": "e1", "scene_id": "S01", "visual_time": 0.5, "stage": "semantic"},
                {"id": "e2", "scene_id": "S01", "visual_time": 1.7, "stage": "semantic"},
                {"id": "e3", "scene_id": "S01", "visual_time": 3.0, "stage": "semantic"},
            ],
            "visual_actions": actions,
            "motion_density": {
                "profile_id": "dense-tech-v1",
                "tracks": (
                    [
                        {
                            "id": "ambient",
                            "scene_id": "S01",
                            "role": "ambient",
                            "start": 0.0,
                            "end": 4.0,
                            "intensity": "low",
                            "loop_period_seconds": 2.0,
                        }
                    ]
                    if supported
                    else []
                ),
            },
        }
        visual = {"static_candidates": static_candidates or []}
        timeline_path = root / "timeline.json"
        visual_path = root / "visual-qc.json"
        report_path = root / "density.json"
        timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
        visual_path.write_text(json.dumps(visual), encoding="utf-8")
        return timeline_path, visual_path, report_path

    def test_dense_motion_passes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            timeline, visual, report = self.write_case(Path(folder))
            result = run(
                [
                    "python3",
                    str(SKILL / "scripts/audit_motion_density.py"),
                    "--timeline",
                    str(timeline),
                    "--visual-qc",
                    str(visual),
                    "--out",
                    str(report),
                ]
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(report.read_text())["status"], "pass")

    def test_static_gap_and_attention_collision_fail(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            timeline, visual, report = self.write_case(
                Path(folder),
                static_candidates=[{"start": 3, "end": 6}],
                collide=True,
                supported=False,
            )
            result = run(
                [
                    "python3",
                    str(SKILL / "scripts/audit_motion_density.py"),
                    "--timeline",
                    str(timeline),
                    "--visual-qc",
                    str(visual),
                    "--out",
                    str(report),
                ]
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(report.read_text())
            self.assertEqual(payload["status"], "fail")
            failed = {check["name"] for check in payload["checks"] if check["status"] == "fail"}
            self.assertIn("unsupported-narration-gaps", failed)
            self.assertIn("primary-attention-collisions", failed)
            self.assertIn("encoded-video-static-candidates", failed)


class SingleLineCaptionTest(unittest.TestCase):
    def test_vertical_and_landscape_outputs_are_single_line(self) -> None:
        script_text = (
            "比如我想做一个文件夹吞噬 APP 图标的动画，"
            "然后自动检查透明背景字幕安全区元素遮挡并重新渲染。"
        )
        spoken = [char for char in script_text if "\u4e00" <= char <= "\u9fff" or char.isascii() and char.isalnum()]
        words = [
            {"text": char, "start": index * 0.09, "end": index * 0.09 + 0.08}
            for index, char in enumerate(spoken)
        ]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "script.md"
            timeline = root / "timeline.json"
            script.write_text(script_text, encoding="utf-8")
            timeline.write_text(json.dumps({"words": words}), encoding="utf-8")
            for width, height in ((1080, 1920), (1920, 1080)):
                out = root / f"{width}x{height}"
                result = run(
                    [
                        "python3",
                        str(SKILL / "scripts/build_captions.py"),
                        "--script",
                        str(script),
                        "--timeline",
                        str(timeline),
                        "--out",
                        str(out),
                        "--frame-width",
                        str(width),
                        "--frame-height",
                        str(height),
                    ]
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                cues = json.loads((out / "captions.json").read_text())
                report = json.loads((out / "captions-report.json").read_text())
                self.assertTrue(cues)
                self.assertTrue(all("\n" not in cue["text"] for cue in cues))
                self.assertEqual(report["max_lines"], 1)
                self.assertGreaterEqual(report["minimum_estimated_font_size"], 36)


class VisualProfileRoutingTest(unittest.TestCase):
    def initialize(self, root: Path, script_text: str) -> tuple[dict, dict]:
        script = root / "script.md"
        project = root / "job"
        script.write_text(script_text, encoding="utf-8")
        result = run(
            [
                "python3",
                str(SKILL / "scripts/init_video_job.py"),
                "--project",
                str(project),
                "--script",
                str(script),
            ]
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        job = json.loads((project / "video-job.json").read_text())
        timeline = json.loads((project / "timeline.json").read_text())
        return job, timeline

    def test_ai_software_topics_route_to_vertical_dense_preset(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            job, timeline = self.initialize(
                Path(folder),
                "用 Codex Agent 自动执行一套软件工作流。",
            )
            self.assertEqual(job["schema_version"], "1.4")
            self.assertEqual(job["delivery"]["width"], 1080)
            self.assertEqual(job["delivery"]["height"], 1920)
            self.assertEqual(
                job["delivery"]["visual_system"]["profile_id"],
                "madem-ai-tech-dark-v1",
            )
            self.assertEqual(
                timeline["motion_density"]["profile_id"],
                "dense-tech-v1",
            )

    def test_non_software_topics_keep_warm_landscape_preset(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            job, timeline = self.initialize(Path(folder), "解释地球上的四季变化。")
            self.assertEqual(job["delivery"]["width"], 1920)
            self.assertEqual(job["delivery"]["height"], 1080)
            self.assertEqual(
                job["delivery"]["visual_system"]["profile_id"],
                "madem-warm-knowledge-v1",
            )
            self.assertIsNone(timeline["motion_density"])


class PatternRoutingTest(unittest.TestCase):
    def test_dense_motion_semantics_route_to_reusable_components(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "script.md"
            out = root / "pattern-plan.json"
            script.write_text(
                "# 标题\n\n"
                "> 状态：制作说明，不是口播。\n\n"
                "用 Codex 做 AI 工作流。\n"
                "十个 APP 图标沿曲线聚合并吞噬到文件夹。\n"
                "检查透明背景、字幕安全区和元素遮挡。\n"
                "发现问题后继续修改并重新渲染。\n",
                encoding="utf-8",
            )
            result = run(
                [
                    "python3",
                    str(SKILL / "scripts/plan_animation_reuse.py"),
                    "--script",
                    str(script),
                    "--out",
                    str(out),
                ]
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            plan = json.loads(out.read_text())
            self.assertTrue(all(not unit["text"].startswith(">") for unit in plan["units"]))
            components = {
                candidate["component"]
                for unit in plan["units"]
                for candidate in unit["candidates"]
            }
            self.assertIn("TechGridSceneShell", components)
            self.assertIn("IconSwarmCollector", components)
            self.assertIn("QualityInspectionLoop", components)


if __name__ == "__main__":
    unittest.main()
