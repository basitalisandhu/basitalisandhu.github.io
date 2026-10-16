#!/usr/bin/env python3
"""Generate the site's default Open Graph image, sitekit/og-default.png (1200x630).

The build copies the committed PNG into docs/og.png, so the build itself stays
standard-library only. Run this by hand after changing the site title or
description, then rebuild:

    python3 -m pip install pillow
    python3 scripts/make_og_image.py [--font-dir DIR]

Fonts: Inter from --font-dir when present, then DejaVu Sans (Linux), then Arial
(macOS), then Pillow's built-in font.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
W, H = 1200, 630
BG = (10, 22, 40)  # --bg
FG = (244, 246, 250)  # --text
MUTED = (147, 160, 189)  # --muted
ACCENT = (46, 107, 255)  # --accent
GOLD = (201, 162, 39)  # --gold
MARGIN = 80

FALLBACKS = {
    "bold": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
    "regular": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"],
}


def font(font_dir: str | None, weight: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = []
    if font_dir:
        candidates.append(os.path.join(font_dir, f"Inter-{weight.capitalize()}.ttf"))
    candidates += FALLBACKS[weight]
    for path in candidates:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def wrap(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=f) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + ([cur] if cur else [])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--font-dir")
    ap.add_argument("--out", type=Path, default=ROOT / "sitekit" / "og-default.png")
    args = ap.parse_args()
    cfg = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 12, H], fill=ACCENT)
    d.ellipse([MARGIN, 92, MARGIN + 22, 114], fill=GOLD)
    d.text((MARGIN + 40, 84), cfg["url"].removeprefix("https://"), font=font(args.font_dir, "regular", 32), fill=MUTED)
    d.text((MARGIN, 170), cfg["title"], font=font(args.font_dir, "bold", 76), fill=FG)
    body = font(args.font_dir, "regular", 40)
    y = 290
    for line in wrap(d, cfg["og_tagline"], body, W - 2 * MARGIN)[:4]:
        d.text((MARGIN, y), line, font=body, fill=FG)
        y += 56
    d.text((MARGIN, H - 100), cfg["github"].removeprefix("https://"), font=font(args.font_dir, "regular", 30), fill=MUTED)
    img.save(args.out, optimize=True)
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
