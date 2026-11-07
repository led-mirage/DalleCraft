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
        self.assertEqual({}, entry.token_usage)
        self.assertIsNone(entry.cost_estimate)

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

    def test_round_trips_token_usage_and_cost_estimate(self):
        data = self.create_entry_data()
        data["token_usage"] = {
            "input_tokens": 10,
            "output_tokens": 1000,
            "total_tokens": 1010,
            "input_tokens_details": {
                "text_tokens": 10,
                "image_tokens": 0,
            },
        }
        data["cost_estimate"] = {
            "currency": "USD",
            "amount": 0.03005,
            "tokens_per_price_unit": 1000000,
            "rates": {
                "text_input": 5.0,
                "image_input": 8.0,
                "image_output": 30.0,
            },
        }

        serialized = SessionEntry.from_dict(data).to_dict()

        self.assertEqual(data["token_usage"], serialized["token_usage"])
        self.assertEqual(data["cost_estimate"], serialized["cost_estimate"])


if __name__ == "__main__":
    unittest.main()
