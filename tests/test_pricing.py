import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pricing import PricingConfig


class PricingConfigTest(unittest.TestCase):
    def create_pricing(self, data):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "pricing.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return PricingConfig(path)

    def test_calculates_estimate_from_separate_token_rates(self):
        pricing = self.create_pricing({
            "currency": "USD",
            "tokens_per_price_unit": 1_000_000,
            "providers": {
                "openai": {
                    "test-model": {
                        "text_input": 5.0,
                        "image_input": 8.0,
                        "image_output": 30.0,
                    },
                },
            },
        })

        estimate = pricing.estimate("openai", "test-model", {
            "input_tokens": 110,
            "output_tokens": 1000,
            "total_tokens": 1110,
            "input_tokens_details": {
                "text_tokens": 10,
                "image_tokens": 100,
            },
        })

        self.assertEqual("USD", estimate["currency"])
        self.assertAlmostEqual(0.03085, estimate["amount"])
        self.assertEqual(1_000_000, estimate["tokens_per_price_unit"])

    def test_uses_provider_wildcard_for_foundry_deployment_names(self):
        pricing = self.create_pricing({
            "currency": "JPY",
            "tokens_per_price_unit": 1_000_000,
            "providers": {
                "foundry": {
                    "*": {
                        "text_input": 1.0,
                        "image_input": 2.0,
                        "image_output": 3.0,
                    },
                },
            },
        })

        estimate = pricing.estimate("foundry", "custom-deployment", {
            "output_tokens": 1000,
            "input_tokens_details": {
                "text_tokens": 0,
                "image_tokens": 0,
            },
        })

        self.assertEqual("JPY", estimate["currency"])
        self.assertAlmostEqual(0.003, estimate["amount"])

    def test_returns_none_when_model_price_is_not_configured(self):
        pricing = self.create_pricing({"providers": {"foundry": {}}})

        self.assertIsNone(pricing.estimate("foundry", "deployment", {
            "output_tokens": 1000,
            "input_tokens_details": {
                "text_tokens": 0,
                "image_tokens": 0,
            },
        }))


if __name__ == "__main__":
    unittest.main()
