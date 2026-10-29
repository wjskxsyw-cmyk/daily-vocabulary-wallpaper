import hashlib
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageChops, ImageColor
import generate as g


class WallpaperTest(unittest.TestCase):
    def test_full_library_and_safe_zones(self):
        entries = g.load_entries()
        selected = []
        for i, entry in enumerate(entries):
            day = g.ANCHOR + timedelta(days=i)
            chosen, cycle = g.selection(day, entries)
            selected.append(chosen['id'])
            self.assertEqual(cycle, 1)
            for palette in g.PALETTES:
                with self.subTest(id=entry['id'], palette=palette[0]):
                    image, bounds = g.render(day, entry, palette)
                    self.assertEqual(image.size, (1290, 2796))
                    for box in bounds:
                        self.assertGreaterEqual(box[0], 100)
                        self.assertLessEqual(box[2], g.W - 100)
                    bg = Image.new('RGB', image.size, ImageColor.getrgb(palette[1]))
                    actual = ImageChops.difference(image, bg).getbbox()
                    self.assertGreaterEqual(actual[1], g.SAFE_TOP)
                    self.assertLessEqual(actual[3], g.SAFE_BOTTOM)
        self.assertEqual(len(selected), len(set(selected)))
        self.assertEqual(g.selection(g.ANCHOR + timedelta(days=len(entries)), entries), (entries[0], 2))
        with self.assertRaises(ValueError):
            g.selection(g.ANCHOR - timedelta(days=1), entries)

    def test_artifact_contract_and_idempotency(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(g, 'OUT', Path(folder)):
            first = g.make(g.ANCHOR)
            png = (g.OUT / 'latest.png').read_bytes()
            self.assertEqual(png, (g.OUT / f'{g.ANCHOR}.png').read_bytes())
            self.assertEqual(first['image_sha256'], hashlib.sha256(png).hexdigest())
            self.assertEqual(first['type'], 'daily-insight')
            self.assertEqual(first, g.make(g.ANCHOR))
            self.assertEqual(png, (g.OUT / 'latest.png').read_bytes())
            self.assertIn(first['content']['source']['url'], (g.OUT / 'index.html').read_text(encoding='utf8'))
            index = json.loads((g.OUT / 'date-index.json').read_text())
            self.assertEqual(len(index['first_cycle']), len(g.load_entries()))

    def test_overlong_content_fails_instead_of_tiny_type(self):
        entry = dict(g.load_entries()[0], explanation='测试' * 1000)
        with self.assertRaisesRegex(ValueError, 'overflow'):
            g.render(g.ANCHOR, entry, g.PALETTES[0])


if __name__ == '__main__':
    unittest.main()
