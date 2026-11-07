# DalleCraft
#
# Copyright (c) 2025-2026 led-mirage
# このソースコードは MITライセンス の下でライセンスされています。
# ライセンスの詳細については、このプロジェクトのLICENSEファイルを参照してください。

import json
from numbers import Real


class PricingConfig:
    """Load token prices and calculate a generation cost estimate."""

    def __init__(self, pricing_path=None):
        self.version = None
        self.currency = "USD"
        self.tokens_per_price_unit = 1_000_000
        self.providers = {}
        if pricing_path:
            self.load(pricing_path)

    def load(self, pricing_path):
        with open(pricing_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        currency = data.get("currency", "USD")
        if not isinstance(currency, str) or not currency.strip():
            raise ValueError("料金設定のcurrencyには文字列を指定してください。")

        tokens_per_price_unit = data.get("tokens_per_price_unit", 1_000_000)
        if (
            isinstance(tokens_per_price_unit, bool)
            or not isinstance(tokens_per_price_unit, int)
            or tokens_per_price_unit <= 0
        ):
            raise ValueError(
                "料金設定のtokens_per_price_unitには正の整数を指定してください。"
            )

        providers = data.get("providers", {})
        if not isinstance(providers, dict):
            raise ValueError("料金設定のprovidersにはオブジェクトを指定してください。")

        normalized_providers = {}
        for provider_name, models in providers.items():
            if not isinstance(models, dict):
                raise ValueError(
                    f"料金設定のproviders.{provider_name}にはオブジェクトを指定してください。"
                )
            normalized_models = {}
            for model_name, rates in models.items():
                normalized_models[model_name] = self._normalize_rates(
                    provider_name,
                    model_name,
                    rates,
                )
            normalized_providers[provider_name] = normalized_models

        self.version = data.get("version")
        self.currency = currency.strip()
        self.tokens_per_price_unit = tokens_per_price_unit
        self.providers = normalized_providers

    @staticmethod
    def _normalize_rates(provider_name, model_name, rates):
        if not isinstance(rates, dict):
            raise ValueError(
                f"料金設定の{provider_name}.{model_name}にはオブジェクトを指定してください。"
            )

        normalized_rates = {}
        for rate_name in ("text_input", "image_input", "image_output"):
            rate = rates.get(rate_name)
            if isinstance(rate, bool) or not isinstance(rate, Real) or rate < 0:
                raise ValueError(
                    f"料金設定の{provider_name}.{model_name}.{rate_name}には"
                    "0以上の数値を指定してください。"
                )
            normalized_rates[rate_name] = float(rate)
        return normalized_rates

    def estimate(self, provider_name: str, model_name: str, token_usage: dict):
        provider_prices = self.providers.get(provider_name, {})
        rates = provider_prices.get(model_name) or provider_prices.get("*")
        if rates is None or not token_usage:
            return None

        input_details = token_usage.get("input_tokens_details")
        if not isinstance(input_details, dict):
            return None

        text_input_tokens = self._token_count(input_details.get("text_tokens"))
        image_input_tokens = self._token_count(input_details.get("image_tokens"))

        output_details = token_usage.get("output_tokens_details")
        if isinstance(output_details, dict) and "image_tokens" in output_details:
            image_output_tokens = self._token_count(output_details.get("image_tokens"))
        else:
            image_output_tokens = self._token_count(token_usage.get("output_tokens"))

        amount = (
            text_input_tokens * rates["text_input"]
            + image_input_tokens * rates["image_input"]
            + image_output_tokens * rates["image_output"]
        ) / self.tokens_per_price_unit

        return {
            "currency": self.currency,
            "amount": amount,
            "tokens_per_price_unit": self.tokens_per_price_unit,
            "rates": dict(rates),
        }

    @staticmethod
    def _token_count(value):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return 0
        return value
