# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

from app_window import AppWindow
from config import Config

CONFIG_FILE = "config.json"


class ConfigService:
    def __init__(self, window: AppWindow, config: Config):
        self.window = window
        self.config = config

    # --------------------------------------------------------------------------
    # JavaScriptから呼び出されるAPI群
    # --------------------------------------------------------------------------

    def api_open_config(self):
        return self.window.open_config_view()

    def api_cancel_config(self):
        self.window.open_index_view()

    def api_submit_config(self, config_dict: dict):
        self.config.api_type = config_dict["apiType"]
        self.config.openai["api_key_envvar"] = config_dict["openai"]["api_key_envvar"]
        self.config.openai["model_name"] = config_dict["openai"]["model_name"]
        self.config.azure["api_key_envvar"] = config_dict["azure"]["api_key_envvar"]
        self.config.azure["endpoint_envvar"] = config_dict["azure"]["endpoint_envvar"]
        self.config.azure["model_name"] = config_dict["azure"]["model_name"]
        self.config.model["model_type"] = config_dict["model"]["model_type"]
        self.config.model["dalle2"]["size"] = config_dict["model"]["dalle2"]["size"]
        self.config.model["dalle3"]["size"] = config_dict["model"]["dalle3"]["size"]
        self.config.model["dalle3"]["quality"] = config_dict["model"]["dalle3"]["quality"]
        self.config.save(CONFIG_FILE)
        self.window.open_index_view()
