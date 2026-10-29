"""Verify the deployed PNG bytes, not merely an Actions green check."""
import hashlib
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE = 'https://wjskxsyw-cmyk.github.io/daily-vocabulary-wallpaper/'


def verify():
    expected = json.loads(Path('public/latest.json').read_text(encoding='utf8'))
    for attempt in range(12):
        try:
            query = f'?verify={expected["date"]}-{time.time_ns()}'
            def read(path):
                with urlopen(Request(BASE + path + query, headers={'Cache-Control': 'no-cache'}), timeout=30) as r:
                    return r.read()
            live = json.loads(read('latest.json'))
            png = read('latest.png')
            assert live['type'] == 'daily-insight'
            assert live['date'] == expected['date'] and live['id'] == expected['id']
            assert hashlib.sha256(png).hexdigest() == expected['image_sha256'] == live['image_sha256']
            assert png.startswith(b'\x89PNG\r\n\x1a\n')
            print(f'PUBLIC VERIFIED: {live["date"]} {live["id"]} {live["image_sha256"]}')
            return
        except Exception as exc:
            print(f'Public verification attempt {attempt + 1}: {exc}')
            if attempt == 11:
                raise
            time.sleep(15)


if __name__ == '__main__':
    verify()
