#!/usr/bin/env python3
"""Deterministic, typography-first bilingual lock-screen wallpaper."""
import json
import os
from datetime import datetime, date
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "public"
OUT.mkdir(exist_ok=True)
W, H = 1290, 2796
# Background, primary text, secondary text, divider; one palette per local day.
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
FONT_LATIN = os.getenv("FONT_LATIN", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
FONT_CJK = os.getenv("FONT_CJK", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")

def font(size, cjk=False):
    return ImageFont.truetype(FONT_CJK if cjk else FONT_LATIN, size)

def wrap(draw, text, f, width):
    lines, current = [], ""
    # Chinese: split by character; Latin: split by word.
    tokens = list(text) if any('\u4e00' <= c <= '\u9fff' for c in text) else text.split(" ")
    sep = "" if isinstance(tokens, list) and len(tokens) and any('\u4e00' <= c <= '\u9fff' for c in text) else " "
    for token in tokens:
        test = (current + sep + token) if current else token
        if draw.textbbox((0,0), test, font=f)[2] <= width:
            current = test
        else:
            if current: lines.append(current)
            current = token
    if current: lines.append(current)
    return lines

def lines(draw, txt, x, y, f, fill, max_width, spacing=15):
    for line in wrap(draw, txt, f, max_width):
        draw.text((x,y),line,font=f,fill=fill,stroke_width=0)
        y += f.size + spacing
    return y

def make(today):
    words=json.loads((ROOT/"data/words.json").read_text(encoding="utf8"))
    anchor=date(2026,10,17)
    item=words[(today-anchor).days % len(words)]
    palette, bg, primary, muted, divider = PALETTES[(today-anchor).days % len(PALETTES)]
    image=Image.new("RGB",(W,H),bg)
    d=ImageDraw.Draw(image)
    x=112; maxw=W-2*x
    # Top 40% is intentionally blank for iOS clock and widgets.
    y=SAFE_TOP
    d.text((x,y),"ENGLISH  /  01",font=font(31),fill=muted)
    y+=68
    d.text((x,y),item["en"],font=font(112),fill=primary)
    y+=151
    d.text((x,y),item["en_ipa"],font=font(37),fill=muted)
    y+=65
    d.text((x,y),item["en_zh"],font=font(42,True),fill=primary)
    y+=92
    y=lines(d,item["en_example"],x,y,font(43),primary,maxw,17)
    y+=12
    y=lines(d,item["en_translation"],x,y,font(33,True),muted,maxw,12)
    y+=75
    d.line((x,y,W-x,y),fill=divider,width=2)
    y+=66
    d.text((x,y),"SRPSKI  /  02",font=font(31),fill=muted)
    y+=69
    d.text((x,y),item["sr"],font=font(93),fill=primary)
    y+=133
    d.text((x,y),item["sr_zh"],font=font(42,True),fill=primary)
    y+=90
    y=lines(d,item["sr_example"],x,y,font(42),primary,maxw,17)
    y+=12
    y=lines(d,item["sr_translation"],x,y,font(33,True),muted,maxw,12)
    # Bottom 15% is reserved for flashlight, camera, and gestures.
    if y>SAFE_BOTTOM:
        raise ValueError(f"Content intrudes into bottom safe zone ({y}). Shorten entry.")
    image.save(OUT/"latest.png",optimize=True)
    image.save(OUT/f"{today.isoformat()}.png",optimize=True)
    (OUT/"latest.json").write_text(json.dumps({"date":today.isoformat(),"english":item["en"],"serbian":item["sr"],"palette":palette},ensure_ascii=False),encoding="utf8")
    (OUT/"index.html").write_text(f"""<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Daily Vocabulary Wallpaper</title><style>body{{background:{bg};color:{primary};font:16px system-ui;text-align:center;padding:30px}}img{{width:min(100%,390px);border-radius:18px}}</style><h1>Daily Vocabulary</h1><p>{today.isoformat()} · {item['en']} / {item['sr']}</p><img src="latest.png" alt="Today's wallpaper"><p><a style="color:{primary}" href="latest.png">Open wallpaper image</a></p></html>""",encoding="utf8")
    print(f"Created {OUT/'latest.png'} for {today}; content ends at y={y}")

if __name__=="__main__":
    import sys
    chosen=date.fromisoformat(sys.argv[1]) if len(sys.argv)>1 else datetime.now(ZoneInfo("Europe/Belgrade")).date()
    make(chosen)
