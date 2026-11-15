# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import json

from image_options import (
    DEFAULT_IMAGE_SIZE_PRESETS,
    normalize_image_size,
    normalize_image_size_presets,
)
from model_options import (
    DEFAULT_COMPLEXITY,
    DEFAULT_MODEL_ID,
    MODEL_ID_GPT_IMAGE_2_5_FLARE,
    MODEL_ID_GPT_IMAGE_2_5_SUNBURST,
    SUPPORTED_COMPLEXITIES,
    SUPPORTED_MODEL_IDS,
    legacy_model_id,
)


def _normalize_text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


class Config:
    FILE_VERSION = "4.0"

    DEFAULT_SIZE = "auto"
    DEFAULT_QUALITY = "auto"
    DEFAULT_WELCOME_MESSAGE = "DalleCraft is a tool for generating images using GPT Image."
    LEGACY_WELCOME_MESSAGES = {
        "DalleCraft is a tool for generating images using DALL-E3.",
        "DalleCraft is a tool for generating images using GPT Image 2.5.",
    }
    LEGACY_WELCOME_MESSAGE = "DalleCraft is a tool for generating images using DALL-E3."

    def __init__(self, config_path=None):
        self.version = None
        self.api_type = None
        self.openai = {
            "api_key_envvar": None
        }
        self.foundry = {
            "api_key_envvar": None,
            "endpoint_envvar": None,
            "deployments": {}
        }
        self.model = {
            "id": None,
            "size": None,
            "quality": None,
            "complexity": None,
            "size_presets": []
        }
        self.system = {
            "window_width": None,
            "window_height": None,
            "welcome_title": None,
            "welcome_message": None
        }
        if config_path:
            self.load(config_path)

    def get_model_param(self):
        return self.model["size"], self.model["quality"]

    def get_complexity(self) -> str:
        return self.model["complexity"]

    def get_model_name(self) -> str:
        model_id = self.model["id"]
        if self.api_type == "foundry":
            deployment = self.foundry["deployments"].get(model_id, "").strip()
            if not deployment:
                raise ValueError(f"{model_id}のFoundryデプロイ名が設定されていません。")
            return deployment
        return model_id

    def load(self, config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.version = data.get("version", None)
            api_type = data.get("api_type", "openai")
            self.api_type = "foundry" if api_type == "azure" else api_type
            self.openai["api_key_envvar"] = data.get("openai", {}).get("api_key_envvar", "OPENAI_API_KEY")

            # v2 used the "azure" key and v3 used one deployment per variant.
            # Read all formats so existing installations can open v4 settings.
            foundry_data = data.get("foundry", data.get("azure", {}))
            self.foundry["api_key_envvar"] = foundry_data.get("api_key_envvar", "AZURE_OPENAI_API_KEY")
            self.foundry["endpoint_envvar"] = foundry_data.get("endpoint_envvar", "AZURE_OPENAI_ENDPOINT")
            deployments = foundry_data.get("deployments", {})
            if not isinstance(deployments, dict):
                deployments = {}
            normalized_deployments = {
                model_id: _normalize_text(deployments.get(model_id, ""))
                for model_id in SUPPORTED_MODEL_IDS
            }
            normalized_deployments[MODEL_ID_GPT_IMAGE_2_5_FLARE] = _normalize_text(
                foundry_data.get(
                    "flare_deployment",
                    normalized_deployments[MODEL_ID_GPT_IMAGE_2_5_FLARE],
                )
            )
            normalized_deployments[MODEL_ID_GPT_IMAGE_2_5_SUNBURST] = _normalize_text(
                foundry_data.get(
                    "sunburst_deployment",
                    normalized_deployments[MODEL_ID_GPT_IMAGE_2_5_SUNBURST],
                )
            )
            self.foundry["deployments"] = normalized_deployments

            model_data = data.get("model", {})
            if "id" in model_data:
                model_id = model_data["id"]
            elif "variant" in model_data:
                model_id = legacy_model_id(model_data["variant"])
            elif self.version in ("2.0", "3.0"):
                model_id = MODEL_ID_GPT_IMAGE_2_5_FLARE
            else:
                model_id = DEFAULT_MODEL_ID
            self.model["id"] = model_id if model_id in SUPPORTED_MODEL_IDS else DEFAULT_MODEL_ID

            if "size" in model_data:
                size = model_data["size"]
            else:
                size = model_data.get("gptimage1", {}).get("size", self.DEFAULT_SIZE)
            self.model["size"] = normalize_image_size(size) or self.DEFAULT_SIZE

            size_presets = model_data.get("size_presets", DEFAULT_IMAGE_SIZE_PRESETS)
            self.model["size_presets"] = normalize_image_size_presets(size_presets)
            if self.model["size"] not in self.model["size_presets"]:
                self.model["size_presets"].append(self.model["size"])

            if "quality" in model_data:
                quality = model_data["quality"]
            else:
                quality = model_data.get("gptimage1", {}).get("quality", self.DEFAULT_QUALITY)
            self.model["quality"] = quality if quality in ("low", "medium", "high", "xhigh", "max", "auto") else self.DEFAULT_QUALITY

            complexity = model_data.get("complexity", DEFAULT_COMPLEXITY)
            self.model["complexity"] = (
                complexity
                if complexity in SUPPORTED_COMPLEXITIES
                else DEFAULT_COMPLEXITY
            )

            self.system["window_width"] = data.get("system", {}).get("window_width", 1024)
            self.system["window_height"] = data.get("system", {}).get("window_height", 800)
            self.system["welcome_title"] = data.get("system", {}).get("welcome_title", "Welcome")
            welcome_message = data.get("system", {}).get("welcome_message", self.DEFAULT_WELCOME_MESSAGE)
            self.system["welcome_message"] = (
                self.DEFAULT_WELCOME_MESSAGE
                if welcome_message in self.LEGACY_WELCOME_MESSAGES
                else welcome_message
            )

    def save(self, config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

    def to_dict(self):
        return {
            "version": self.FILE_VERSION,
            "api_type": self.api_type,
            "openai": self.openai,
            "foundry": self.foundry,
            "model": self.model,
            "system": self.system
        }
