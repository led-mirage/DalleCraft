# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import webview

from app_const import APP_NAME, APP_VERSION


class AppWindow:
    def __init__(self):
        self._window: webview.Window = None

    def set_raw_window(self, window: webview.Window):
        self._window = window

    def set_window_title(self, logfile_name: str):
        window_title = f"{APP_NAME}  ver {APP_VERSION} - {logfile_name}"
        self._window.set_title(window_title)

    def open_file_dialog(self, filename: str) -> str:
        file_types = ('Image Files (*.png)', 'All files (*.*)')
        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG, directory='/', file_types=file_types, save_filename=filename
        )
        return result
    
    def evaluate_js(self, js: str):
        return self._window.evaluate_js(js)

    def open_index_view(self):
        self._window.load_url("html/index.html")

    def open_config_view(self):
        self._window.load_url("html/config.html")
