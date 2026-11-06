import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from image_options import normalize_image_size, normalize_image_size_presets


class ImageOptionsTest(unittest.TestCase):
    def test_accepts_and_normalizes_supported_sizes(self):
        expected = {
            "auto": "auto",
            " 1536 × 864 ": "1536x864",
            "3840X2160": "3840x2160",
            "3072x1024": "3072x1024",
        }

        for value, normalized in expected.items():
            with self.subTest(value=value):
                self.assertEqual(normalized, normalize_image_size(value))

    def test_rejects_sizes_outside_api_constraints(self):
        invalid_sizes = (
            None,
            1024,
            "invalid",
            "1920x1080",
            "640x640",
            "4096x1024",
            "3088x1024",
            "3840x2304",
        )

        for value in invalid_sizes:
            with self.subTest(value=value):
                self.assertIsNone(normalize_image_size(value))

    def test_normalizes_deduplicates_and_filters_presets(self):
        presets = normalize_image_size_presets([
            "auto",
            "1536 × 864",
            "1536x864",
            "1920x1080",
        ])

        self.assertEqual(["auto", "1536x864"], presets)
        self.assertEqual(["auto"], normalize_image_size_presets([]))


if __name__ == "__main__":
    unittest.main()
