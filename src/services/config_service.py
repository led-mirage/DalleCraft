# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

from app_window import AppWindow
from config import Config
from image_options import normalize_image_size
from model_options import SUPPORTED_COMPLEXITIES, SUPPORTED_MODEL_IDS

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
        api_type = config_dict["apiType"]
        if api_type not in ("openai", "foundry"):
            raise ValueError(f"未対応のAPI種別です: {api_type}")

        deployments = config_dict["foundry"].get("deployments", {})
        normalized_deployments = {
            model_id: str(deployments.get(model_id, "")).strip()
            for model_id in SUPPORTED_MODEL_IDS
        }

        model_id = config_dict["model"]["id"]
        if model_id not in SUPPORTED_MODEL_IDS:
            raise ValueError(f"未対応のモデルです: {model_id}")
        if api_type == "foundry" and not normalized_deployments[model_id]:
            raise ValueError(f"{model_id}のFoundryデプロイ名を入力してください。")

        size = normalize_image_size(config_dict["model"]["size"])
        if size is None:
            raise ValueError(f"未対応の解像度です: {config_dict['model']['size']}")
        quality = config_dict["model"]["quality"]
        if quality not in ("low", "medium", "high", "xhigh", "max", "auto"):
            raise ValueError(f"未対応の品質です: {quality}")
        complexity = config_dict["model"]["complexity"]
        if complexity not in SUPPORTED_COMPLEXITIES:
            raise ValueError(f"未対応の計画量です: {complexity}")

        self.config.api_type = api_type
        self.config.openai["api_key_envvar"] = config_dict["openai"]["api_key_envvar"]
        self.config.foundry["api_key_envvar"] = config_dict["foundry"]["api_key_envvar"]
        self.config.foundry["endpoint_envvar"] = config_dict["foundry"]["endpoint_envvar"]
        self.config.foundry["deployments"] = normalized_deployments
        self.config.model["id"] = model_id
        self.config.model["size"] = size
        if size not in self.config.model["size_presets"]:
            self.config.model["size_presets"].append(size)
        self.config.model["quality"] = quality
        self.config.model["complexity"] = complexity
        self.config.save(CONFIG_FILE)
        self.window.open_index_view()
