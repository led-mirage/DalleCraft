import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dalle import (
    GPTImageClient,
    get_openai_model_name,
    normalize_foundry_endpoint,
)


class GPTImageClientTest(unittest.TestCase):
    def test_model_name_matches_variant(self):
        self.assertEqual("gpt-image-2.5-flare", get_openai_model_name("flare"))
        self.assertEqual("gpt-image-2.5-sunburst", get_openai_model_name("sunburst"))

    def test_normalizes_foundry_resource_and_v1_endpoints(self):
        self.assertEqual(
            "https://example.openai.azure.com/openai/v1/",
            normalize_foundry_endpoint("https://example.openai.azure.com"),
        )
        self.assertEqual(
            "https://example.services.ai.azure.com/openai/v1/",
            normalize_foundry_endpoint("https://example.services.ai.azure.com/openai/v1/"),
        )

    @patch("dalle.OpenAI")
    def test_generates_png_with_shared_gpt_image_parameters(self, openai_class):
        image = SimpleNamespace(b64_json="aW1hZ2U=", revised_prompt=None)
        openai_class.return_value.images.generate.return_value = SimpleNamespace(data=[image])

        client = GPTImageClient(
            api_key="test-key",
            model="flare-production",
            base_url="https://example.openai.azure.com",
        )
        image_b64, revised_prompt = client.gen_image(
            "a test image",
            size="1536x1024",
            quality="max",
        )

        openai_class.assert_called_once_with(
            api_key="test-key",
            base_url="https://example.openai.azure.com/openai/v1/",
        )
        openai_class.return_value.images.generate.assert_called_once_with(
            model="flare-production",
            prompt="a test image",
            size="1536x1024",
            quality="max",
            output_format="png",
            n=1,
        )
        self.assertEqual("aW1hZ2U=", image_b64)
        self.assertEqual("", revised_prompt)

    @patch("dalle.OpenAI")
    def test_edits_png_with_input_image(self, openai_class):
        image = SimpleNamespace(b64_json="ZWRpdGVk", revised_prompt="revised")
        openai_class.return_value.images.edit.return_value = SimpleNamespace(data=[image])

        client = GPTImageClient(api_key="test-key", model="gpt-image-2.5-sunburst")
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.png"
            input_path.write_bytes(b"test image")
            image_b64, revised_prompt = client.edit_image(
                "edit this image",
                str(input_path),
                size="1024x1024",
                quality="high",
            )

        call = openai_class.return_value.images.edit.call_args
        self.assertEqual("gpt-image-2.5-sunburst", call.kwargs["model"])
        self.assertEqual("edit this image", call.kwargs["prompt"])
        self.assertEqual("1024x1024", call.kwargs["size"])
        self.assertEqual("high", call.kwargs["quality"])
        self.assertEqual("png", call.kwargs["output_format"])
        self.assertEqual(1, call.kwargs["n"])
        self.assertEqual(str(input_path), call.kwargs["image"].name)
        self.assertEqual("ZWRpdGVk", image_b64)
        self.assertEqual("revised", revised_prompt)


if __name__ == "__main__":
    unittest.main()
