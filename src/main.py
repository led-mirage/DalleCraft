# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import base64
import json
import os
import shutil
import sys
import time
from datetime import datetime

import openai
import webview
from PIL import Image

from config import Config
from dalle import DalleAzure, DalleOpenAI
from generation_logger import ImageGenerationLogger
from session import SessionManager, Session, SessionEntry

if getattr(sys, "frozen", False):
    import pyi_splash # type: ignore

APP_NAME = "DalleCraft"
APP_VERSION = "1.0.0"
COPYRIGHT = "Copyright 2025 led-mirage"

IMAGE_DIR = "images"
CONFIG_FILE = "config.json"


class Application:
    def __init__(self):
        self._window = None
        self.config = Config(CONFIG_FILE)
        self.session_manager = SessionManager()

    def start(self):
        window_title = f"{APP_NAME}  ver {APP_VERSION}"
        width = self.config.system["window_width"]
        height = self.config.system["window_height"]
        self._window = webview.create_window(window_title, url="html/index.html", js_api=self, text_select=True, width=width, height=height)
        self.session_manager.create_new_session()
        webview.start(debug=False)
        self.set_window_title()

    def set_window_title(self):
        session = self.session_manager.get_current_session()
        window_title = f"{APP_NAME}  ver {APP_VERSION} - {session.logfile_name}"
        self._window.set_title(window_title)

    def gen_image(self, prompt: str) -> tuple[str, str, float]:
        start_time = time.time()
        dalle3 = self.create_dalle_client()

        size, quality = self.config.get_model_param()
        image_b64, revised_prompt = dalle3.gen_image(prompt, size=size, quality=quality)

        elapsed_time = time.time() - start_time
        return image_b64, revised_prompt, elapsed_time

    def create_dalle_client(self) -> DalleOpenAI | DalleAzure:
        if self.config.api_type == "openai":
            return DalleOpenAI(
                api_key=os.environ[self.config.openai["api_key_envvar"]],
                model=self.config.openai["model_name"]
            )
        else:
            return DalleAzure(
                api_key=os.environ[self.config.azure["api_key_envvar"]],
                endpoint=os.environ[self.config.azure["endpoint_envvar"]],
                model=self.config.azure["model_name"]
            )

    def save_image(self, image_b64: str) -> str:
        if not os.path.isdir(IMAGE_DIR):
            os.mkdir(IMAGE_DIR)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(IMAGE_DIR, f'generated_image_{timestamp}.png')

        generated_image = base64.b64decode(image_b64)
        with open(image_path, "wb") as image_file:
            image_file.write(generated_image)

        return image_path

    def save_resized_image(self, image_path: str, ratio:float = 0.5) -> str:
        img = Image.open(image_path)

        width, height = img.size
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        resized_img = img.resize((new_width, new_height))

        file_name, file_ext = os.path.splitext(image_path)
        new_file_path = f"{file_name}_thumbnail{file_ext}"

        resized_img.save(new_file_path)
        return new_file_path

    def open_file_dialog(self, window, filename: str) -> str:
        file_types = ('Image Files (*.png)', 'All files (*.*)')
        result = window.create_file_dialog(
            webview.SAVE_DIALOG, directory='/', file_types=file_types, save_filename=filename
        )
        return result

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

    def api_gen_image(self, prompt: str) -> dict:
        api_type = self.config.api_type
        model_name = self.config.openai["model_name"] if api_type == "openai" else self.config.azure["model_name"]
        try:
            image_b64, revised_prompt, elapsed_time = self.gen_image(prompt)
            image_path = self.save_image(image_b64)
            image_filename = os.path.basename(image_path)
            image_size, image_quality = self.config.get_model_param()
            thumbnail_path = self.save_resized_image(image_path)
            thumbnail_filename = os.path.basename(thumbnail_path)
            entry = SessionEntry(prompt, revised_prompt, api_type, model_name, image_size, image_quality, True, elapsed_time, image_filename, thumbnail_filename)
            session = self.session_manager.get_current_session()
            session.add_entry(entry)
            session.save_to_file()
            ImageGenerationLogger.log(entry)
            dict = entry.to_dict()
            dict["image_base64"] = image_b64
            return dict
        except openai.BadRequestError as e:
            image_size, image_quality = self.config.get_model_param()
            entry = SessionEntry(prompt, "", api_type, model_name, image_size, image_quality, False, 0.0, "", "", e.message)
            session = self.session_manager.get_current_session()
            session.add_entry(entry)
            session.save_to_file()
            ImageGenerationLogger.log(entry)
            return entry.to_dict()
        except KeyError as e:
            return {"error_info": f"環境変数 {e} が見つかりません。"}
        except Exception as e:
            return {"error_info": str(e)}

    def api_save_image(self, entry_id: int):
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        dst_path = self.open_file_dialog(self._window, entry.image_filename)
        if dst_path:
            src_path = os.path.join(IMAGE_DIR, entry.image_filename)
            shutil.copy2(src_path, dst_path)

    def api_get_image_base64(self, entry_id: int) -> str:
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        image_path = os.path.join(IMAGE_DIR, entry.image_filename)
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                image_b64 = base64.b64encode(image_file.read()).decode("utf-8")
                return image_b64
        else:
            return ""

    def api_get_image_info(self, entry_id: int) -> dict:
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        return entry.to_dict()

    def api_prev_session(self):
        session = self.session_manager.previous_session()
        self.set_window_title()
        self.refresh_view(session)

    def api_next_session(self):
        session = self.session_manager.next_session()
        self.set_window_title()
        self.refresh_view(session)

    def api_new_session(self):
        session = self.session_manager.create_new_session()
        self.set_window_title()
        self.refresh_view(session)

    def api_delete_entry(self, entry_id: int):
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        if entry and entry.success:
            image_path = os.path.join(IMAGE_DIR, entry.image_filename)
            thumbnail_path = os.path.join(IMAGE_DIR, entry.thumbnail_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        session.remove_entry(entry_id)
        session.save_to_file()

    def api_delete_current_session(self):
        session = self.session_manager.get_current_session()
        for entry in session.entries:
            if entry.success:
                image_path = os.path.join(IMAGE_DIR, entry.image_filename)
                thumbnail_path = os.path.join(IMAGE_DIR, entry.thumbnail_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
        session = self.session_manager.delete_current_session()
        self.refresh_view(session)

    def api_set_session_name(self, session_name: str):
        session = self.session_manager.get_current_session()
        session.session_name = session_name
        session.save_to_file()

    def api_open_config(self):
        self._window.load_url("html/config.html")

    def api_cancel_config(self):
        self._window.load_url("html/index.html")
        session = self.session_manager.get_current_session()
        self.refresh_view(session)

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
        self._window.load_url("html/index.html")
        session = self.session_manager.get_current_session()
        self.refresh_view(session)

    def refresh_view(self, session: Session):
        if session:
            self._window.evaluate_js("clearContents()")
            session_name = session.session_name if session.session_name else APP_NAME
            self._window.evaluate_js(f"setSessionName('{session_name}')")
            for entry in session.entries:
                dict = entry.to_dict()
                if entry.success:
                    if entry.thumbnail_filename == "":
                        image_path = os.path.join(IMAGE_DIR, entry.image_filename)
                        thumbnail_path = self.save_resized_image(image_path)
                        entry.thumbnail_filename = os.path.basename(thumbnail_path)
                        session.save_to_file()

                    image_path = os.path.join(IMAGE_DIR, entry.thumbnail_filename)
                    with open(image_path, "rb") as image_file:
                        image_b64 = base64.b64encode(image_file.read()).decode("utf-8")
                        dict["image_base64"] = image_b64
                self._window.evaluate_js(f"addEntry({json.dumps(dict)})")


if __name__ == '__main__':
    if getattr(sys, "frozen", False):
        time.sleep(2)
        pyi_splash.close()

    app = Application()
    app.start()
