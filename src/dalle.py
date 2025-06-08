# DalleCraft
#
# Copyright (c) 2025 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

from openai import OpenAI
from openai import AzureOpenAI

MODEL_TYPE_DALLE2 = "dalle2"
MODEL_TYPE_DALLE3 = "dalle3"
MODEL_TYPE_GPTIMAGE1 = "gptimage1"

DALLE2_IMAGE_SIZE1 = "256x256"
DALLE2_IMAGE_SIZE2 = "512x512"
DALLE2_IMAGE_SIZE3 = "1024x1024"

DALLE3_IMAGE_SIZE1 = "1024x1024"
DALLE3_IMAGE_SIZE2 = "1792x1024"
DALLE3_IMAGE_SIZE3 = "1024x1792"

DALLE3_QUALITY_STANDARD = "standard"
DALLE3_QUALITY_HD = "hd"

GPTIMAGE1_IMAGE_SIZE1 = "1024x1024"
GPTIMAGE1_IMAGE_SIZE2 = "1536x1024"
GPTIMAGE1_IMAGE_SIZE3 = "1024x1536"
GPTIMAGE1_IMAGE_SIZE4 = "auto"

GPTIMAGE1_QUALITY_LOW = "low"
GPTIMAGE1_QUALITY_MEDIUM = "medium"
GPTIMAGE1_QUALITY_HIGH = "high"


class DalleOpenAI:
    def __init__(self, api_key: str, model_type: str, model: str):
        self.model_type = model_type
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def gen_image(self, prompt: str, size: str = DALLE3_IMAGE_SIZE1, quality: str = DALLE3_QUALITY_STANDARD) -> tuple[str, str]:
        if self.model_type == MODEL_TYPE_GPTIMAGE1:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1
            )
        else:
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
    def __init__(self, api_key: str, endpoint: str, model_type: str, model: str):
        self.model_type = model_type
        self.model = model
        self.client = AzureOpenAI(
            api_version="2024-02-01",
            api_key=api_key,
            azure_endpoint=endpoint
        )

    def gen_image(self, prompt: str, size: str = DALLE3_IMAGE_SIZE1, quality: str = DALLE3_QUALITY_STANDARD) -> tuple[str, str]:
        if self.model_type == MODEL_TYPE_GPTIMAGE1:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1
            )
        else :
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
                response_format="b64_json"
            )
        return response.data[0].b64_json, response.data[0].revised_prompt
