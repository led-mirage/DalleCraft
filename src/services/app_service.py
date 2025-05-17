# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

from app_const import APP_NAME, APP_VERSION, COPYRIGHT
from config import Config


class AppService:
    def __init__(self, config: Config):
        self.config = config

    # --------------------------------------------------------------------------
    # JavaScriptから呼び出されるAPI群
    # --------------------------------------------------------------------------

    def api_get_app_info(self):
        return {
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "copyright": COPYRIGHT
        }

    def api_get_config(self) -> dict:
        return self.config.to_dict()
