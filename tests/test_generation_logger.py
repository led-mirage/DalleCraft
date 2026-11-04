import sys
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from generation_logger import ImageGenerationLogger
from session import SessionEntry


class ImageGenerationLoggerTest(unittest.TestCase):
    @patch("generation_logger.open", new_callable=mock_open)
    def test_logs_edit_mode_and_input_images(self, file_open):
        entry = SessionEntry(
            "prompt",
            "",
            "openai",
            "gpt-image-2.5-flare",
            "1024x1024",
            "high",
            True,
            1.25,
            "generated.png",
            "generated_thumbnail.png",
            input_images=[
                {
                    "filename": "input-1.png",
                    "original_width": 3000,
                    "original_height": 300,
                    "width": 2048,
                    "height": 205,
                    "original_size_bytes": 25000000,
                    "size_bytes": 1200000,
                    "resized": True,
                },
                {
                    "filename": "input-2.png",
                    "original_width": 800,
                    "original_height": 600,
                    "width": 800,
                    "height": 600,
                    "original_size_bytes": 300000,
                    "size_bytes": 300000,
                    "resized": False,
                },
            ],
        )

        ImageGenerationLogger.log(entry)

        written = file_open().write.call_args.args[0]
        self.assertTrue(written.endswith(
            "\tgenerated.png\tedit\tinput-1.png,input-2.png\t"
            "3000x300,800x600\t2048x205,800x600\t"
            "25000000,300000\t1200000,300000\ttrue,false\n"
        ))

    @patch("generation_logger.open", new_callable=mock_open)
    def test_logs_generate_mode_without_input_image(self, file_open):
        entry = SessionEntry(
            "prompt",
            "",
            "openai",
            "gpt-image-2.5-flare",
            "1024x1024",
            "high",
            True,
            1.25,
            "generated.png",
            "generated_thumbnail.png",
        )

        ImageGenerationLogger.log(entry)

        written = file_open().write.call_args.args[0]
        self.assertTrue(written.endswith(
            "\tgenerated.png\tgenerate\t-\t-\t-\t-\t-\t-\n"
        ))


if __name__ == "__main__":
    unittest.main()
