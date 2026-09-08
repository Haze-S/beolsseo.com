#!/usr/bin/env python3
"""파비콘 생성 (허브 #6 — blog-dev scripts/favicon.py 와 같은 도형·규칙)

data/site.json 의 favicon 값(배경색·전경색·글리프)으로 아래 3개를 만든다. 외부 이미지·폰트 없이 도형만 그린다.
  favicon.ico              루트. 16·32·48 멀티 사이즈 (브라우저가 /favicon.ico 를 자동 요청)
  assets/favicon.svg       선명한 벡터판 (지원 브라우저 우선)
  assets/apple-touch-icon.png  180x180 (iOS 홈 화면·사파리 탭)

글리프
  prompt   터미널 프롬프트 `>_` (개발 블로그)
  그 외    한 글자 텍스트 (예: "₩", "L") — 시스템 볼드 폰트가 있으면 그것으로, 없으면 기본 폰트

허브 글리프는 `H`(Haze). 변경 시 data/site.json favicon.glyph 를 바꾸고 --force 로 재생성한다.
사용: python3 scripts/favicon.py [--force]
"""

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CANVAS = 512
DEFAULTS = {"bg": "#3f5fcf", "fg": "#ffffff", "glyph": "H"}
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def read_config() -> dict:
    """data/site.json 의 favicon 블록을 읽는다."""
    import json
    cfg = dict(DEFAULTS)
    path = ROOT / "data" / "site.json"
    if path.exists():
        block = json.loads(path.read_text(encoding="utf-8")).get("favicon") or {}
        cfg.update({k: v for k, v in block.items() if k in DEFAULTS and v})
    return cfg


def draw_prompt(draw: ImageDraw.ImageDraw, fg: str) -> None:
    """`>_` — 둥근 끝 선 두 개. 좌표는 512 캔버스 기준."""
    w = 64
    chevron = [(150, 150), (270, 256), (150, 362)]
    draw.line(chevron, fill=fg, width=w, joint="curve")
    for p in (chevron[0], chevron[-1]):
        draw.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=fg)
    under = [(300, 362), (400, 362)]
    draw.line(under, fill=fg, width=w)
    for p in under:
        draw.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=fg)


def draw_text(draw: ImageDraw.ImageDraw, text: str, fg: str) -> None:
    font = None
    for cand in FONT_CANDIDATES:
        if Path(cand).exists():
            font = ImageFont.truetype(cand, int(CANVAS * 0.62))
            break
    if font is None:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.text(((CANVAS - tw) / 2 - box[0], (CANVAS - th) / 2 - box[1]), text, font=font, fill=fg)


def render(cfg: dict) -> Image.Image:
    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, CANVAS - 1, CANVAS - 1], radius=int(CANVAS * 0.22), fill=cfg["bg"])
    if cfg["glyph"] == "prompt":
        draw_prompt(draw, cfg["fg"])
    else:
        draw_text(draw, cfg["glyph"][:2], cfg["fg"])
    return img


def svg(cfg: dict) -> str:
    r = int(CANVAS * 0.22)
    if cfg["glyph"] == "prompt":
        body = (
            f'<path d="M150 150 L270 256 L150 362 M300 362 H400" fill="none" stroke="{cfg["fg"]}" '
            'stroke-width="64" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    else:
        body = (
            f'<text x="256" y="256" fill="{cfg["fg"]}" font-family="system-ui, sans-serif" font-weight="700" '
            f'font-size="320" text-anchor="middle" dominant-baseline="central">{cfg["glyph"][:2]}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS} {CANVAS}">'
        f'<rect width="{CANVAS}" height="{CANVAS}" rx="{r}" fill="{cfg["bg"]}"/>{body}</svg>\n'
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="기존 파일도 다시 생성")
    args = parser.parse_args()
    cfg = read_config()
    outputs = {
        ROOT / "favicon.ico": None,
        ROOT / "assets" / "favicon.svg": None,
        ROOT / "assets" / "apple-touch-icon.png": None,
    }
    if not args.force and all(p.exists() for p in outputs):
        print("파비콘 이미 있음 — 건너뜀 (--force 로 재생성)")
        return 0
    img = render(cfg)
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "favicon.svg").write_text(svg(cfg), encoding="utf-8")
    img.resize((180, 180), Image.LANCZOS).save(ROOT / "assets" / "apple-touch-icon.png", "PNG", optimize=True)
    # ICO: 사이즈별로 LANCZOS 축소한 프레임을 담는다 (PIL 이 내부 축소하면 뭉개진다)
    frames = [img.resize((s, s), Image.LANCZOS) for s in (48, 32, 16)]
    frames[0].save(ROOT / "favicon.ico", format="ICO", sizes=[(48, 48), (32, 32), (16, 16)],
                   append_images=frames[1:])
    for p in outputs:
        print(f"생성: {p.relative_to(ROOT)} ({p.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
