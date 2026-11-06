import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import Config
from image_options import DEFAULT_IMAGE_SIZE_PRESETS


class ConfigTest(unittest.TestCase):
    def write_config(self, directory: str, data: dict) -> Path:
        path = Path(directory) / "config.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_loads_v3_config_and_selects_provider_model(self):
        data = {
            "version": "3.0",
            "api_type": "foundry",
            "openai": {"api_key_envvar": "OPENAI_API_KEY"},
            "foundry": {
                "api_key_envvar": "FOUNDRY_KEY",
                "endpoint_envvar": "FOUNDRY_ENDPOINT",
                "flare_deployment": "flare-production",
                "sunburst_deployment": "sunburst-production",
            },
            "model": {
                "variant": "sunburst",
                "size": "1536x1024",
                "quality": "xhigh",
            },
            "system": {},
        }

        with tempfile.TemporaryDirectory() as directory:
            config = Config(self.write_config(directory, data))

        self.assertEqual("foundry", config.api_type)
        self.assertEqual("sunburst-production", config.get_model_name())
        self.assertEqual(("1536x1024", "xhigh"), config.get_model_param())
        self.assertEqual(
            list(DEFAULT_IMAGE_SIZE_PRESETS),
            config.model["size_presets"],
        )

        config.api_type = "openai"
        self.assertEqual("gpt-image-2.5-sunburst", config.get_model_name())

    def test_migrates_v2_azure_and_gpt_image_settings(self):
        data = {
            "version": "2.0",
            "api_type": "azure",
            "openai": {
                "api_key_envvar": "OPENAI_API_KEY",
                "model_name": "gpt-image-1",
            },
            "azure": {
                "api_key_envvar": "OLD_AZURE_KEY",
                "endpoint_envvar": "OLD_AZURE_ENDPOINT",
                "model_name": "gpt-image-1",
            },
            "model": {
                "model_type": "gptimage1",
                "gptimage1": {
                    "size": "1024x1536",
                    "quality": "high",
                },
            },
            "system": {
                "welcome_message": Config.LEGACY_WELCOME_MESSAGE,
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory, data)
            config = Config(path)
            config.save(path)
            saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual("foundry", config.api_type)
        self.assertEqual("flare", config.model["variant"])
        self.assertEqual("1024x1536", config.model["size"])
        self.assertEqual("high", config.model["quality"])
        self.assertEqual(Config.DEFAULT_WELCOME_MESSAGE, config.system["welcome_message"])
        self.assertEqual("3.0", saved["version"])
        self.assertIn("foundry", saved)
        self.assertNotIn("azure", saved)
        self.assertNotIn("gptimage1", saved["model"])

    def test_loads_custom_size_presets_and_filters_invalid_values(self):
        data = {
            "version": "3.0",
            "model": {
                "variant": "flare",
                "size": "1536 × 864",
                "quality": "auto",
                "size_presets": [
                    "auto",
                    "1536 × 864",
                    "1536x864",
                    "1920x1080",
                ],
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            config = Config(self.write_config(directory, data))

        self.assertEqual("1536x864", config.model["size"])
        self.assertEqual(
            ["auto", "1536x864"],
            config.model["size_presets"],
        )

    def test_adds_valid_selected_size_to_presets(self):
        data = {
            "version": "3.0",
            "model": {
                "variant": "flare",
                "size": "2048x2048",
                "quality": "auto",
                "size_presets": ["auto", "1024x1024"],
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            config = Config(self.write_config(directory, data))

        self.assertEqual(
            ["auto", "1024x1024", "2048x2048"],
            config.model["size_presets"],
        )


if __name__ == "__main__":
    unittest.main()
