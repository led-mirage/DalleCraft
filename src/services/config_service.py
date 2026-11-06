# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

from app_window import AppWindow
from config import Config
from image_options import normalize_image_size

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
        self.config.foundry["api_key_envvar"] = config_dict["foundry"]["api_key_envvar"]
        self.config.foundry["endpoint_envvar"] = config_dict["foundry"]["endpoint_envvar"]
        self.config.foundry["flare_deployment"] = config_dict["foundry"]["flare_deployment"]
        self.config.foundry["sunburst_deployment"] = config_dict["foundry"]["sunburst_deployment"]
        self.config.model["variant"] = config_dict["model"]["variant"]
        size = normalize_image_size(config_dict["model"]["size"])
        if size is None:
            raise ValueError(f"未対応の解像度です: {config_dict['model']['size']}")
        self.config.model["size"] = size
        if size not in self.config.model["size_presets"]:
            self.config.model["size_presets"].append(size)
        self.config.model["quality"] = config_dict["model"]["quality"]
        self.config.save(CONFIG_FILE)
        self.window.open_index_view()
