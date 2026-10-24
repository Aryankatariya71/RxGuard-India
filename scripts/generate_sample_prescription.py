#!/usr/bin/env python3
"""Generate a synthetic clean printed sample prescription image (demo only)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "samples" / "sample_prescription.png"

LINES = [
    "RxGuard Demo Clinic — SYNTHETIC SAMPLE",
    "Patient: Demo Patient (illustrative only)",
    "",
    "Rx",
    "1. Tab Demo Product Alpha 500 mg  1-0-1  x 5 days",
    "2. Tab Demo Product Beta 325 mg   BD     x 3 days",
    "3. Cap Demo Product Delta 75 mg   HS     x 7 days",
    "",
    "Not a real prescription. Synthetic content for OCR demo.",
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    w, h = 900, 520
    img = Image.new("RGB", (w, h), "#f7f4ef")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
        title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
        small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
        title = font
        small = font

    draw.rectangle([24, 24, w - 24, h - 24], outline="#1e3a4c", width=2)
    y = 48
    for i, line in enumerate(LINES):
        f = title if i == 0 else (small if "Not a real" in line else font)
        draw.text((48, y), line, fill="#12263a", font=f)
        y += 36 if i < 3 else 32

    img.save(OUT, format="PNG")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
