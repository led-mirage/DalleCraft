import io
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from image_clipboard import image_to_dib


class ImageClipboardTest(unittest.TestCase):
    def test_converts_image_to_dib_without_bmp_file_header(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "image.png"
            Image.new("RGBA", (3, 2), (255, 0, 0, 128)).save(image_path)

            dib = image_to_dib(str(image_path))

        self.assertEqual(40, int.from_bytes(dib[:4], "little"))
        self.assertNotEqual(b"BM", dib[:2])


if __name__ == "__main__":
    unittest.main()
