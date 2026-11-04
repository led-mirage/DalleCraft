# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import os
from datetime import datetime

from session import SessionEntry

LOG_DIR = "logs"
LOG_FILENAME = "image_generation.log"


class ImageGenerationLogger:

    @classmethod
    def log(cls, entry: SessionEntry):
        log_path = os.path.join(LOG_DIR, LOG_FILENAME)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        success_flag = "Success" if entry.success else "Failure"
        generation_mode = "edit" if entry.input_images else "generate"
        if entry.input_images:
            input_filename = ",".join(
                input_image.get("filename", "")
                for input_image in entry.input_images
            )
            original_size = ",".join(
                cls._format_dimensions(
                    input_image.get("original_width"),
                    input_image.get("original_height"),
                )
                for input_image in entry.input_images
            )
            sent_size = ",".join(
                cls._format_dimensions(
                    input_image.get("width"),
                    input_image.get("height"),
                )
                for input_image in entry.input_images
            )
            original_bytes = ",".join(
                str(input_image.get("original_size_bytes", "-"))
                for input_image in entry.input_images
            )
            sent_bytes = ",".join(
                str(input_image.get("size_bytes", "-"))
                for input_image in entry.input_images
            )
            resized = ",".join(
                str(input_image.get("resized", False)).lower()
                for input_image in entry.input_images
            )
        else:
            input_filename = "-"
            original_size = "-"
            sent_size = "-"
            original_bytes = "-"
            sent_bytes = "-"
            resized = "-"

        log_entry = (
            f"{timestamp}\t{success_flag}\t{entry.image_size}\t{entry.image_quality}\t"
            f"{entry.elapsed_time:.2f}\t{entry.image_filename}\t{generation_mode}\t"
            f"{input_filename}\t{original_size}\t{sent_size}\t{original_bytes}\t"
            f"{sent_bytes}\t{resized}\n"
        )

        with open(log_path, "a") as logfile:
            logfile.write(log_entry)

    @staticmethod
    def _format_dimensions(width, height):
        if width is None or height is None:
            return "-"
        return f"{width}x{height}"
