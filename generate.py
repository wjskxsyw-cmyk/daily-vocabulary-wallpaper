#!/usr/bin/env python3
"""Curated, source-checked Daily Insight. No runtime AI or external content fetch."""
import hashlib
import html
import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'public'
W, H = 1290, 2796
ANCHOR = date(2026, 10, 29)
TIMEZONE = 'Europe/Belgrade'
PALETTES = (
    ("warm ivory", "#F4EFE6", "#302D28", "#625C52", "#C7BBA9"),
    ("forest green", "#193C34", "#F5F1E7", "#C0D2C5", "#698A78"),
    ("burgundy", "#512D39", "#FAF0E8", "#DEC2C6", "#9B737D"),
    ("graphite", "#292C30", "#F2F0EB", "#C1C4C7", "#737A80"),
    ("lavender", "#E5DEED", "#383040", "#65586F", "#B3A5C1"),
    ("mocha", "#59453B", "#FAF1E7", "#DECABC", "#A58B79"),
    ("dusty rose", "#E6C8C7", "#432F35", "#705057", "#B18A8F"),
    ("slate blue", "#3E5366", "#F4F2EC", "#C8D5DF", "#859CAD"),
)
SAFE_TOP = (H * 40 + 99) // 100
SAFE_BOTTOM = H * 85 // 100
FONT_LATIN = os.getenv('FONT_LATIN', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
FONT_CJK = os.getenv('FONT_CJK', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')

def font(size, cjk=False):
    return ImageFont.truetype(FONT_CJK if cjk else FONT_LATIN, size)

def load_entries():
    entries = json.loads((ROOT / 'data/insights.json').read_text(encoding='utf8'))
    ids = [e['id'] for e in entries]
    assert len(entries) >= 32 and len(ids) == len(set(ids)), 'Unique content IDs required'
    for e in entries:
        for key in ('title', 'english', 'explanation', 'example', 'action'):
            assert isinstance(e[key], str) and e[key].strip(), (e['id'], key)
        assert e['english_kind'] == 'faithful paraphrase'
        assert e['example_kind'] == 'editorial illustration'
        s = e['source']
        assert s['url'].startswith('https://') and s['author'] and s['title']
        # Preserve month-only source dates; never invent a day of publication.
        assert len(s['published']) in (7, 10)
        date.fromisoformat(s['published'] + ('-01' if len(s['published']) == 7 else ''))
        date.fromisoformat(s['verified_on'])
    return entries

def selection(day, entries):
    offset = (day - ANCHOR).days
    if offset < 0:
        raise ValueError('Daily Insight starts on 2026-10-29')
    return entries[offset % len(entries)], offset // len(entries) + 1

def wrap(draw, text, f, width):
    # Keep Latin words together; split Chinese and long URLs only when needed.
    import re
    tokens = re.findall(r'[A-Za-z0-9]+(?:[’\x27-][A-Za-z0-9]+)*|[^A-Za-z0-9]', text)
    result, line = [], ''
    for token in tokens:
        if draw.textlength(token, font=f) > width:
            parts = list(token)
        else:
            parts = [token]
        for part in parts:
            if line and draw.textlength(line + part, font=f) > width:
                if part in '，。；：？！、）”’':
                    result.append(line[:-1].rstrip())
                    line = line[-1]
                else:
                    result.append(line.rstrip())
                    line = ''
            line += part if line else part.lstrip()
    if line.strip():
        result.append(line.rstrip())
    return result

def render(day, entry, palette):
    name, bg, primary, muted, divider = palette
    image = Image.new('RGB', (W, H), bg)
    draw = ImageDraw.Draw(image)
    x, width, y = 104, W - 208, SAFE_TOP + 12
    bounds = []

    def text(value, size, cjk=False, color=primary, gap=14):
        nonlocal y
        f = font(size, cjk)
        for line in wrap(draw, value, f, width):
            box = draw.textbbox((x, y), line, font=f, anchor='lt')
            if box[0] < 100 or box[2] > W - 100 or box[3] > SAFE_BOTTOM:
                raise ValueError(f"{entry['id']}: text overflow: {box}")
            draw.text((x, y), line, font=f, fill=color, anchor='lt')
            bounds.append(box)
            y += max(size, box[3] - box[1]) + 10
        y += gap

    text(f"DAILY INSIGHT  /  {day.isoformat()}", 30, color=muted, gap=24)
    text(entry['title'], 60, True, gap=22)
    text('ENGLISH · 意译，非原话', 26, True, muted, 9)
    text(entry['english'], 44, gap=19)
    text(entry['explanation'], 42, True, gap=21)
    text('例 · 自拟情境  ' + entry['example'], 40, True, gap=21)
    text('今天试试  ' + entry['action'], 44, True, gap=21)
    draw.line((x, y, W - x, y), fill=divider, width=2)
    y += 20
    s = entry['source']
    text(f"{s['author']} · {s['published']}", 28, gap=2)
    text(s['title'], 27, gap=2)
    text(s['url'].removeprefix('https://'), 27, color=muted, gap=0)
    if y > SAFE_BOTTOM:
        raise ValueError(f"{entry['id']}: content ends at {y}, limit {SAFE_BOTTOM}")
    return image, bounds

def make(today):
    entries = load_entries()
    entry, cycle = selection(today, entries)
    palette = PALETTES[(today - ANCHOR).days % len(PALETTES)]
    image, bounds = render(today, entry, palette)
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / 'latest.png', optimize=True)
    image.save(OUT / f'{today}.png', optimize=True)
    metadata = dict(date=str(today), type='daily-insight', id=entry['id'],
                    palette=palette[0], timezone=TIMEZONE, cycle=cycle,
                    library_size=len(entries), mode='curated rotation',
                    image_sha256=hashlib.sha256((OUT / 'latest.png').read_bytes()).hexdigest(),
                    content=entry, content_bounds=bounds)
    (OUT / 'latest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf8')
    # A reviewable date-to-ID index. Same date always selects the same item.
    index = {str(ANCHOR + timedelta(days=i)): entries[i]['id'] for i in range(len(entries))}
    (OUT / 'date-index.json').write_text(json.dumps(dict(anchor=str(ANCHOR), repeat_after_days=len(entries), first_cycle=index), indent=2), encoding='utf8')
    esc = html.escape
    s = entry['source']
    page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Daily Insight</title>
<style>body{{background:{palette[1]};color:{palette[2]};font:18px/1.7 system-ui;max-width:720px;margin:auto;padding:24px}}a{{color:inherit}}img{{width:min(100%,390px);display:block;margin:auto}}small{{font-size:14px}}</style>
<h1>Daily Insight · {today}</h1><h2>{esc(entry['title'])}</h2>
<p lang="en">{esc(entry['english'])}</p><small>英文为忠实意译，并非作者原话；以下例子与行动建议为编辑整理。</small>
<p>{esc(entry['explanation'])}</p><p>例：{esc(entry['example'])}</p><p>今天试试：{esc(entry['action'])}</p>
<p>来源：<a href="{esc(s['url'], quote=True)}">{esc(s['author'])} · {esc(s['title'])}</a> · {s['published']}<br><small>来源核验日期：{s['verified_on']}。原文仅标月份时保留月份。</small></p>
<p><a href="latest.png">下载壁纸 latest.png</a> · <a href="latest.json">内容与校验信息</a> · <a href="date-index.json">日期索引</a></p>
<img src="latest.png?day={today}" alt="{esc(entry['title'], quote=True)}">
<p><small>{len(entries)} 条精选内容，{len(entries)} 天内不重复，之后循环。目前第 {cycle} 轮。不是无限 AI 创作，不使用 API key。</small></p></html>'''
    (OUT / 'index.html').write_text(page, encoding='utf8')
    (OUT / '.nojekyll').touch()
    print(f"Daily Insight {today}: {entry['id']}, cycle {cycle}, {palette[0]}")
    return metadata

if __name__ == '__main__':
    import sys
    chosen = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(ZoneInfo(TIMEZONE)).date()
    make(chosen)
