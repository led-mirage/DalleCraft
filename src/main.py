# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import sys
import time

import webview

from app_const import APP_NAME, APP_VERSION, CONFIG_FILE
from app_window import AppWindow
from config import Config
from session import SessionManager
from services.api import Api
from services.app_service import AppService
from services.index_service import IndexService
from services.config_service import ConfigService

if getattr(sys, "frozen", False):
    import pyi_splash # type: ignore


class Application:
    def __init__(self):
        self._window = None
        self.app_window = AppWindow()
        self.config = Config(CONFIG_FILE)
        self.session_manager = SessionManager()
        self.app_service = AppService(self.config)
        self.index_service = IndexService(self.app_window, self.config, self.session_manager)
        self.config_service = ConfigService(self.app_window, self.config)
        self.api = Api(self.app_service, self.index_service, self.config_service)

    def start(self):
        window_title = f"{APP_NAME}  ver {APP_VERSION}"
        width = self.config.system["window_width"]
        height = self.config.system["window_height"]
        self._window = webview.create_window(window_title, url="html/index.html", js_api=self.api, text_select=True, width=width, height=height)
        self.app_window.set_raw_window(self._window)
        self.session_manager.create_new_session()
        webview.start(debug=False)
        session = self.session_manager.get_current_session()
        self.app_window.set_window_title(session.logfile_name)


if __name__ == '__main__':
    if getattr(sys, "frozen", False):
        time.sleep(2)
        pyi_splash.close()

    app = Application()
    app.start()
