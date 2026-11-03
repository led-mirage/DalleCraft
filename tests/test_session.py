import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from session import SessionEntry


class SessionEntryTest(unittest.TestCase):
    def create_entry_data(self):
        return {
            "id": 1,
            "timestamp": datetime.now().isoformat(),
            "prompt": "test",
            "revised_prompt": "",
            "api_type": "openai",
            "model_name": "gpt-image-2.5-flare",
            "image_size": "1024x1024",
            "image_quality": "high",
            "success": True,
            "elapsed_time": 1.0,
            "image_filename": "generated.png",
            "thumbnail_filename": "generated_thumbnail.png",
            "error_info": None,
        }

    def test_loads_legacy_entry_without_input_images(self):
        entry = SessionEntry.from_dict(self.create_entry_data())

        self.assertEqual([], entry.input_images)

    def test_round_trips_input_image_metadata(self):
        data = self.create_entry_data()
        data["input_images"] = [{
            "filename": "input.png",
            "thumbnail_filename": "input_thumbnail.png",
            "original_name": "pasted-image.png",
            "source": "clipboard",
            "mime_type": "image/png",
            "original_width": 3000,
            "original_height": 300,
            "width": 2048,
            "height": 205,
            "original_size_bytes": 25000000,
            "size_bytes": 1200000,
            "resized": True,
        }]

        entry = SessionEntry.from_dict(data)
        serialized = entry.to_dict()

        self.assertEqual(data["input_images"], serialized["input_images"])


if __name__ == "__main__":
    unittest.main()
