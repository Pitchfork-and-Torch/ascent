#!/usr/bin/env python3
"""ASCENT tweet/OG card - exact 1200x630 raster (Pillow).

v2.1.0: premium hero card from scratch - Fontshare Clash Display + Satoshi,
cinematic void, ascending wire constellation (not the dense stack panel).
ASCII hyphens only in drawn text (no em/en dashes).
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public"
MASTER = ROOT.parent / "assets" / "masters"
HOME = Path.home()
FONTSHARE = HOME / "design-assets" / "fontshare"

W, H = 1200, 630
VERSION = "2.1.0"

# Brand tokens (match site/public/styles.css)
BG = (10, 10, 15)
TEAL = (0, 229, 192)
CYAN = (61, 214, 255)
VIOLET = (139, 124, 255)
AMBER = (240, 180, 41)
PINK = (255, 122, 217)
TEXT = (245, 247, 250)
MUTED = (139, 144, 165)
FAINT = (90, 95, 117)
PANEL = (16, 16, 24)


def font_path(*parts: str) -> Path:
    return FONTSHARE.joinpath(*parts)


def load_font(size: int, kind: str = "sans") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Prefer Fontshare; fall back to system faces."""
    candidates: list[Path] = []
    if kind == "display":
        candidates += [
            font_path("clash-display", "otf", "ClashDisplay-Bold.otf"),
            font_path("clash-display", "otf", "ClashDisplay-Semibold.otf"),
            Path(r"C:\Windows\Fonts\segoeuib.ttf"),
            Path(r"C:\Windows\Fonts\arialbd.ttf"),
        ]
    elif kind == "display_med":
        candidates += [
            font_path("clash-display", "otf", "ClashDisplay-Medium.otf"),
            font_path("clash-display", "otf", "ClashDisplay-Semibold.otf"),
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
        ]
    elif kind == "sans_bold":
        candidates += [
            font_path("satoshi", "otf", "Satoshi-Bold.otf"),
            font_path("satoshi", "otf", "Satoshi-Medium.otf"),
            Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        ]
    elif kind == "sans_med":
        candidates += [
            font_path("satoshi", "otf", "Satoshi-Medium.otf"),
            font_path("satoshi", "otf", "Satoshi-Regular.otf"),
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
        ]
    elif kind == "sans":
        candidates += [
            font_path("satoshi", "otf", "Satoshi-Regular.otf"),
            font_path("general-sans", "ttf", "GeneralSans-Regular.ttf"),
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
            Path(r"C:\Windows\Fonts\arial.ttf"),
        ]
    else:  # mono
        candidates += [
            Path(r"C:\Windows\Fonts\consola.ttf"),
            Path(r"C:\Windows\Fonts\cour.ttf"),
            Path(r"C:\Windows\Fonts\lucon.ttf"),
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
        ]
    for p in candidates:
        try:
            return ImageFont.truetype(str(p), size)
        except OSError:
            continue
    return ImageFont.load_default()


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_rgb(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )


def rr(draw: ImageDraw.ImageDraw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def paint_void() -> Image.Image:
    """Deep void with dual orbs + vignette (site aesthetic)."""
    img = Image.new("RGB", (W, H), BG)
    px = img.load()
    for y in range(H):
        for x in range(W):
            nx, ny = x / (W - 1), y / (H - 1)
            r = int(8 + 4 * ny)
            g = int(8 + 5 * ny)
            b = int(12 + 10 * ny)
            # Teal orb (left-mid)
            d1 = math.hypot(nx - 0.22, ny - 0.38)
            m1 = max(0.0, 1.0 - d1 * 1.55) ** 2.2
            g += int(95 * m1)
            b += int(78 * m1)
            r += int(8 * m1)
            # Cyan/violet orb (right)
            d2 = math.hypot(nx - 0.78, ny - 0.42)
            m2 = max(0.0, 1.0 - d2 * 1.35) ** 2.0
            r += int(28 * m2)
            g += int(55 * m2)
            b += int(120 * m2)
            # Amber kiss (lower right)
            d3 = math.hypot(nx - 0.92, ny - 0.86)
            m3 = max(0.0, 1.0 - d3 * 2.4) ** 2
            r += int(48 * m3)
            g += int(28 * m3)
            b += int(6 * m3)
            px[x, y] = (min(255, r), min(255, g), min(255, b))

    # Soft grid
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, W, 48):
        gd.line([(x, 0), (x, H)], fill=(61, 214, 255, 9), width=1)
    for y in range(0, H, 48):
        gd.line([(0, y), (W, y)], fill=(61, 214, 255, 7), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), grid).convert("RGB")

    # Film grain
    rng = random.Random(42)
    grain = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gpx = grain.load()
    for _ in range(9000):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        a = rng.randint(4, 18)
        v = rng.randint(180, 255)
        gpx[x, y] = (v, v, v, a)
    img = Image.alpha_composite(img.convert("RGBA"), grain).convert("RGB")

    # Vignette
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for i in range(100):
        a = int(i * 1.55)
        vd.rectangle((i, i, W - 1 - i, H - 1 - i), outline=(0, 0, 0, min(220, a)))
    img = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")
    return img


def draw_spectral_bar(draw: ImageDraw.ImageDraw) -> None:
    """Top bar: plane spectrum P0 -> P9."""
    planes = [
        (232, 234, 240),  # P0
        (90, 143, 255),  # P1
        (124, 92, 255),  # P2
        (160, 100, 255),
        (200, 90, 230),
        (61, 214, 255),  # P5
        (240, 180, 41),  # P6
        (255, 122, 217),  # P7
        (100, 220, 200),
        (0, 229, 192),  # P9
    ]
    n = len(planes)
    for x in range(W):
        t = x / (W - 1)
        idx = min(n - 2, int(t * (n - 1)))
        local = (t * (n - 1)) - idx
        c = lerp_rgb(planes[idx], planes[idx + 1], local)
        draw.line([(x, 0), (x, 6)], fill=(*c, 255))


def draw_wire_constellation(base: Image.Image) -> Image.Image:
    """Right-side ascending wire geometry: nodes, fences, hex glow."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = random.Random(7)

    # Anchor region (right half)
    cx, cy = 880, 300
    nodes: list[tuple[float, float, tuple[int, int, int], float]] = []
    colors = [TEAL, CYAN, VIOLET, AMBER, PINK, (90, 143, 255)]

    # Spiral ascent of nodes
    for i in range(28):
        ang = i * 0.55 + 0.4
        rad = 40 + i * 11.5
        x = cx + math.cos(ang) * rad * 1.15
        y = cy + math.sin(ang) * rad * 0.72 - i * 3.2
        col = colors[i % len(colors)]
        r = 4.5 + (i % 5) * 1.4
        nodes.append((x, y, col, r))

    # Extra free stars
    for _ in range(40):
        x = rng.uniform(620, 1160)
        y = rng.uniform(70, 560)
        col = colors[rng.randint(0, len(colors) - 1)]
        nodes.append((x, y, col, rng.uniform(1.5, 3.2)))

    # Links between nearby spiral nodes
    for i in range(min(27, len(nodes) - 1)):
        x1, y1, c1, _ = nodes[i]
        x2, y2, c2, _ = nodes[i + 1]
        mid = (
            int((c1[0] + c2[0]) / 2),
            int((c1[1] + c2[1]) / 2),
            int((c1[2] + c2[2]) / 2),
        )
        d.line([(x1, y1), (x2, y2)], fill=(*mid, 55), width=1)

    # A few long diagonals (constellation)
    for a, b in ((0, 8), (3, 14), (6, 18), (10, 22), (12, 25)):
        if a < len(nodes) and b < len(nodes):
            x1, y1, c1, _ = nodes[a]
            x2, y2, c2, _ = nodes[b]
            d.line([(x1, y1), (x2, y2)], fill=(*c1, 40), width=1)

    # Glow discs under key nodes
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i, (x, y, col, r) in enumerate(nodes[:18]):
        gr = r * 7
        gd.ellipse((x - gr, y - gr, x + gr, y + gr), fill=(*col, 18))
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    layer = Image.alpha_composite(layer, glow)
    d = ImageDraw.Draw(layer)

    # Nodes
    for x, y, col, r in nodes:
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*col, 230))
        d.ellipse((x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4), fill=(255, 255, 255, 90))

    # Agent fence brackets (visual motif, not dense UI)
    fmono = load_font(13, "mono")
    # Left fence 9A
    bx, by = 700, 120
    d.rounded_rectangle((bx, by, bx + 72, by + 36), radius=8, fill=(10, 12, 18, 180), outline=(*TEAL, 100), width=1)
    d.text((bx + 14, by + 10), "9A", font=fmono, fill=(*TEAL, 255))
    # Right fence 9B
    bx2, by2 = 1040, 480
    d.rounded_rectangle((bx2, by2, bx2 + 72, by2 + 36), radius=8, fill=(10, 12, 18, 180), outline=(*VIOLET, 100), width=1)
    d.text((bx2 + 14, by2 + 10), "9B", font=fmono, fill=(*VIOLET, 255))
    # MM marker
    bx3, by3 = 980, 160
    d.rounded_rectangle((bx3, by3, bx3 + 64, by3 + 32), radius=8, fill=(10, 12, 18, 180), outline=(*CYAN, 90), width=1)
    d.text((bx3 + 14, by3 + 8), "MM", font=fmono, fill=(*CYAN, 255))
    # P9 RS chip
    bx4, by4 = 720, 470
    d.rounded_rectangle((bx4, by4, bx4 + 110, by4 + 32), radius=8, fill=(10, 12, 18, 180), outline=(*AMBER, 90), width=1)
    d.text((bx4 + 12, by4 + 8), "P9 RS", font=fmono, fill=(*AMBER, 255))

    # Soft hex whisper (readable at full size, texture at small)
    whisper = [
        (760, 250, "D3 A9"),
        (900, 360, "F3 AD"),
        (840, 200, "C1 01"),
        (1020, 300, "00 80"),
    ]
    for x, y, txt in whisper:
        d.text((x, y), txt, font=fmono, fill=(*MUTED, 70))

    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def draw_left_copy(img: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(img, "RGBA")

    f_badge = load_font(14, "mono")
    f_title = load_font(96, "display")
    f_kicker = load_font(15, "sans_bold")
    f_sub = load_font(24, "sans_med")
    f_law = load_font(15, "mono")
    f_chip = load_font(13, "mono")
    f_meta = load_font(16, "sans_med")
    f_url = load_font(18, "sans_bold")
    f_foot = load_font(13, "mono")

    left = 56
    # Live pill
    rr(draw, (left, 52, left + 340, 90), 999, (0, 229, 192, 18), (*TEAL, 130), 1)
    draw.ellipse((left + 16, 64, left + 32, 80), fill=(*TEAL, 255))
    draw.text((left + 42, 62), f"NEXUS  ·  WIRE LAB  ·  v{VERSION}", font=f_badge, fill=(*TEAL, 255))

    # Kicker
    draw.text((left, 118), "ASCII SUCCESSOR", font=f_kicker, fill=(*CYAN, 220))

    # Massive title
    draw.text((left, 142), "ASCENT", font=f_title, fill=(*TEXT, 255))

    # Gradient underline under title
    under_y = 248
    for x in range(left, left + 360):
        t = (x - left) / 360
        if t < 0.55:
            c = lerp_rgb(TEAL, CYAN, t / 0.55)
        else:
            c = lerp_rgb(CYAN, VIOLET, (t - 0.55) / 0.45)
        draw.line([(x, under_y), (x, under_y + 4)], fill=(*c, 230))

    # Tagline (product promise, readable at tweet scale)
    draw.text((left, 272), "Byte-identical 0-127 forever.", font=f_sub, fill=(*TEXT, 245))
    draw.text((left, 306), "Agents, multimodal, deep space.", font=f_sub, fill=(*MUTED, 255))

    # Parse law capsule
    law = "parse law:  byte < 0x80  ->  ASCII forever"
    rr(draw, (left, 362, left + 520, 412), 12, (8, 10, 16, 220), (*TEAL, 85), 1)
    draw.text((left + 18, 378), law, font=f_law, fill=(180, 245, 220, 255))

    # Mode chips
    chips = [
        ("P0 ASCII", TEAL),
        ("AGENT", CYAN),
        ("MM", VIOLET),
        ("ASCENT-D", AMBER),
    ]
    x = left
    cy = 436
    for label, col in chips:
        tw = f_chip.getlength(label) if hasattr(f_chip, "getlength") else len(label) * 8
        box_w = int(tw) + 28
        rr(draw, (x, cy, x + box_w, cy + 34), 8, (14, 16, 24, 230), (*col, 120), 1)
        draw.text((x + 14, cy + 9), label, font=f_chip, fill=(*col, 255))
        x += box_w + 10

    # Footer
    draw.text((left, 520), "ascent.jonbailey.xyz", font=f_url, fill=(*CYAN, 255))
    draw.text(
        (left, 556),
        "pip install ascent-wire   ·   npm install ascent-wire",
        font=f_foot,
        fill=(*FAINT, 255),
    )
    draw.text((left, 582), "Pitchfork-and-Torch  ·  MIT  ·  SPEC 1.0.0-rc1", font=f_foot, fill=(*FAINT, 220))

    # Version stamp bottom-right
    draw.text((1088, 582), f"v{VERSION}", font=f_meta, fill=(*TEAL, 255))

    return img


def main() -> None:
    img = paint_void()
    draw = ImageDraw.Draw(img, "RGBA")
    draw_spectral_bar(draw)
    img = draw_wire_constellation(img)
    img = draw_left_copy(img)

    # Outer hairline frame (premium card edge)
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rounded_rectangle((10, 10, W - 11, H - 11), radius=18, outline=(61, 214, 255, 28), width=1)

    out_img = img.convert("RGB")
    OUT.mkdir(parents=True, exist_ok=True)
    MASTER.mkdir(parents=True, exist_ok=True)
    jpg = OUT / "og.jpg"
    png = OUT / "og.png"
    master = MASTER / "ascent-og-1200x630.jpg"
    master_png = MASTER / "ascent-og-1200x630.png"
    out_img.save(jpg, "JPEG", quality=95, optimize=True, progressive=True)
    out_img.save(png, "PNG", optimize=True)
    out_img.save(master, "JPEG", quality=96, optimize=True)
    out_img.save(master_png, "PNG", optimize=True)

    check = Image.open(jpg)
    assert check.size == (1200, 630), check.size
    print("wrote", jpg, f"({jpg.stat().st_size} bytes)")
    print("wrote", png, f"({png.stat().st_size} bytes)")
    print("wrote", master)
    print("VERSION", VERSION)


if __name__ == "__main__":
    main()
