import base64
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config import Config
from session import SessionEntry, SessionManager
from app_const import IMAGE_DIR
from services.index_service import INPUT_IMAGE_DIR, IndexService


class IndexServiceTest(unittest.TestCase):
    def create_service(self, config, session_manager=None):
        service = IndexService(
            window=None,
            config=config,
            session_manager=session_manager,
        )
        self.addCleanup(service.close)
        return service

    def create_png_base64(self, size=(8, 8)):
        buffer = io.BytesIO()
        Image.new("RGB", size, "red").save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    @patch("services.index_service.GPTImageClient")
    def test_creates_foundry_client_with_selected_deployment(self, client_class):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        config.api_type = "foundry"
        config.model["variant"] = "sunburst"
        config.foundry["sunburst_deployment"] = "sunburst-production"
        config.foundry["api_key_envvar"] = "TEST_FOUNDRY_KEY"
        config.foundry["endpoint_envvar"] = "TEST_FOUNDRY_ENDPOINT"
        service = self.create_service(config)

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
        service = self.create_service(config, session_manager)
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
            input_image_path=None,
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
        service = self.create_service(config)
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
        service = self.create_service(config)

        result = service.api_update_generation_options(
            {"size": "1024x1536", "quality": "max"}
        )

        self.assertTrue(result["success"])
        self.assertEqual("1024x1536", config.model["size"])
        self.assertEqual("max", config.model["quality"])
        config_save.assert_called_once_with("config.json")

    def test_registers_and_releases_pasted_image(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = self.create_service(config)

        result = service.api_register_input_image({
            "filename": "clipboard.png",
            "source": "clipboard",
            "mime_type": "image/png",
            "image_base64": self.create_png_base64(),
        })

        self.assertTrue(result["success"])
        self.assertEqual("clipboard.png", result["filename"])
        self.assertEqual("image/png", result["mime_type"])
        self.assertTrue(result["preview_base64"])
        self.assertFalse(result["resized"])
        self.assertEqual((8, 8), (result["original_width"], result["original_height"]))
        self.assertEqual((8, 8), (result["width"], result["height"]))
        self.assertEqual(result["original_size_bytes"], result["size_bytes"])
        self.assertIn(result["input_image_id"], service._pending_input_images)

        release_result = service.api_release_input_image(result["input_image_id"])
        self.assertTrue(release_result["success"])
        self.assertNotIn(result["input_image_id"], service._pending_input_images)

    def test_rejects_non_image_input(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = self.create_service(config)

        result = service.api_register_input_image({
            "filename": "not-image.png",
            "source": "drop",
            "mime_type": "image/png",
            "image_base64": base64.b64encode(b"not an image").decode("ascii"),
        })

        self.assertFalse(result["success"])
        self.assertIn("PNG、JPEG、WebP", result["error_info"])

    def test_rejects_input_image_at_size_limit(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = self.create_service(config)
        service.MAX_INPUT_IMAGE_BYTES = 8

        result = service.api_register_input_image({
            "filename": "large.png",
            "source": "drop",
            "mime_type": "image/png",
            "image_base64": base64.b64encode(b"12345678").decode("ascii"),
        })

        self.assertFalse(result["success"])
        self.assertIn("20MB未満", result["error_info"])

    def test_resizes_input_image_long_edge_to_2048_pixels(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = self.create_service(config)

        result = service.api_register_input_image({
            "filename": "wide.png",
            "source": "drop",
            "mime_type": "image/png",
            "image_base64": self.create_png_base64((3000, 300)),
        })

        self.assertTrue(result["success"])
        self.assertTrue(result["resized"])
        self.assertEqual((3000, 300), (result["original_width"], result["original_height"]))
        self.assertEqual((2048, 205), (result["width"], result["height"]))
        self.assertIn("3000×300", result["resize_message"])
        self.assertIn("2048×205", result["resize_message"])
        pending = service._pending_input_images[result["input_image_id"]]
        with Image.open(pending["path"]) as image:
            self.assertEqual((2048, 205), image.size)

    def test_preserves_png_transparency_when_resizing(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = self.create_service(config)
        buffer = io.BytesIO()
        Image.new("RGBA", (2050, 2), (255, 0, 0, 0)).save(buffer, format="PNG")

        result = service.api_register_input_image({
            "filename": "transparent.png",
            "source": "drop",
            "mime_type": "image/png",
            "image_base64": base64.b64encode(buffer.getvalue()).decode("ascii"),
        })

        self.assertTrue(result["success"])
        pending = service._pending_input_images[result["input_image_id"]]
        with Image.open(pending["path"]) as image:
            self.assertIn("A", image.getbands())
            self.assertEqual(0, image.getchannel("A").getextrema()[1])

    @patch("services.index_service.ImageGenerationLogger.log")
    @patch.object(Config, "save")
    def test_generates_edit_with_registered_input_image(self, config_save, log):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        session_manager = SessionManager()
        session = session_manager.create_new_session()
        session.save_to_file = Mock(return_value=True)
        service = self.create_service(config, session_manager)
        registered = service.api_register_input_image({
            "filename": "source.png",
            "source": "drop",
            "mime_type": "image/png",
            "image_base64": self.create_png_base64(),
        })
        pending_path = service._pending_input_images[registered["input_image_id"]]["path"]
        service.gen_image = Mock(return_value=("aW1hZ2U=", "", 1.25))
        service.save_image = Mock(return_value="images/generated.png")
        service.save_resized_image = Mock(return_value="images/generated_thumbnail.png")
        service.persist_input_image = Mock(return_value={
            "filename": "input_image.png",
            "thumbnail_filename": "input_image_thumbnail.png",
            "original_name": "source.png",
            "source": "drop",
            "mime_type": "image/png",
        })

        result = service.api_gen_image(
            "edit this image",
            {
                "size": config.model["size"],
                "quality": config.model["quality"],
                "input_image_id": registered["input_image_id"],
            },
        )

        service.gen_image.assert_called_once_with(
            "edit this image",
            size=config.model["size"],
            quality=config.model["quality"],
            input_image_path=pending_path,
        )
        self.assertEqual("source.png", result["input_images"][0]["original_name"])
        self.assertNotIn(registered["input_image_id"], service._pending_input_images)
        log.assert_called_once()

    def test_removes_generated_and_input_image_files(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = self.create_service(config)
        service.remove_managed_file = Mock()
        entry = SessionEntry(
            "prompt",
            "",
            "openai",
            "gpt-image-2.5-flare",
            "1024x1024",
            "high",
            True,
            1.0,
            "generated.png",
            "generated_thumbnail.png",
            input_images=[{
                "filename": "input.png",
                "thumbnail_filename": "input_thumbnail.png",
            }],
        )

        service.remove_entry_files(entry)

        self.assertEqual(
            [
                call("generated.png"),
                call("generated_thumbnail.png"),
                call("input.png", INPUT_IMAGE_DIR),
                call("input.png", IMAGE_DIR),
                call("input_thumbnail.png", INPUT_IMAGE_DIR),
                call("input_thumbnail.png", IMAGE_DIR),
            ],
            service.remove_managed_file.call_args_list,
        )

    def test_persists_input_images_under_log_directory(self):
        config = Config(Path(__file__).resolve().parents[1] / "config.json")
        service = self.create_service(config)
        registered = service.api_register_input_image({
            "filename": "source.png",
            "source": "drop",
            "mime_type": "image/png",
            "image_base64": self.create_png_base64(),
        })
        pending = service._pending_input_images[registered["input_image_id"]]

        with tempfile.TemporaryDirectory() as directory:
            input_directory = Path(directory) / "logs" / "input-images"
            with patch("services.index_service.INPUT_IMAGE_DIR", str(input_directory)):
                metadata = service.persist_input_image(pending)

            self.assertTrue((input_directory / metadata["filename"]).exists())
            self.assertTrue(
                (input_directory / metadata["thumbnail_filename"]).exists()
            )
            self.assertEqual(8, metadata["original_width"])
            self.assertEqual(8, metadata["width"])
            self.assertFalse(metadata["resized"])


if __name__ == "__main__":
    unittest.main()
