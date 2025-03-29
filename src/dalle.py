# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

from openai import OpenAI
from openai import AzureOpenAI

DALLE2_IMAGE_SIZE1 = "256x256"
DALLE2_IMAGE_SIZE2 = "512x512"
DALLE2_IMAGE_SIZE3 = "1024x1024"

DALLE3_IMAGE_SIZE1 = "1024x1024"
DALLE3_IMAGE_SIZE2 = "1792x1024"
DALLE3_IMAGE_SIZE3 = "1024x1792"

DALLE3_QUALITY_STANDARD = "standard"
DALLE3_QUALITY_HD = "hd"


class DalleOpenAI:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def gen_image(self, prompt: str, size: str = DALLE3_IMAGE_SIZE1, quality: str = DALLE3_QUALITY_STANDARD) -> tuple[str, str]:
        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
            response_format="b64_json"
        )
        return response.data[0].b64_json, response.data[0].revised_prompt


class DalleAzure:
    def __init__(self, api_key: str, endpoint: str, model: str):
        self.model = model
        self.client = AzureOpenAI(
            api_version="2024-02-01",
            api_key=api_key,
            azure_endpoint=endpoint
        )

    def gen_image(self, prompt: str, size: str = DALLE3_IMAGE_SIZE1, quality: str = DALLE3_QUALITY_STANDARD) -> tuple[str, str]:
        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
            response_format="b64_json"
        )
        return response.data[0].b64_json, response.data[0].revised_prompt
