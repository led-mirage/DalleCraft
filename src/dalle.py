# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

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
    ) -> tuple[str, str]:
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
        return image.b64_json, revised_prompt

    def edit_image(
        self,
        prompt: str,
        image_path: str,
        size: str = IMAGE_SIZE_AUTO,
        quality: str = IMAGE_QUALITY_AUTO,
    ) -> tuple[str, str]:
        with open(image_path, "rb") as input_image:
            response = self.client.images.edit(
                model=self.model,
                image=input_image,
                prompt=prompt,
                size=size,
                quality=quality,
                output_format="png",
                n=1,
            )

        image = response.data[0]
        if not image.b64_json:
            raise ValueError("画像編集APIから画像データが返されませんでした。")

        revised_prompt = getattr(image, "revised_prompt", None) or ""
        return image.b64_json, revised_prompt
