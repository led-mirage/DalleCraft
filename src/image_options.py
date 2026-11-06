# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import re


DEFAULT_IMAGE_SIZE_PRESETS = (
    "auto",
    "1024x1024",
    "1536x1024",
    "1024x1536",
    "1792x1008",
    "1008x1792",
    "1920x1280",
    "1280x1920",
    "2048x1152",
    "1152x2048",
)

MIN_IMAGE_PIXELS = 655_360
MAX_IMAGE_PIXELS = 8_294_400
MAX_IMAGE_EDGE = 3840

_IMAGE_SIZE_PATTERN = re.compile(r"^(\d+)x(\d+)$")


def normalize_image_size(value) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = "".join(value.strip().lower().replace("×", "x").split())
    if normalized == "auto":
        return normalized

    match = _IMAGE_SIZE_PATTERN.fullmatch(normalized)
    if match is None:
        return None

    width, height = map(int, match.groups())
    if width % 16 != 0 or height % 16 != 0:
        return None
    if max(width, height) > MAX_IMAGE_EDGE:
        return None
    if max(width, height) > min(width, height) * 3:
        return None

    pixels = width * height
    if not MIN_IMAGE_PIXELS <= pixels <= MAX_IMAGE_PIXELS:
        return None
    return normalized


def normalize_image_size_presets(values) -> list[str]:
    if not isinstance(values, (list, tuple)):
        values = DEFAULT_IMAGE_SIZE_PRESETS

    presets = []
    for value in values:
        normalized = normalize_image_size(value)
        if normalized is not None and normalized not in presets:
            presets.append(normalized)
    return presets or ["auto"]
