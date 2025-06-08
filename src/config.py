# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import json


class Config:
    FILE_VERSION = "2.0"

    def __init__(self, config_path=None):
        self.version = None
        self.api_type = None
        self.openai = {
            "api_key_envvar": None,
            "model_name": None
        }
        self.azure = {
            "api_key_envvar": None,
            "endpoint_envvar": None,
            "model_name": None
        }
        self.model = {
            "model_type": None,
            "dalle2": {
                "size": None,
            },
            "dalle3": {
                "size": None,
                "quality": None
            },
            "gptimage1": {
                "size": None,
                "quality": None
            }
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
        if self.model["model_type"] == "dalle3":
            return self.model["dalle3"]["size"], self.model["dalle3"]["quality"]
        elif self.model["model_type"] == "dalle2":
            return self.model["dalle2"]["size"], "standard"
        else:
            return None, None

    def load(self, config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.version = data.get("version", None)
            self.api_type = data.get("api_type", "openai")
            self.openai["api_key_envvar"] = data.get("openai", {}).get("api_key_envvar", "OPENAI_API_KEY")
            self.openai["model_name"] = data.get("openai", {}).get("model_name", "dall-e-3")
            self.azure["api_key_envvar"] = data.get("azure", {}).get("api_key_envvar", "AZURE_OPENAI_API_KEY")
            self.azure["endpoint_envvar"] = data.get("azure", {}).get("endpoint_envvar", "AZURE_OPENAI_ENDPOINT")
            self.azure["model_name"] = data.get("azure", {}).get("model_name", "dall-e-3")
            self.model["model_type"] = data.get("model", {}).get("model_type", "dalle3")
            self.model["dalle2"]["size"] = data.get("model", {}).get("dalle2", {}).get("size", "1024x1024")
            self.model["dalle3"]["size"] = data.get("model", {}).get("dalle3", {}).get("size", "1792x1024")
            self.model["dalle3"]["quality"] = data.get("model", {}).get("dalle3", {}).get("quality", "standard")
            self.model["gptimage1"]["size"] = data.get("model", {}).get("gptimage1", {}).get("size", "1536x1024")
            self.model["gptimage1"]["quality"] = data.get("model", {}).get("gptimage1", {}).get("quality", "low")
            self.system["window_width"] = data.get("system", {}).get("window_width", 1024)
            self.system["window_height"] = data.get("system", {}).get("window_height", 800)
            self.system["welcome_title"] = data.get("system", {}).get("welcome_title", "Welcome")
            self.system["welcome_message"] = data.get("system", {}).get("welcome_message", "DalleCraft is a tool for generating images using DALL-E3.")

    def save(self, config_path):
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    def to_dict(self):
        return {
            "version": self.FILE_VERSION,
            "api_type": self.api_type,
            "openai": self.openai,
            "azure": self.azure,
            "model": self.model,
            "system": self.system
        }
