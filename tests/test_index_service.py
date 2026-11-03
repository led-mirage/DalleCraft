import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import Config
from session import SessionManager
from services.index_service import IndexService


class IndexServiceTest(unittest.TestCase):
    @patch("services.index_service.GPTImageClient")
    def test_creates_foundry_client_with_selected_deployment(self, client_class):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        config.api_type = "foundry"
        config.model["variant"] = "sunburst"
        config.foundry["sunburst_deployment"] = "sunburst-production"
        config.foundry["api_key_envvar"] = "TEST_FOUNDRY_KEY"
        config.foundry["endpoint_envvar"] = "TEST_FOUNDRY_ENDPOINT"
        service = IndexService(window=None, config=config, session_manager=None)

        with patch.dict(
            os.environ,
            {
                "TEST_FOUNDRY_KEY": "test-key",
                "TEST_FOUNDRY_ENDPOINT": "https://example.services.ai.azure.com/openai/v1/",
            },
        ):
            service.create_image_client()

        client_class.assert_called_once_with(
            api_key="test-key",
            base_url="https://example.services.ai.azure.com/openai/v1/",
            model="sunburst-production",
        )

    @patch("services.index_service.ImageGenerationLogger.log")
    @patch.object(Config, "save")
    def test_generates_with_and_saves_quick_options(self, config_save, log):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        session_manager = SessionManager()
        session = session_manager.create_new_session()
        session.save_to_file = Mock(return_value=True)
        service = IndexService(window=None, config=config, session_manager=session_manager)
        service.gen_image = Mock(return_value=("aW1hZ2U=", "", 1.25))
        service.save_image = Mock(return_value="images/generated.png")
        service.save_resized_image = Mock(return_value="images/generated_thumbnail.png")

        result = service.api_gen_image(
            "a test image",
            {"size": "1536x1024", "quality": "high"},
        )

        service.gen_image.assert_called_once_with(
            "a test image",
            size="1536x1024",
            quality="high",
        )
        config_save.assert_called_once_with("config.json")
        self.assertEqual("1536x1024", config.model["size"])
        self.assertEqual("high", config.model["quality"])
        self.assertEqual("1536x1024", result["image_size"])
        self.assertEqual("high", result["image_quality"])
        log.assert_called_once()

    @patch.object(Config, "save")
    def test_rejects_invalid_quick_options_without_generating(self, config_save):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = IndexService(window=None, config=config, session_manager=None)
        service.gen_image = Mock()

        result = service.api_gen_image(
            "a test image",
            {"size": "invalid", "quality": "high"},
        )

        self.assertIn("未対応の解像度", result["error_info"])
        service.gen_image.assert_not_called()
        config_save.assert_not_called()

    @patch.object(Config, "save")
    def test_updates_generation_options_without_generating(self, config_save):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = IndexService(window=None, config=config, session_manager=None)

        result = service.api_update_generation_options(
            {"size": "1024x1536", "quality": "max"}
        )

        self.assertTrue(result["success"])
        self.assertEqual("1024x1536", config.model["size"])
        self.assertEqual("max", config.model["quality"])
        config_save.assert_called_once_with("config.json")


if __name__ == "__main__":
    unittest.main()
