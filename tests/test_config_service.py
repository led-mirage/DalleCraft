import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import Config
from services.config_service import ConfigService


class ConfigServiceTest(unittest.TestCase):
    def create_submission(self, api_type="openai"):
        return {
            "apiType": api_type,
            "openai": {"api_key_envvar": "OPENAI_API_KEY"},
            "foundry": {
                "api_key_envvar": "FOUNDRY_KEY",
                "endpoint_envvar": "FOUNDRY_ENDPOINT",
                "deployments": {
                    "gpt-image-2.6-flare": "flare-production",
                    "gpt-image-2.6-sunburst": "",
                    "gpt-image-2.5-flare": "",
                    "gpt-image-2.5-sunburst": "",
                },
            },
            "model": {
                "id": "gpt-image-2.6-flare",
                "size": "1024x1024",
                "quality": "high",
                "complexity": "medium",
            },
        }

    def test_restores_prompt_draft_only_once(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        window = Mock()
        service = ConfigService(window, config)

        service.api_open_config("unfinished prompt")

        window.open_config_view.assert_called_once_with()
        self.assertEqual("unfinished prompt", service.api_take_prompt_draft())
        self.assertIsNone(service.api_take_prompt_draft())

    def test_preserves_empty_prompt_draft(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = ConfigService(Mock(), config)

        service.api_open_config("")

        self.assertEqual("", service.api_take_prompt_draft())

    @patch.object(Config, "save")
    def test_saves_model_and_foundry_deployment_map(self, save):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        window = Mock()
        service = ConfigService(window, config)

        service.api_submit_config(self.create_submission("foundry"))

        self.assertEqual("gpt-image-2.6-flare", config.model["id"])
        self.assertEqual("medium", config.model["complexity"])
        self.assertEqual(
            "flare-production",
            config.foundry["deployments"]["gpt-image-2.6-flare"],
        )
        save.assert_called_once_with("config.json")
        window.open_index_view.assert_called_once_with()

    def test_rejects_missing_selected_foundry_deployment(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        original_api_type = config.api_type
        original_model_name = config.get_model_name()
        service = ConfigService(Mock(), config)
        submission = self.create_submission("foundry")
        submission["foundry"]["deployments"]["gpt-image-2.6-flare"] = ""

        with self.assertRaisesRegex(ValueError, "Foundryデプロイ名"):
            service.api_submit_config(submission)

        self.assertEqual(original_api_type, config.api_type)
        self.assertEqual(original_model_name, config.get_model_name())


if __name__ == "__main__":
    unittest.main()
