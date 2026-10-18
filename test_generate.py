"""Run with the same FONT_LATIN/FONT_CJK settings as generate.py."""
import contextlib
import io
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageChops, ImageColor
import generate as g


class WallpaperTest(unittest.TestCase):
    def test_cycle_and_safe_zones(self):
        words = json.loads((g.ROOT / 'data/words.json').read_text(encoding='utf8'))
        anchor = date(2026, 10, 17)
        names = set()
        with tempfile.TemporaryDirectory() as folder, patch.object(g, 'OUT', Path(folder)):
            for i in range(len(words)):
                day = anchor + timedelta(days=i)
                with self.subTest(day=day), contextlib.redirect_stdout(io.StringIO()):
                    g.make(day)
                    metadata = json.loads((g.OUT / 'latest.json').read_text(encoding='utf8'))
                    name, bg, *_ = g.PALETTES[i % 8]
                    names.add(metadata['palette'])
                    self.assertEqual(metadata, dict(date=str(day), english=words[i]['en'], serbian=words[i]['sr'], palette=name))
                    with Image.open(g.OUT / 'latest.png') as image:
                        self.assertEqual(image.size, (1290, 2796))
                        bounds = ImageChops.difference(image, Image.new('RGB', image.size, ImageColor.getrgb(bg))).getbbox()
                        self.assertIsNotNone(bounds)
                        self.assertGreaterEqual(bounds[1], g.SAFE_TOP)
                        self.assertLessEqual(bounds[3], g.SAFE_BOTTOM)
                    self.assertEqual((g.OUT / 'latest.png').read_bytes(), (g.OUT / f'{day}.png').read_bytes())
                    self.assertIn(f'background:{bg}', (g.OUT / 'index.html').read_text(encoding='utf8'))
        self.assertEqual(names, {p[0] for p in g.PALETTES})


if __name__ == '__main__':
    unittest.main()
