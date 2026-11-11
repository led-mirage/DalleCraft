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

    def test_builds_image_size_options_from_config(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "config.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="image-size-options"', source)
        self.assertIn('src="js/image-size.js"', source)
        self.assertIn("populateImageSizeRadios(", source)
        self.assertIn("config.model.size_presets", source)

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
        self.assertIn("session-cost-estimate", parser.ids)
        self.assertIn("prompt-input-container", parser.ids)
        self.assertIn("input-image-previews", parser.ids)

    def test_builds_image_size_options_from_config(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('src="js/image-size.js"', source)
        self.assertIn("populateImageSizeSelect(sizeSelect, sizePresets, size)", source)
        self.assertIn("modelConfig.size_presets", source)

    def test_formats_image_size_labels_dynamically(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "js" / "image-size.js"
        ).read_text(encoding="utf-8")

        self.assertIn("function formatImageSizeLabel(size)", source)
        self.assertIn('width > height ? "横長" : "縦長"', source)
        self.assertIn("imageSizeGreatestCommonDivisor(width, height)", source)

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
        self.assertIn("const MAX_INPUT_IMAGES = 2", source)
        self.assertIn("options.input_image_ids", source)
        self.assertIn("inputImages.forEach((inputImage, imageIndex)", source)

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

    def test_supports_favoriting_generated_images(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('favoriteButton.className = "favorite-button"', source)
        self.assertIn("updateFavoriteButton(favoriteButton, Boolean(entry.favorite))", source)
        self.assertIn("pywebview.api.api_set_favorite(entryId, favorite)", source)
        self.assertIn('button.setAttribute("aria-pressed"', source)

    def test_displays_modals_above_favorite_buttons(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "css" / "style.css"
        ).read_text(encoding="utf-8")
        modal_rule = re.search(r"\.modal-background\s*\{(.*?)\}", source, re.DOTALL)
        favorite_rule = re.search(r"\.favorite-button\s*\{(.*?)\}", source, re.DOTALL)

        self.assertIsNotNone(modal_rule)
        self.assertIsNotNone(favorite_rule)
        modal_z_index = int(re.search(r"z-index:\s*(\d+)", modal_rule.group(1)).group(1))
        favorite_z_index = int(
            re.search(r"z-index:\s*(\d+)", favorite_rule.group(1)).group(1)
        )
        self.assertGreater(modal_z_index, favorite_z_index)

    def test_supports_naming_generated_images(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="rename-image"', source)
        self.assertIn('id="rename-image"><i class="fa-regular fa-file"', source)
        self.assertIn('img.dataset.imageName = entry.image_name || ""', source)
        self.assertIn('imageName.className = "image-name"', source)
        self.assertIn("pywebview.api.api_set_image_name(entryId, imageName)", source)
        self.assertIn("updateImageName(entryId, result.image_name)", source)

    def test_supports_exporting_session_images(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="export-session-button"', source)
        self.assertIn('id="export-target-all"', source)
        self.assertIn('id="export-target-favorites"', source)
        self.assertIn("function openSessionExportDialog()", source)
        self.assertIn("pywebview.api.api_export_session_images(target)", source)
        self.assertIn("result.skipped_count > 0", source)

    def test_uses_generated_image_as_edit_reference(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="edit-from-image"', source)
        self.assertIn("prepareImageEdit(parseInt(target.dataset.entryId))", source)
        self.assertIn("pywebview.api.api_prepare_image_edit(entryId)", source)
        self.assertIn("pendingInputImages = [result]", source)
        self.assertIn('document.getElementById("prompt")', source)
        self.assertIn("prompt.focus()", source)

    def test_supports_brush_mask_editing(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="masked-edit-from-image"', source)
        self.assertIn('id="image-mask-canvas"', source)
        self.assertIn('id="image-mask-brush-size"', source)
        self.assertIn("handleImageMaskPointerDown", source)
        self.assertIn('viewport.addEventListener("wheel"', source)
        self.assertIn('event.code === "Space"', source)
        self.assertIn("clearImageMaskSelection", source)
        self.assertIn("pywebview.api.api_set_input_image_mask", source)
        self.assertIn("pywebview.api.api_get_pending_input_image_mask_base64", source)
        self.assertIn("restoreImageMaskSelection", source)
        self.assertIn("openImageMaskEditor(image, true)", source)
        self.assertIn("image.source_entry_id === entryId", source)

    def test_displays_token_usage_and_estimated_cost(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="image-info-input-tokens"', source)
        self.assertIn('id="image-info-output-tokens"', source)
        self.assertIn('id="image-info-total-tokens"', source)
        self.assertIn('id="image-info-estimated-cost"', source)
        self.assertIn("info.token_usage || {}", source)
        self.assertIn("info.cost_estimate", source)

    def test_displays_session_cost_estimate(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn("const sessionCostEntries = new Map()", source)
        self.assertIn("function updateSessionCostEntry(entry)", source)
        self.assertIn("function renderSessionCostEstimate()", source)
        self.assertIn("updateSessionCostEntry(entry)", source)
        self.assertIn("function setSessionUsageHistory(usageHistory)", source)
        self.assertNotIn("removeSessionCostEntry(cardId)", source)
        self.assertIn("resetSessionCostEstimate()", source)
        self.assertIn("API料金概算: ${formatSessionCost(currency, amount, 3)}", source)
        self.assertIn('details.push(`料金集計: ${estimatedCount}件`)', source)
        self.assertIn('details.push(`削除済み画像: ${deletedImageCount}件`)', source)
        self.assertIn('details.push(`算出不可: ${unavailableCount}件`)', source)
        self.assertIn("renderSessionCostEstimate();", source)


if __name__ == "__main__":
    unittest.main()
