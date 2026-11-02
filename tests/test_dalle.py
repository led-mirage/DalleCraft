import sys
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


if __name__ == "__main__":
    unittest.main()
