import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


class _IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, _tag, attrs):
        self.ids.update(value for key, value in attrs if key == "id")


class ConfigHtmlTest(unittest.TestCase):
    def test_javascript_references_existing_elements(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "config.html"
        ).read_text(encoding="utf-8")
        parser = _IdCollector()
        parser.feed(source)
        references = set(re.findall(r'getElementById\("([^"]+)"\)', source))

        self.assertEqual(references - parser.ids, set())


class IndexHtmlTest(unittest.TestCase):
    def test_quick_setting_elements_exist(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")
        parser = _IdCollector()
        parser.feed(source)

        self.assertIn("quick-image-size", parser.ids)
        self.assertIn("quick-image-quality", parser.ids)
        self.assertIn("current-api-type", parser.ids)
        self.assertIn("prompt-input-container", parser.ids)
        self.assertIn("input-image-preview", parser.ids)
        self.assertIn("input-image-preview-img", parser.ids)
        self.assertIn("remove-input-image-button", parser.ids)

    def test_quick_quality_labels_are_english(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        for label in ("Auto", "Low", "Medium", "High", "XHigh", "Max"):
            self.assertRegex(source, rf'<option value="[^"]+">{label}</option>')

    def test_displays_current_api_type(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn("initCurrentApiType(config.api_type)", source)
        self.assertIn('openai: "OpenAI"', source)
        self.assertIn('foundry: "Microsoft Foundry"', source)

    def test_supports_paste_and_drop_input_images(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('prompt.addEventListener("paste", handleInputImagePaste)', source)
        self.assertIn('container.addEventListener("drop", handleInputImageDrop)', source)
        self.assertIn("file.size >= 20 * 1024 * 1024", source)
        self.assertIn("result.resize_message", source)

    def test_supports_copying_generated_images(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="copy-image"', source)
        self.assertIn("pywebview.api.api_copy_image(cardId)", source)
        self.assertIn("画像をクリップボードにコピーしました", source)

    def test_supports_zooming_modal_images(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="image-modal-viewport"', source)
        self.assertIn('viewport.addEventListener("wheel"', source)
        self.assertIn('modalImg.addEventListener("mousedown"', source)
        self.assertIn('modalImg.addEventListener("dblclick"', source)
        self.assertIn("function clampImageModalPosition()", source)

    def test_regenerates_with_the_original_entry(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn("regenerateImage(parseInt(target.dataset.entryId))", source)
        self.assertIn("pywebview.api.api_regenerate_image(entryId, getQuickSettings())", source)


if __name__ == "__main__":
    unittest.main()
