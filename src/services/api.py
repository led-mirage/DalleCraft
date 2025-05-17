# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app_service import AppService
    from index_service import IndexService
    from config_service import ConfigService


class Api:
    def __init__(self, app_service: "AppService", index_service: "IndexService", config_service: "ConfigService"):
        self.app_service = app_service
        self.index_service = index_service
        self.config_service = config_service

    # --------------------------------------------------------------------------
    # AppService
    # --------------------------------------------------------------------------

    def api_get_app_info(self):
        return self.app_service.api_get_app_info()

    def api_get_config(self) -> dict:
        return self.app_service.api_get_config()

    # --------------------------------------------------------------------------
    # IndexService
    # --------------------------------------------------------------------------

    def api_refresh_index_view(self):
        return self.index_service.api_refresh_index_view()

    def api_gen_image(self, prompt: str) -> dict:
        return self.index_service.api_gen_image(prompt)

    def api_save_image(self, entry_id: int):
        return self.index_service.api_save_image(entry_id)

    def api_get_image_base64(self, entry_id: int) -> str:
        return self.index_service.api_get_image_base64(entry_id)

    def api_get_image_info(self, entry_id: int) -> dict:
        return self.index_service.api_get_image_info(entry_id)

    def api_prev_session(self):
        return self.index_service.api_prev_session()

    def api_next_session(self):
        return self.index_service.api_next_session()

    def api_new_session(self):
        return self.index_service.api_new_session()

    def api_delete_entry(self, entry_id: int):
        return self.index_service.api_delete_entry(entry_id)

    def api_delete_current_session(self):
        return self.index_service.api_delete_current_session()

    def api_set_session_name(self, session_name: str):
        return self.index_service.api_set_session_name(session_name)

    # --------------------------------------------------------------------------
    # ConfigService
    # --------------------------------------------------------------------------

    def api_open_config(self):
        return self.config_service.api_open_config()

    def api_cancel_config(self):
        return self.config_service.api_cancel_config()

    def api_submit_config(self, config_dict: dict):
        return self.config_service.api_submit_config(config_dict)
