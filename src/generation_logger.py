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
        log_entry = f"{timestamp}\t{success_flag}\t{entry.image_size}\t{entry.image_quality}\t{entry.elapsed_time:.2f}\t{entry.image_filename}\n"

        with open(log_path, "a") as logfile:
            logfile.write(log_entry)
