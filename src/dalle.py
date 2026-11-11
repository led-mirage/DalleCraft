# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

from contextlib import ExitStack

from openai import OpenAI

MODEL_VARIANT_FLARE = "flare"
MODEL_VARIANT_SUNBURST = "sunburst"

MODEL_NAME_FLARE = "gpt-image-2.5-flare"
MODEL_NAME_SUNBURST = "gpt-image-2.5-sunburst"

IMAGE_SIZE_SQUARE = "1024x1024"
IMAGE_SIZE_LANDSCAPE = "1536x1024"
IMAGE_SIZE_PORTRAIT = "1024x1536"
IMAGE_SIZE_AUTO = "auto"

IMAGE_QUALITY_LOW = "low"
IMAGE_QUALITY_MEDIUM = "medium"
IMAGE_QUALITY_HIGH = "high"
IMAGE_QUALITY_XHIGH = "xhigh"
IMAGE_QUALITY_MAX = "max"
IMAGE_QUALITY_AUTO = "auto"


def _get_response_value(value, name, default=None):
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def extract_token_usage(response) -> dict:
    usage = _get_response_value(response, "usage")
    if usage is None:
        return {}

    token_usage = {
        "input_tokens": _get_response_value(usage, "input_tokens", 0),
        "output_tokens": _get_response_value(usage, "output_tokens", 0),
        "total_tokens": _get_response_value(usage, "total_tokens", 0),
    }

    input_details = _get_response_value(usage, "input_tokens_details")
    if input_details is not None:
        token_usage["input_tokens_details"] = {
            "text_tokens": _get_response_value(input_details, "text_tokens", 0),
            "image_tokens": _get_response_value(input_details, "image_tokens", 0),
        }

    output_details = _get_response_value(usage, "output_tokens_details")
    if output_details is not None:
        token_usage["output_tokens_details"] = {
            "text_tokens": _get_response_value(output_details, "text_tokens", 0),
            "image_tokens": _get_response_value(output_details, "image_tokens", 0),
        }

    return token_usage


def get_openai_model_name(variant: str) -> str:
    if variant == MODEL_VARIANT_SUNBURST:
        return MODEL_NAME_SUNBURST
    return MODEL_NAME_FLARE


def normalize_foundry_endpoint(endpoint: str) -> str:
    """Return a base URL suitable for the standard OpenAI client."""
    normalized = endpoint.strip().rstrip("/")
    if not normalized:
        raise ValueError("Microsoft Foundryのエンドポイントが設定されていません。")
    if not normalized.endswith("/openai/v1"):
        normalized = f"{normalized}/openai/v1"
    return f"{normalized}/"


class GPTImageClient:
    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self.model = model
        client_options = {"api_key": api_key}
        if base_url:
            client_options["base_url"] = normalize_foundry_endpoint(base_url)
        self.client = OpenAI(**client_options)

    def gen_image(
        self,
        prompt: str,
        size: str = IMAGE_SIZE_AUTO,
        quality: str = IMAGE_QUALITY_AUTO,
    ) -> tuple[str, str, dict]:
        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
            quality=quality,
            output_format="png",
            n=1,
        )

        image = response.data[0]
        if not image.b64_json:
            raise ValueError("画像生成APIから画像データが返されませんでした。")

        # GPT Image models do not return revised_prompt. Keep the field empty
        # so existing session log files remain compatible.
        revised_prompt = getattr(image, "revised_prompt", None) or ""
        return image.b64_json, revised_prompt, extract_token_usage(response)

    def edit_image(
        self,
        prompt: str,
        image_paths: str | list[str],
        size: str = IMAGE_SIZE_AUTO,
        quality: str = IMAGE_QUALITY_AUTO,
        mask_path: str | None = None,
    ) -> tuple[str, str, dict]:
        paths = [image_paths] if isinstance(image_paths, str) else list(image_paths)
        if not paths:
            raise ValueError("入力画像が指定されていません。")
        api_prompt = prompt
        if mask_path:
            api_prompt = (
                f"{prompt}\n\n"
                "The fully transparent area in the mask is the only area to edit. "
                "Reconstruct that area naturally according to the request. "
                "Do not render the mask, leave a black or blank patch, or make the result transparent. "
                "Preserve everything outside the masked area."
            )

        with ExitStack() as stack:
            input_images = [
                stack.enter_context(open(image_path, "rb"))
                for image_path in paths
            ]
            edit_options = {
                "model": self.model,
                "image": input_images[0] if len(input_images) == 1 else input_images,
                "prompt": api_prompt,
                "size": size,
                "quality": quality,
                "background": "opaque",
                "output_format": "png",
                "n": 1,
            }
            if mask_path:
                edit_options["mask"] = stack.enter_context(open(mask_path, "rb"))

            response = self.client.images.edit(
                **edit_options,
            )

        image = response.data[0]
        if not image.b64_json:
            raise ValueError("画像編集APIから画像データが返されませんでした。")

        revised_prompt = getattr(image, "revised_prompt", None) or ""
        return image.b64_json, revised_prompt, extract_token_usage(response)
