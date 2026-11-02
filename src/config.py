# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import json


class Config:
    FILE_VERSION = "3.0"

    DEFAULT_VARIANT = "flare"
    DEFAULT_SIZE = "auto"
    DEFAULT_QUALITY = "auto"
    DEFAULT_WELCOME_MESSAGE = "DalleCraft is a tool for generating images using GPT Image 2.5."
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
            "flare_deployment": None,
            "sunburst_deployment": None
        }
        self.model = {
            "variant": None,
            "size": None,
            "quality": None
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

    def get_model_name(self) -> str:
        variant = self.model["variant"]
        if self.api_type == "foundry":
            return self.foundry[f"{variant}_deployment"]
        return f"gpt-image-2.5-{variant}"

    def load(self, config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.version = data.get("version", None)
            api_type = data.get("api_type", "openai")
            self.api_type = "foundry" if api_type == "azure" else api_type
            self.openai["api_key_envvar"] = data.get("openai", {}).get("api_key_envvar", "OPENAI_API_KEY")

            # v2 used the "azure" key and a single deployment name. Read both
            # formats so existing installations can open the v3 settings page.
            foundry_data = data.get("foundry", data.get("azure", {}))
            self.foundry["api_key_envvar"] = foundry_data.get("api_key_envvar", "AZURE_OPENAI_API_KEY")
            self.foundry["endpoint_envvar"] = foundry_data.get("endpoint_envvar", "AZURE_OPENAI_ENDPOINT")
            self.foundry["flare_deployment"] = foundry_data.get("flare_deployment", "gpt-image-2.5-flare")
            self.foundry["sunburst_deployment"] = foundry_data.get("sunburst_deployment", "gpt-image-2.5-sunburst")

            model_data = data.get("model", {})
            variant = model_data.get("variant", self.DEFAULT_VARIANT)
            self.model["variant"] = variant if variant in ("flare", "sunburst") else self.DEFAULT_VARIANT

            if "size" in model_data:
                self.model["size"] = model_data["size"]
            else:
                self.model["size"] = model_data.get("gptimage1", {}).get("size", self.DEFAULT_SIZE)

            if "quality" in model_data:
                quality = model_data["quality"]
            else:
                quality = model_data.get("gptimage1", {}).get("quality", self.DEFAULT_QUALITY)
            self.model["quality"] = quality if quality in ("low", "medium", "high", "xhigh", "max", "auto") else self.DEFAULT_QUALITY

            self.system["window_width"] = data.get("system", {}).get("window_width", 1024)
            self.system["window_height"] = data.get("system", {}).get("window_height", 800)
            self.system["welcome_title"] = data.get("system", {}).get("welcome_title", "Welcome")
            welcome_message = data.get("system", {}).get("welcome_message", self.DEFAULT_WELCOME_MESSAGE)
            self.system["welcome_message"] = self.DEFAULT_WELCOME_MESSAGE if welcome_message == self.LEGACY_WELCOME_MESSAGE else welcome_message

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
