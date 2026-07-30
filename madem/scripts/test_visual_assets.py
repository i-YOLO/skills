#!/usr/bin/env python3
"""Validate approved visual assets and source-level rendering contracts."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from PIL import Image


SKILL = Path(__file__).resolve().parents[1]


class VisualAssetContractTest(unittest.TestCase):
    def test_solid_background(self) -> None:
        with Image.open(SKILL / "assets/design-system/cream-FAF8F3-1920x1080.png") as source:
            image = source.convert("RGB")
            self.assertEqual(image.size, (1920, 1080))
            self.assertEqual(image.getextrema(), ((250, 250), (248, 248), (243, 243)))

    def test_product_icons_are_normalized_transparent_assets(self) -> None:
        catalog = json.loads((SKILL / "assets/product-icons/catalog.json").read_text())
        self.assertEqual(len(catalog["assets"]), 4)
        for asset in catalog["assets"]:
            path = SKILL / "assets/product-icons" / asset["file"]
            with Image.open(path) as image:
                self.assertEqual(image.size, (220, 220))
                self.assertEqual(image.mode, "RGBA")
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), asset["sha256"])

    def test_product_icons_v2_are_hash_locked_high_resolution_or_svg(self) -> None:
        root = SKILL / "assets/product-icons/v2"
        catalog = json.loads((root / "catalog.json").read_text())
        self.assertEqual(catalog["status"], "project-proven")
        self.assertEqual(len(catalog["assets"]), 10)
        self.assertEqual(
            {asset["asset_id"] for asset in catalog["assets"]},
            {
                "chatgpt",
                "claude",
                "gemini",
                "manus",
                "perplexity",
                "coze",
                "grok",
                "deepseek",
                "yuanbao",
                "kimi",
            },
        )
        self.assertTrue(
            all(asset["status"] == "project-proven" for asset in catalog["assets"])
        )
        for asset in catalog["assets"]:
            source = root / asset["source_file"]
            canonical = root / asset["canonical_file"]
            self.assertTrue(source.is_file())
            self.assertTrue(canonical.is_file())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), asset["source_sha256"])
            self.assertEqual(hashlib.sha256(canonical.read_bytes()).hexdigest(), asset["sha256"])
            self.assertTrue(asset["official_domain"])
            if canonical.suffix == ".png":
                with Image.open(canonical) as image:
                    self.assertEqual(image.size, (1024, 1024))
                    self.assertEqual(image.mode, "RGBA")
                    alpha = image.getchannel("A")
                    self.assertEqual(
                        [
                            alpha.getpixel((0, 0)),
                            alpha.getpixel((1023, 0)),
                            alpha.getpixel((0, 1023)),
                            alpha.getpixel((1023, 1023)),
                        ],
                        [0, 0, 0, 0],
                    )
                    self.assertEqual(list(alpha.getbbox() or (0, 0, 0, 0)), asset["alpha_bbox"])
            else:
                self.assertIn("<svg", canonical.read_text(encoding="utf-8")[:1000].lower())
        source = (root / "ProductIcon.tsx").read_text()
        self.assertIn("assetId: ProductIconId", source)
        self.assertNotIn("index:", source)
        grok = next(asset for asset in catalog["assets"] if asset["asset_id"] == "grok")
        self.assertIn("boundary-connected", grok["exterior_cleanup"])
        for locked in ("gemini", "coze"):
            asset = next(item for item in catalog["assets"] if item["asset_id"] == locked)
            self.assertTrue(asset["preserve_original_shape"])
        validation = catalog["validation"]
        self.assertEqual(
            validation["backgrounds"],
            ["transparent-checkerboard", "black", "white"],
        )
        contact_sheet = root / validation["contact_sheet_png"]
        self.assertTrue(contact_sheet.is_file())
        self.assertEqual(
            hashlib.sha256(contact_sheet.read_bytes()).hexdigest(),
            validation["contact_sheet_sha256"],
        )
        with Image.open(contact_sheet) as image:
            self.assertEqual(image.size, (960, 1680))

    def test_yolo_library_contains_only_final_transparent_poses(self) -> None:
        catalog = json.loads((SKILL / "assets/ip/yolo/catalog.json").read_text())
        files = {path.name for path in (SKILL / "assets/ip/yolo/poses").iterdir()}
        self.assertEqual(files, {"opening.png", "closing.png"})
        for asset in catalog["assets"]:
            with Image.open(SKILL / "assets/ip/yolo" / asset["file"]) as image:
                self.assertEqual(image.mode, "RGBA")

    def test_yolo_motion_candidate_has_catalog_component_and_valid_assets(self) -> None:
        root = SKILL / "assets/ip/yolo-motion-v1"
        catalog = json.loads((root / "catalog.json").read_text())
        self.assertEqual(catalog["asset_family"], "yolo-motion-v1")
        self.assertEqual(catalog["source_fps"], 12)
        self.assertEqual(catalog["status"], "candidate")
        self.assertEqual(catalog["production"]["default_display_height_1080p"], 320)
        self.assertEqual(catalog["production"]["max_display_height_1080p"], 380)
        self.assertEqual(
            {item["asset_id"] for item in catalog["motions"]},
            {
                "yolo-verify-source",
                "yolo-quiet-observe",
                "yolo-chin-think",
                "yolo-point-tap",
                "yolo-catch-card",
                "yolo-risk-reminder",
            },
        )
        self.assertEqual(set(catalog["props"]), {"magnifier", "card", "slot"})
        motion = next(item for item in catalog["motions"] if item["asset_id"] == "yolo-verify-source")
        self.assertEqual(set(motion["outcomes"]), {"not-found", "verified"})
        self.assertEqual(set(motion["facings"]), {"left", "right"})
        for facing in motion["facings"].values():
            for entry in facing["common"]:
                self.assertTrue((root / entry["file"]).exists())
            for branch in facing["branches"].values():
                self.assertGreaterEqual(sum(entry["ticks"] for entry in branch), 12)
                for entry in branch:
                    self.assertTrue((root / entry["file"]).exists())
        for motion in catalog["motions"]:
            self.assertEqual(motion["status"], "candidate")
            self.assertEqual(motion["evidence"]["manual_visual_review"], "pass")
            for facing in motion["facings"].values():
                for outcome, branch in facing["branches"].items():
                    entries = [*facing["common"], *branch]
                    self.assertGreaterEqual(len(entries), 8)
                    if motion["playback_mode"] != "loop":
                        self.assertGreaterEqual(entries[-1]["ticks"], catalog["source_fps"])
        for report in catalog["validation_reports"].values():
            self.assertTrue((root / report).exists())

        source = (SKILL / "assets/remotion-animation-library/YoloMotion.tsx").read_text()
        for contract in (
            "motionId",
            "facing",
            "outcome",
            "displayHeight",
            "freezeAtEnd",
            "reserved_slots_1080p",
        ):
            self.assertIn(contract, source)

    def test_cover_preset_has_independent_four_three_and_three_four_sources(self) -> None:
        root = SKILL / "assets/covers/ai-knowledge-high-density"
        catalog = json.loads((root / "catalog.json").read_text())
        self.assertEqual(catalog["delivery_default"], ["4:3", "3:4"])
        sizes = {}
        for asset in catalog["references"]:
            path = root / asset["file"]
            with Image.open(path) as image:
                sizes[asset["aspect_ratio"]] = image.size
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), asset["sha256"])
        self.assertGreater(sizes["4:3"][0], sizes["4:3"][1])
        self.assertGreater(sizes["3:4"][1], sizes["3:4"][0])

    def test_caption_defaults_have_clean_ten_pixel_stroke(self) -> None:
        source = (SKILL / "assets/remotion-caption-overlay/CaptionOverlay.tsx").read_text()
        for contract in (
            "bottomMargin = 86",
            "portrait ? 70 : 140",
            "portrait ? 940 : 1540",
            "fontSize = 49",
            "minimumFontSize = 36",
            "10 * scale",
            'paintOrder: "stroke fill"',
            'whiteSpace: "nowrap"',
            'replace(/\\s+/g, " ")',
        ):
            self.assertIn(contract, source)
        self.assertNotIn("textShadow", source)

    def test_ai_tech_dense_motion_pack_is_registered(self) -> None:
        preset = json.loads(
            (SKILL / "assets/design-system/ai-tech-dark-v1.json").read_text()
        )
        self.assertEqual(preset["canvas"]["width"], 1080)
        self.assertEqual(preset["canvas"]["height"], 1920)
        self.assertEqual(preset["canvas"]["render_image_format"], "png")
        self.assertEqual(preset["captions"]["mode"], "single-line")
        self.assertEqual(preset["motion_density_profile"], "dense-tech-v1")
        catalog = json.loads(
            (
                SKILL
                / "assets/remotion-animation-library/dense-tech-catalog.json"
            ).read_text()
        )
        self.assertEqual(catalog["status"], "project-proven")
        source = (
            SKILL / "assets/remotion-animation-library/DenseTechMotion.tsx"
        ).read_text()
        for component in catalog["components"]:
            if component == "ProductIcon":
                continue
            self.assertIn(component, source)

    def test_reusable_components_enforce_timing_and_alignment_contracts(self) -> None:
        source = (SKILL / "assets/remotion-animation-library/KnowledgeVisuals.tsx").read_text()
        self.assertIn("markerEnd={path.progress > 0.02", source)
        for progress in (
            "startToDecisionProgress",
            "questionLoopProgress",
            "decisionToContinueProgress",
            "continueToCompleteProgress",
        ):
            self.assertIn(progress, source)
        self.assertIn('alignItems: "center"', source)
        pattern = (SKILL / "assets/remotion-animation-library/PatternLibrary.tsx").read_text()
        self.assertIn('ink: "#12315B"', pattern)
        self.assertIn('surface: "#FFFCF7"', pattern)
        self.assertIn("stepStarts?: number[]", pattern)
        self.assertIn("columnStarts?: number[]", pattern)
        self.assertIn("tagStarts?: number[][]", pattern)


if __name__ == "__main__":
    unittest.main()
