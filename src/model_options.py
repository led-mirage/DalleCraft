# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

MODEL_ID_GPT_IMAGE_2_6_FLARE = "gpt-image-2.6-flare"
MODEL_ID_GPT_IMAGE_2_6_SUNBURST = "gpt-image-2.6-sunburst"
MODEL_ID_GPT_IMAGE_2_5_FLARE = "gpt-image-2.5-flare"
MODEL_ID_GPT_IMAGE_2_5_SUNBURST = "gpt-image-2.5-sunburst"

SUPPORTED_MODEL_IDS = (
    MODEL_ID_GPT_IMAGE_2_6_FLARE,
    MODEL_ID_GPT_IMAGE_2_6_SUNBURST,
    MODEL_ID_GPT_IMAGE_2_5_FLARE,
    MODEL_ID_GPT_IMAGE_2_5_SUNBURST,
)

DEFAULT_MODEL_ID = MODEL_ID_GPT_IMAGE_2_6_FLARE
DEFAULT_COMPLEXITY = "high"
SUPPORTED_COMPLEXITIES = ("low", "medium", "high")


def legacy_model_id(variant: str) -> str:
    if variant == "sunburst":
        return MODEL_ID_GPT_IMAGE_2_5_SUNBURST
    return MODEL_ID_GPT_IMAGE_2_5_FLARE


def supports_complexity(model_id: str) -> bool:
    return model_id in (
        MODEL_ID_GPT_IMAGE_2_6_FLARE,
        MODEL_ID_GPT_IMAGE_2_6_SUNBURST,
    )
