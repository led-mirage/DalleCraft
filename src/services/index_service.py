# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import base64
import binascii
import io
import json
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime

import openai
from PIL import Image, ImageOps, UnidentifiedImageError

from app_const import APP_NAME, CONFIG_FILE, IMAGE_DIR, PRICING_FILE
from app_window import AppWindow
from config import Config
from dalle import GPTImageClient
from image_clipboard import copy_image_to_clipboard
from session import LOG_DIR, SessionManager, SessionEntry, Session
from generation_logger import ImageGenerationLogger
from image_options import normalize_image_size
from pricing import PricingConfig

INPUT_IMAGE_DIR = os.path.join(LOG_DIR, "input-images")


class IndexService:
    MAX_INPUT_IMAGES = 2
    MAX_INPUT_IMAGE_BYTES = 20 * 1024 * 1024
    MAX_INPUT_IMAGE_EDGE = 2048
    INPUT_IMAGE_FORMATS = {
        "PNG": (".png", "image/png"),
        "JPEG": (".jpg", "image/jpeg"),
        "WEBP": (".webp", "image/webp"),
    }
    VALID_IMAGE_QUALITIES = {
        "auto",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
    }

    def __init__(
        self,
        window: AppWindow,
        config: Config,
        session_manager: SessionManager,
        pricing: PricingConfig | None = None,
    ):
        self.window = window
        self.config = config
        self.session_manager = session_manager
        if pricing is None:
            try:
                pricing = PricingConfig(PRICING_FILE)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                print(f"料金設定ファイルの読み込みエラー: {error}")
                pricing = PricingConfig()
        self.pricing = pricing
        self._input_image_temp_dir = tempfile.TemporaryDirectory(prefix="dallecraft-input-")
        self._pending_input_images: dict[str, dict] = {}

    def close(self):
        for input_image_id in list(self._pending_input_images):
            self.release_input_image(input_image_id)
        self._input_image_temp_dir.cleanup()

    def gen_image(
        self,
        prompt: str,
        size: str | None = None,
        quality: str | None = None,
        input_image_paths: list[str] | None = None,
    ) -> tuple[str, str, float, dict]:
        start_time = time.time()
        image_client = self.create_image_client()

        configured_size, configured_quality = self.config.get_model_param()
        size = configured_size if size is None else size
        quality = configured_quality if quality is None else quality
        if input_image_paths:
            image_b64, revised_prompt, token_usage = image_client.edit_image(
                prompt,
                input_image_paths,
                size=size,
                quality=quality,
            )
        else:
            image_b64, revised_prompt, token_usage = image_client.gen_image(
                prompt,
                size=size,
                quality=quality,
            )

        elapsed_time = time.time() - start_time
        return image_b64, revised_prompt, elapsed_time, token_usage

    def resolve_generation_options(self, options: dict | None = None) -> tuple[str, str]:
        configured_size, configured_quality = self.config.get_model_param()
        if options is None:
            options = {}
        elif not isinstance(options, dict):
            raise ValueError("生成オプションの形式が正しくありません。")

        size = options.get("size", configured_size)
        quality = options.get("quality", configured_quality)
        normalized_size = normalize_image_size(size)
        if normalized_size is None:
            raise ValueError(f"未対応の解像度です: {size}")
        if quality not in self.VALID_IMAGE_QUALITIES:
            raise ValueError(f"未対応の品質です: {quality}")
        return normalized_size, quality

    def update_generation_options(self, size: str, quality: str) -> bool:
        if self.config.get_model_param() == (size, quality):
            return False
        self.config.model["size"] = size
        if size not in self.config.model["size_presets"]:
            self.config.model["size_presets"].append(size)
        self.config.model["quality"] = quality
        self.config.save(CONFIG_FILE)
        return True

    def normalize_input_image(self, image_bytes: bytes) -> dict:
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                image_format = image.format
                image.verify()

            if image_format not in self.INPUT_IMAGE_FORMATS:
                raise ValueError("PNG、JPEG、WebP形式の画像を貼り付けてください。")

            with Image.open(io.BytesIO(image_bytes)) as image:
                normalized_image = ImageOps.exif_transpose(image)
                original_width, original_height = normalized_image.size
                resized = max(original_width, original_height) > self.MAX_INPUT_IMAGE_EDGE

                if resized:
                    normalized_image.thumbnail(
                        (self.MAX_INPUT_IMAGE_EDGE, self.MAX_INPUT_IMAGE_EDGE),
                        Image.Resampling.LANCZOS,
                    )
                    output = io.BytesIO()
                    if image_format == "JPEG":
                        if normalized_image.mode not in ("RGB", "L"):
                            normalized_image = normalized_image.convert("RGB")
                        normalized_image.save(
                            output,
                            format="JPEG",
                            quality=90,
                            optimize=True,
                        )
                    elif image_format == "WEBP":
                        normalized_image.save(
                            output,
                            format="WEBP",
                            quality=90,
                            method=4,
                        )
                    else:
                        normalized_image.save(output, format="PNG", optimize=True)
                    normalized_bytes = output.getvalue()
                else:
                    normalized_bytes = image_bytes

                width, height = normalized_image.size
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError) as e:
            if isinstance(e, ValueError) and str(e).startswith("PNG、JPEG、WebP"):
                raise
            raise ValueError("PNG、JPEG、WebP形式の画像を貼り付けてください。") from e

        return {
            "image_bytes": normalized_bytes,
            "image_format": image_format,
            "original_width": original_width,
            "original_height": original_height,
            "width": width,
            "height": height,
            "original_size_bytes": len(image_bytes),
            "size_bytes": len(normalized_bytes),
            "resized": resized,
        }

    def register_input_image(self, image_data: dict) -> dict:
        if not isinstance(image_data, dict):
            raise ValueError("貼り付け画像の形式が正しくありません。")

        encoded_image = image_data.get("image_base64", "")
        if not isinstance(encoded_image, str) or not encoded_image:
            raise ValueError("貼り付け画像のデータがありません。")
        if encoded_image.startswith("data:"):
            try:
                encoded_image = encoded_image.split(",", 1)[1]
            except IndexError as e:
                raise ValueError("貼り付け画像のデータが正しくありません。") from e

        try:
            image_bytes = base64.b64decode(encoded_image, validate=True)
        except (binascii.Error, ValueError) as e:
            raise ValueError("貼り付け画像を読み込めませんでした。") from e

        if len(image_bytes) >= self.MAX_INPUT_IMAGE_BYTES:
            raise ValueError("貼り付け画像は20MB未満にしてください。")

        normalized = self.normalize_input_image(image_bytes)
        image_bytes = normalized["image_bytes"]
        image_format = normalized["image_format"]

        extension, mime_type = self.INPUT_IMAGE_FORMATS[image_format]
        input_image_id = uuid.uuid4().hex
        temp_path = os.path.join(
            self._input_image_temp_dir.name,
            f"{input_image_id}{extension}",
        )
        with open(temp_path, "wb") as image_file:
            image_file.write(image_bytes)

        try:
            preview_base64 = self.create_image_preview_base64(temp_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

        source = image_data.get("source", "clipboard")
        if source not in ("clipboard", "drop", "generated"):
            source = "clipboard"
        default_name = f"pasted-image{extension}"
        original_name = os.path.basename(image_data.get("filename") or default_name)
        pending_image = {
            "id": input_image_id,
            "path": temp_path,
            "original_name": original_name,
            "source": source,
            "mime_type": mime_type,
            "extension": extension,
            "original_width": normalized["original_width"],
            "original_height": normalized["original_height"],
            "width": normalized["width"],
            "height": normalized["height"],
            "original_size_bytes": normalized["original_size_bytes"],
            "size_bytes": normalized["size_bytes"],
            "resized": normalized["resized"],
        }
        self._pending_input_images[input_image_id] = pending_image

        result = {
            "success": True,
            "input_image_id": input_image_id,
            "filename": original_name,
            "source": source,
            "mime_type": mime_type,
            "preview_base64": preview_base64,
            "original_width": normalized["original_width"],
            "original_height": normalized["original_height"],
            "width": normalized["width"],
            "height": normalized["height"],
            "original_size_bytes": normalized["original_size_bytes"],
            "size_bytes": normalized["size_bytes"],
            "resized": normalized["resized"],
        }
        if normalized["resized"]:
            result["resize_message"] = (
                f"入力画像を {normalized['original_width']}×{normalized['original_height']} から "
                f"{normalized['width']}×{normalized['height']} に縮小しました。"
            )
        return result

    def release_input_image(self, input_image_id: str) -> bool:
        pending_image = self._pending_input_images.pop(input_image_id, None)
        if pending_image is None:
            return False
        image_path = pending_image["path"]
        if os.path.exists(image_path):
            os.remove(image_path)
        return True

    def resolve_input_images(self, options: dict | None) -> list[dict]:
        if not options:
            return []

        input_image_ids = options.get("input_image_ids")
        if input_image_ids is None:
            # 従来の単一画像リクエストとの互換性を維持する。
            legacy_input_image_id = options.get("input_image_id")
            input_image_ids = [legacy_input_image_id] if legacy_input_image_id else []

        if not isinstance(input_image_ids, list):
            raise ValueError("貼り付け画像のID一覧が正しくありません。")
        if len(input_image_ids) > self.MAX_INPUT_IMAGES:
            raise ValueError(f"入力画像は最大{self.MAX_INPUT_IMAGES}枚までです。")
        if any(
            not isinstance(input_image_id, str) or not input_image_id
            for input_image_id in input_image_ids
        ):
            raise ValueError("貼り付け画像のIDが正しくありません。")
        if len(set(input_image_ids)) != len(input_image_ids):
            raise ValueError("同じ入力画像が複数指定されています。")

        pending_images = []
        for input_image_id in input_image_ids:
            pending_image = self._pending_input_images.get(input_image_id)
            if pending_image is None or not os.path.exists(pending_image["path"]):
                raise ValueError("貼り付け画像が見つかりません。もう一度貼り付けてください。")
            pending_images.append(pending_image)
        return pending_images

    def create_image_preview_base64(self, image_path: str, max_size=(256, 256)) -> str:
        with Image.open(image_path) as image:
            preview = ImageOps.exif_transpose(image)
            preview.thumbnail(max_size, Image.Resampling.LANCZOS)
            if preview.mode not in ("RGB", "RGBA"):
                preview = preview.convert("RGBA")
            preview_buffer = io.BytesIO()
            preview.save(preview_buffer, format="PNG")
        return base64.b64encode(preview_buffer.getvalue()).decode("utf-8")

    def persist_input_image(self, pending_image: dict) -> dict:
        os.makedirs(INPUT_IMAGE_DIR, exist_ok=True)

        input_filename = f"input_image_{uuid.uuid4().hex}{pending_image['extension']}"
        input_path = os.path.join(INPUT_IMAGE_DIR, input_filename)
        shutil.copy2(pending_image["path"], input_path)

        thumbnail_filename = f"{os.path.splitext(input_filename)[0]}_thumbnail.png"
        thumbnail_path = os.path.join(INPUT_IMAGE_DIR, thumbnail_filename)
        thumbnail_data = base64.b64decode(self.create_image_preview_base64(input_path))
        with open(thumbnail_path, "wb") as thumbnail_file:
            thumbnail_file.write(thumbnail_data)

        return {
            "filename": input_filename,
            "thumbnail_filename": thumbnail_filename,
            "original_name": pending_image["original_name"],
            "source": pending_image["source"],
            "mime_type": pending_image["mime_type"],
            "original_width": pending_image["original_width"],
            "original_height": pending_image["original_height"],
            "width": pending_image["width"],
            "height": pending_image["height"],
            "original_size_bytes": pending_image["original_size_bytes"],
            "size_bytes": pending_image["size_bytes"],
            "resized": pending_image["resized"],
        }

    def get_stored_input_image_path(self, filename: str) -> str:
        if not filename:
            return ""
        input_path = os.path.join(INPUT_IMAGE_DIR, filename)
        if os.path.exists(input_path):
            return input_path

        # Compatibility with input images created before logs/input-images was used.
        legacy_path = os.path.join(IMAGE_DIR, filename)
        if os.path.exists(legacy_path):
            return legacy_path
        return input_path

    def add_input_image_previews(self, entry_dict: dict):
        for input_image in entry_dict.get("input_images", []):
            thumbnail_filename = input_image.get("thumbnail_filename", "")
            thumbnail_path = self.get_stored_input_image_path(thumbnail_filename)
            if thumbnail_filename and os.path.exists(thumbnail_path):
                with open(thumbnail_path, "rb") as image_file:
                    input_image["thumbnail_base64"] = base64.b64encode(
                        image_file.read()
                    ).decode("utf-8")

    def remove_managed_file(self, filename: str, directory: str = IMAGE_DIR):
        if not filename:
            return
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    def remove_entry_files(self, entry: SessionEntry):
        if entry.success:
            self.remove_managed_file(entry.image_filename)
            self.remove_managed_file(entry.thumbnail_filename)
        for input_image in entry.input_images:
            for filename in (
                input_image.get("filename", ""),
                input_image.get("thumbnail_filename", ""),
            ):
                self.remove_managed_file(filename, INPUT_IMAGE_DIR)
                self.remove_managed_file(filename, IMAGE_DIR)

    def create_image_client(self) -> GPTImageClient:
        model_name = self.config.get_model_name()
        if self.config.api_type == "openai":
            return GPTImageClient(
                api_key=os.environ[self.config.openai["api_key_envvar"]],
                model=model_name,
            )
        return GPTImageClient(
            api_key=os.environ[self.config.foundry["api_key_envvar"]],
            base_url=os.environ[self.config.foundry["endpoint_envvar"]],
            model=model_name,
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

    def refresh_view(self, session: Session):
        if session:
            self.window.evaluate_js("clearContents()")
            session_name = session.session_name if session.session_name else APP_NAME
            self.window.evaluate_js(f"setSessionName({json.dumps(session_name)})")
            for entry in session.entries:
                entry_dict = entry.to_dict()
                self.add_input_image_previews(entry_dict)
                if entry.success:
                    if entry.thumbnail_filename == "":
                        image_path = os.path.join(IMAGE_DIR, entry.image_filename)
                        thumbnail_path = self.save_resized_image(image_path)
                        entry.thumbnail_filename = os.path.basename(thumbnail_path)
                        session.save_to_file()

                    image_path = os.path.join(IMAGE_DIR, entry.thumbnail_filename)
                    with open(image_path, "rb") as image_file:
                        image_b64 = base64.b64encode(image_file.read()).decode("utf-8")
                        entry_dict["image_base64"] = image_b64
                self.window.evaluate_js(f"addEntry({json.dumps(entry_dict)})")
            self.window.evaluate_js(
                f"setSessionUsageHistory({json.dumps(session.get_usage_history())})"
            )

    # --------------------------------------------------------------------------
    # JavaScriptから呼び出されるAPI群
    # --------------------------------------------------------------------------

    def api_refresh_index_view(self):
        session = self.session_manager.get_current_session()
        if len(session.entries) > 0 or len(session.usage_history) > 0:
            self.refresh_view(session)

    def api_update_generation_options(self, options: dict) -> dict:
        try:
            image_size, image_quality = self.resolve_generation_options(options)
            self.update_generation_options(image_size, image_quality)
            return {
                "success": True,
                "size": image_size,
                "quality": image_quality,
            }
        except (TypeError, ValueError) as e:
            return {"success": False, "error_info": str(e)}

    def api_register_input_image(self, image_data: dict) -> dict:
        try:
            return self.register_input_image(image_data)
        except Exception as e:
            return {"success": False, "error_info": str(e)}

    def api_prepare_image_edit(self, entry_id: int) -> dict:
        try:
            session = self.session_manager.get_current_session()
            entry = session.find_entry(entry_id)
            if entry is None:
                return {
                    "success": False,
                    "error_info": "編集元の画像が見つかりません。",
                }

            image_filename = entry.image_filename
            if not image_filename:
                return {
                    "success": False,
                    "error_info": "編集元の画像ファイルが見つかりません。",
                }
            image_path = os.path.join(IMAGE_DIR, image_filename)
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error_info": "編集元の画像ファイルが見つかりません。",
                }

            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("ascii")

            return self.register_input_image({
                "filename": image_filename,
                "source": "generated",
                "mime_type": "image/png",
                "image_base64": image_base64,
            })
        except Exception as e:
            return {"success": False, "error_info": str(e)}

    def api_release_input_image(self, input_image_id: str) -> dict:
        return {"success": self.release_input_image(input_image_id)}

    def api_get_pending_input_image_base64(self, input_image_id: str) -> str:
        pending_image = self._pending_input_images.get(input_image_id)
        if pending_image is None:
            return ""
        image_path = pending_image["path"]
        if not os.path.exists(image_path):
            return ""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def api_gen_image(self, prompt: str, options: dict | None = None) -> dict:
        api_type = self.config.api_type
        model_name = self.config.get_model_name()
        image_size, image_quality = self.config.get_model_param()
        pending_input_images = []
        try:
            image_size, image_quality = self.resolve_generation_options(options)
            pending_input_images = self.resolve_input_images(options)
            if options is not None:
                self.update_generation_options(image_size, image_quality)
            image_b64, revised_prompt, elapsed_time, token_usage = self.gen_image(
                prompt,
                size=image_size,
                quality=image_quality,
                input_image_paths=[
                    pending_input_image["path"]
                    for pending_input_image in pending_input_images
                ] or None,
            )
            cost_estimate = self.pricing.estimate(
                api_type,
                model_name,
                token_usage,
            )
            image_path = self.save_image(image_b64)
            image_filename = os.path.basename(image_path)
            thumbnail_path = self.save_resized_image(image_path)
            thumbnail_filename = os.path.basename(thumbnail_path)
            input_images = [
                self.persist_input_image(pending_input_image)
                for pending_input_image in pending_input_images
            ]
            entry = SessionEntry(
                prompt,
                revised_prompt,
                api_type,
                model_name,
                image_size,
                image_quality,
                True,
                elapsed_time,
                image_filename,
                thumbnail_filename,
                input_images=input_images,
                token_usage=token_usage,
                cost_estimate=cost_estimate,
            )
            session = self.session_manager.get_current_session()
            session.add_entry(entry)
            session.save_to_file()
            ImageGenerationLogger.log(entry)
            entry_dict = entry.to_dict()
            entry_dict["image_base64"] = image_b64
            self.add_input_image_previews(entry_dict)
            for pending_input_image in pending_input_images:
                self.release_input_image(pending_input_image["id"])
            return entry_dict
        except openai.BadRequestError as e:
            input_images = []
            for pending_input_image in pending_input_images:
                try:
                    input_images.append(self.persist_input_image(pending_input_image))
                except OSError:
                    input_images.append({
                        "filename": "",
                        "thumbnail_filename": "",
                        "original_name": pending_input_image["original_name"],
                        "source": pending_input_image["source"],
                        "mime_type": pending_input_image["mime_type"],
                        "original_width": pending_input_image["original_width"],
                        "original_height": pending_input_image["original_height"],
                        "width": pending_input_image["width"],
                        "height": pending_input_image["height"],
                        "original_size_bytes": pending_input_image["original_size_bytes"],
                        "size_bytes": pending_input_image["size_bytes"],
                        "resized": pending_input_image["resized"],
                    })
            entry = SessionEntry(
                prompt,
                "",
                api_type,
                model_name,
                image_size,
                image_quality,
                False,
                0.0,
                "",
                "",
                str(e),
                input_images=input_images,
            )
            session = self.session_manager.get_current_session()
            session.add_entry(entry)
            session.save_to_file()
            ImageGenerationLogger.log(entry)
            entry_dict = entry.to_dict()
            self.add_input_image_previews(entry_dict)
            return entry_dict
        except KeyError as e:
            return {"error_info": f"環境変数 {e} が見つかりません。"}
        except Exception as e:
            return {"error_info": str(e)}

    def api_regenerate_image(self, entry_id: int, options: dict | None = None) -> dict:
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        if entry is None:
            return {"error_info": "再作成する画像が見つかりません。"}
        if options is not None and not isinstance(options, dict):
            return {"error_info": "生成オプションの形式が正しくありません。"}

        # 入力欄で準備中の参照画像は再作成リクエストへ混ぜない。
        regeneration_options = dict(options or {})
        regeneration_options.pop("input_image_id", None)
        regeneration_options.pop("input_image_ids", None)
        regenerated_input_ids = []
        try:
            if len(entry.input_images) > self.MAX_INPUT_IMAGES:
                return {"error_info": f"入力画像は最大{self.MAX_INPUT_IMAGES}枚までです。"}

            for input_image in entry.input_images:
                input_filename = input_image.get("filename", "")
                input_path = self.get_stored_input_image_path(input_filename)
                if not input_filename or not os.path.exists(input_path):
                    return {"error_info": "元の参照画像ファイルが見つかりません。"}

                with open(input_path, "rb") as image_file:
                    image_base64 = base64.b64encode(image_file.read()).decode("ascii")
                registered = self.register_input_image({
                    "filename": input_image.get("original_name") or input_filename,
                    "source": input_image.get("source", "clipboard"),
                    "mime_type": input_image.get("mime_type", "image/png"),
                    "image_base64": image_base64,
                })
                regenerated_input_ids.append(registered["input_image_id"])

            if regenerated_input_ids:
                regeneration_options["input_image_ids"] = regenerated_input_ids

            return self.api_gen_image(entry.prompt, regeneration_options)
        except Exception as e:
            return {"error_info": str(e)}
        finally:
            for regenerated_input_id in regenerated_input_ids:
                self.release_input_image(regenerated_input_id)

    def api_save_image(self, entry_id: int):
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        dst_path = self.window.open_file_dialog(entry.image_filename)
        if dst_path:
            src_path = os.path.join(IMAGE_DIR, entry.image_filename)
            shutil.copy2(src_path, dst_path)

    def api_copy_image(self, entry_id: int) -> dict:
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        if entry is None or not entry.image_filename:
            return {"success": False, "error_info": "コピーする画像が見つかりません。"}

        image_path = os.path.join(IMAGE_DIR, entry.image_filename)
        if not os.path.exists(image_path):
            return {"success": False, "error_info": "画像ファイルが見つかりません。"}

        try:
            copy_image_to_clipboard(image_path)
            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error_info": f"画像をクリップボードにコピーできませんでした。\n{e}",
            }

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

    def api_get_input_image_base64(self, entry_id: int, image_index: int = 0) -> str:
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        if entry is None or not 0 <= image_index < len(entry.input_images):
            return ""
        input_filename = entry.input_images[image_index].get("filename", "")
        input_path = self.get_stored_input_image_path(input_filename)
        if not input_filename or not os.path.exists(input_path):
            return ""
        with open(input_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def api_get_image_info(self, entry_id: int) -> dict:
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        return entry.to_dict()

    def api_prev_session(self):
        session = self.session_manager.previous_session()
        if session:
            self.window.set_window_title(session.logfile_name)
            self.refresh_view(session)

    def api_next_session(self):
        session = self.session_manager.next_session()
        if session:
            self.window.set_window_title(session.logfile_name)
            self.refresh_view(session)

    def api_new_session(self):
        session = self.session_manager.create_new_session()
        if session:
            self.window.set_window_title(session.logfile_name)
            self.refresh_view(session)

    def api_delete_entry(self, entry_id: int):
        session = self.session_manager.get_current_session()
        entry = session.find_entry(entry_id)
        if entry:
            self.remove_entry_files(entry)
        session.remove_entry(entry_id)
        session.save_to_file()

    def api_delete_current_session(self):
        session = self.session_manager.get_current_session()
        for entry in session.entries:
            self.remove_entry_files(entry)
        session = self.session_manager.delete_current_session()
        self.refresh_view(session)

    def api_set_session_name(self, session_name: str):
        session = self.session_manager.get_current_session()
        if session:
            session.session_name = session_name
            session.save_to_file()
