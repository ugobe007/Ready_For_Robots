"""Tests for the Kare face favicon renderer."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "render_kare_face_icons.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("render_kare_face_icons", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FaceIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_mod()
        cls.face = cls.mod.load_face()

    def test_face_is_15x15_with_stroke(self):
        self.assertEqual(len(self.face), 15)
        self.assertTrue(all(len(row) == 15 for row in self.face))
        self.assertEqual(self.face[0], [1] * 15)
        self.assertEqual(self.face[14], [1] * 15)
        self.assertEqual(self.face[1][0], 1)
        self.assertEqual(self.face[1][1], 0)

    def test_svg_rect_count_matches_filled_pixels(self):
        svg = self.mod.svg_face(self.face)
        filled = sum(sum(row) for row in self.face)
        self.assertEqual(svg.count("<rect x="), filled)
        self.assertIn(self.mod.NAVY_HEX, svg)
        self.assertIn(self.mod.EMERALD_HEX, svg)

    def test_32px_has_navy_pad_and_emerald_stroke(self):
        rows = self.mod.paint_face(self.face, canvas=32, scale=2, pad=1)
        self.assertEqual(rows[0][0], self.mod.NAVY)
        self.assertEqual(rows[1][0], self.mod.NAVY)
        self.assertEqual(rows[1][1], self.mod.EMERALD)

    def test_og_canvas_is_1200x630(self):
        rows = self.mod.paint_og(self.face)
        self.assertEqual(len(rows), 630)
        self.assertEqual(len(rows[0]), 1200)
        self.assertEqual(rows[0][0], self.mod.NAVY)
        # Top-left stroke of the 15×15 face, scaled 28px, centered on 1200×630.
        self.assertEqual(rows[105][390], self.mod.EMERALD)

    def test_generated_files_on_disk(self):
        self.mod.check_assets(self.face)


if __name__ == "__main__":
    unittest.main()
