import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


class _IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, _tag, attrs):
        self.ids.update(value for key, value in attrs if key == "id")


class ConfigHtmlTest(unittest.TestCase):
    def test_javascript_references_existing_elements(self):
        source = (
            Path(__file__).parents[1] / "src" / "html" / "config.html"
        ).read_text(encoding="utf-8")
        parser = _IdCollector()
        parser.feed(source)
        references = set(re.findall(r'getElementById\("([^"]+)"\)', source))

        self.assertEqual(references - parser.ids, set())


if __name__ == "__main__":
    unittest.main()
