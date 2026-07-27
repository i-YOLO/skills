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

    def test_yolo_library_contains_only_final_transparent_poses(self) -> None:
        catalog = json.loads((SKILL / "assets/ip/yolo/catalog.json").read_text())
        files = {path.name for path in (SKILL / "assets/ip/yolo/poses").iterdir()}
        self.assertEqual(files, {"opening.png", "closing.png"})
        for asset in catalog["assets"]:
            with Image.open(SKILL / "assets/ip/yolo" / asset["file"]) as image:
                self.assertEqual(image.mode, "RGBA")

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
            "horizontalMargin = 140",
            "maxWidth = 1540",
            "fontSize = 49",
            "10 * scale",
            'paintOrder: "stroke fill"',
        ):
            self.assertIn(contract, source)
        self.assertNotIn("textShadow", source)

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
