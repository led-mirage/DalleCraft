import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import Config
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


if __name__ == "__main__":
    unittest.main()
