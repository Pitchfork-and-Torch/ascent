#!/usr/bin/env python3
"""ASCENT Nexus architecture card - exact text via Pillow.

Standing: after every major ASCENT update, bump VERSION, regenerate, deploy site + repo.
ASCII hyphens only. Outputs docs/, site/public/, assets/masters/
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
W, H = 1200, 1800
VERSION = "3.0.0"


def font(size: int, bold: bool = False):
    paths = []
    if bold:
        paths += [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
        ]
    paths += [
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\consola.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def mono(size: int):
    for p in (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return font(size)


def rr(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def main() -> None:
    img = Image.new("RGB", (W, H), (10, 10, 15))
    draw = ImageDraw.Draw(img, "RGBA")

    for x in range(W):
        t = x / max(1, W - 1)
        if t < 0.5:
            u = t * 2
            r = int(0 * (1 - u) + 61 * u)
            g = int(229 * (1 - u) + 214 * u)
            b = int(192 * (1 - u) + 255 * u)
        else:
            u = (t - 0.5) * 2
            r = int(61 * (1 - u) + 240 * u)
            g = int(214 * (1 - u) + 180 * u)
            b = int(255 * (1 - u) + 41 * u)
        draw.line([(x, 0), (x, 6)], fill=(r, g, b, 255))

    f_badge = mono(17)
    f_title = font(68, bold=True)
    f_sub = font(22)
    f_h = font(20, bold=True)
    f_body = font(18)
    f_mono = mono(15)
    f_small = mono(13)
    f_tiny = mono(12)

    mint = (0, 229, 192)
    cyan = (61, 214, 255)
    amber = (240, 180, 41)
    violet = (139, 124, 255)
    text = (232, 234, 240)
    muted = (139, 144, 165)
    panel = (16, 16, 24, 255)
    panel2 = (20, 20, 30, 255)

    draw.text(
        (56, 28),
        f"ASCENT NEXUS  ·  Wire Lab 3.0 Crystal Wire  ·  v{VERSION}  ·  MIT",
        font=f_badge,
        fill=(*mint, 255),
    )
    draw.text((56, 64), "ASCENT", font=f_title, fill=(*text, 255))
    draw.text(
        (56, 142),
        "ASCII Successor with Compatible Encoding of Named Text",
        font=f_sub,
        fill=(*muted, 255),
    )
    draw.text(
        (56, 174),
        "Wire instrument for humans, agents, media, deep space  -  and dual-mode Grok resilience.",
        font=f_body,
        fill=(*muted, 255),
    )

    rr(draw, (56, 214, W - 56, 298), 14, panel, (*mint, 150), 2)
    draw.text((76, 228), "ETERNAL PARSE LAW", font=f_small, fill=(*mint, 255))
    draw.text(
        (76, 256),
        "if byte < 0x80  ->  classic 7-bit ASCII, width 1, forever",
        font=f_mono,
        fill=(200, 240, 220, 255),
    )

    draw.text((56, 324), "WHAT IT ADDS", font=f_h, fill=(*text, 255))
    pillars = [
        ("P0 forever", "0x00-0x7F stays\nbyte-identical ASCII", mint),
        ("Agents", "ROLE TOOL THINK\nSAFETY HANDOFF", cyan),
        ("Multimodal", "REF / INLINE\nCHUNK + hash", amber),
        ("AEGIR / PQ", "Alg registry\nno silent downgrade", violet),
        ("Deep space", "P9 RS(255,223)\nerase-on-fail", mint),
        ("Dual-mode", "CLOUD · EDGE\nQUEUE · DEAD", cyan),
    ]
    x0, y0, cw, ch, gap = 56, 356, 172, 118, 12
    for i, (title, body, col) in enumerate(pillars):
        x = x0 + i * (cw + gap)
        rr(draw, (x, y0, x + cw, y0 + ch), 12, panel, (*col, 110), 2)
        draw.rectangle((x, y0, x + 4, y0 + ch), fill=(*col, 230))
        draw.text((x + 12, y0 + 12), title, font=f_h, fill=(*col, 255))
        for j, line in enumerate(body.split("\n")):
            draw.text((x + 12, y0 + 48 + j * 24), line, font=f_body, fill=(*muted, 255))

    draw.text((56, 498), "ONE STREAM  ·  HELLO, UNIVERSE", font=f_h, fill=(*text, 255))
    rr(draw, (56, 528, W - 56, 678), 14, panel, (40, 40, 55, 255), 1)
    segs = [
        ("HEADER", "ASCENT/1.0", mint),
        ("TEXT", "Hello, Universe.", mint),
        ("AGENT", "ROLE=guide", cyan),
        ("MEDIA", "MM REF + hash", amber),
    ]
    sx = 78
    for i, (lab, val, col) in enumerate(segs):
        rr(draw, (sx, 552, sx + 248, 652), 10, panel2, (*col, 120), 2)
        draw.text((sx + 14, 568), lab, font=f_small, fill=(*col, 255))
        draw.text((sx + 14, 604), val, font=f_mono, fill=(*text, 255))
        if i < len(segs) - 1:
            draw.polygon(
                [(sx + 256, 598), (sx + 268, 602), (sx + 256, 606)],
                fill=(*muted, 180),
            )
        sx += 278
    draw.text(
        (78, 658),
        "132-byte civilization kit  ·  greppable P0  ·  fenced control  ·  content-addressed media",
        font=f_tiny,
        fill=(*muted, 255),
    )

    draw.text((56, 702), "ELEVEN PLANES", font=f_h, fill=(*text, 255))
    planes = [
        ("P0", "Identity"),
        ("P1", "C1 fences"),
        ("P2", "Escape"),
        ("P3", "Scripts V"),
        ("P4", "Emoji"),
        ("P5", "Agent"),
        ("P6", "Multimodal"),
        ("P7", "PQ-safe"),
        ("P8", "Self-map"),
        ("P9", "Deep ECC"),
        ("P10+", "Private"),
    ]
    py = 732
    pw = (W - 112 - 10 * 6) // 11
    for i, (pid, name) in enumerate(planes):
        x = 56 + i * (pw + 6)
        col = (
            mint
            if pid == "P0"
            else (
                cyan
                if pid in ("P5", "P9")
                else (amber if pid == "P6" else violet if pid == "P7" else muted)
            )
        )
        rr(draw, (x, py, x + pw, py + 64), 8, panel, (*col, 90), 1)
        draw.text((x + 8, py + 10), pid, font=f_small, fill=(*col, 255))
        draw.text((x + 8, py + 34), name[:10], font=f_tiny, fill=(*muted, 255))

    draw.text((56, 822), "PROFILES", font=f_h, fill=(*text, 255))
    profiles = [
        ("7", "Identity ASCII only"),
        ("E", "Earth full control"),
        ("D", "Deep-space ECC outer"),
        ("A", "Archive / DEF heavy"),
    ]
    px = 56
    for tag, desc in profiles:
        rr(draw, (px, 852, px + 260, 938), 10, panel, (*cyan, 70), 2)
        draw.text((px + 16, 868), "ASCENT-" + tag, font=f_mono, fill=(*mint, 255))
        draw.text((px + 16, 900), desc, font=f_body, fill=(*muted, 255))
        px += 276

    draw.text((56, 968), "CONTROL GRAMMAR (frozen packing)", font=f_h, fill=(*text, 255))
    rr(draw, (56, 998, W - 56, 1148), 14, panel, (*mint, 70), 2)
    lines = [
        "Agent       9A | C1 ver opcode:u16be flags len:u16be args | 9B",
        "Multimodal  9D 4D kind codec flags hash-alg hash len:u64be [body]",
        "Crypto      9C 4B alg:u16be kid nonce ct   (AEGIR registry)",
        "ASCENT-V    Cont 0xA0-0xBF (5-bit)  ·  2/3/4-byte  ·  LONG F5 03 + u24be",
        "ASCENT-D    sync D5E5C0DE + RS(255,223)  ·  parity fail = erase unit",
    ]
    yy = 1018
    for line in lines:
        draw.text((76, yy), line, font=f_mono, fill=(190, 200, 220, 255))
        yy += 24

    # Dual-mode resilience plan
    draw.text(
        (56, 1172),
        "DUAL-MODE RESILIENCE  ·  GROK + STARLINK + ASCENT",
        font=f_h,
        fill=(*text, 255),
    )
    rr(draw, (56, 1202, W - 56, 1448), 14, panel, (*cyan, 90), 2)

    truth = [
        "Truth: Starlink = last-mile IP  ·  ASCENT = wire/session  ·  Grok = cloud GPUs",
        "Stack:  TUI -> ASCENT (P0+P5) -> optional P9 RS  ->  TLS  ->  IP  ->  dish/fiber  ->  api.x.ai",
    ]
    yy = 1218
    for line in truth:
        draw.text((76, yy), line, font=f_tiny, fill=(180, 220, 235, 255))
        yy += 20

    modes = [
        ("CLOUD", "api.x.ai up", mint),
        ("EDGE", "local model", cyan),
        ("QUEUE", "store-forward", amber),
        ("DEAD", "honest fail", violet),
    ]
    mx = 76
    for lab, sub, col in modes:
        rr(draw, (mx, 1264, mx + 250, 1324), 10, panel2, (*col, 130), 2)
        draw.text((mx + 14, 1276), lab, font=f_mono, fill=(*col, 255))
        draw.text((mx + 14, 1300), sub, font=f_body, fill=(*muted, 255))
        mx += 268

    phases = [
        ("P0", "Lab BER + queue"),
        ("P1", "Dual-mode CLI (stock kit)"),
        ("P2", "Edge + optional DTN ADU"),
        ("P3", "Deep-space partnership"),
    ]
    mx = 76
    for lab, sub in phases:
        draw.text((mx, 1344), lab, font=f_small, fill=(*amber, 255))
        draw.text((mx + 36, 1344), sub, font=f_body, fill=(*muted, 255))
        mx += 280

    draw.text(
        (76, 1380),
        "Kill: space Grok fantasy · Dishy RF reverse-engineer · ASCENT-as-router · 7B = frontier",
        font=f_tiny,
        fill=(200, 160, 140, 255),
    )
    draw.text(
        (76, 1408),
        "Works today: regional last-mile failover + edge brain + erase-on-fail spool. Not global collapse Grok.",
        font=f_tiny,
        fill=(*muted, 255),
    )
    draw.text(
        (76, 1432),
        "docs/GROK-ASCENT-STARLINK-ARCHITECTURE.md  ·  examples/ascent_starlink_client/",
        font=f_tiny,
        fill=(*cyan, 200),
    )

    # Footer
    draw.text((56, 1472), "ascent.jonbailey.xyz", font=f_mono, fill=(*cyan, 255))
    draw.text(
        (56, 1504),
        "Keep every classic ASCII byte sacred. Ascend the rest without burning the stairs.",
        font=f_body,
        fill=(*muted, 255),
    )
    draw.text(
        (56, 1542),
        "SPEC 1.0.0-rc1  ·  packing Cont 0xA0-0xBF  ·  Pitchfork-and-Torch  ·  @suddenlyjon",
        font=f_tiny,
        fill=(*muted, 200),
    )
    draw.text((W - 200, 1542), f"v{VERSION}", font=f_mono, fill=(*mint, 255))
    draw.text(
        (56, 1576),
        "pip/npm install ascent-wire  ·  GitHub Pitchfork-and-Torch/ascent  ·  MIT",
        font=f_tiny,
        fill=(*muted, 180),
    )
    draw.text(
        (56, 1608),
        "Nexus 3.0: cmdk palette · mission HUD · captain log · timeline · density · Fontshare · dual editors",
        font=f_tiny,
        fill=(*muted, 160),
    )

    out = img.convert("RGB")
    docs = ROOT / "docs"
    pub = ROOT / "site" / "public"
    masters = ROOT / "assets" / "masters"
    for d in (docs, pub, masters):
        d.mkdir(parents=True, exist_ok=True)

    targets = [
        docs / "ascent-infographic.png",
        docs / "ascent-infographic.jpg",
        pub / "infographic.png",
        pub / "infographic.jpg",
        masters / "ascent-infographic.png",
        masters / "ascent-infographic.jpg",
    ]
    for p in targets:
        if p.suffix.lower() == ".png":
            out.save(p, "PNG", optimize=True)
        else:
            out.save(p, "JPEG", quality=93, optimize=True, progressive=True)
        print("wrote", p, p.stat().st_size)

    # Banner: crop header + pillars for social
    crop = out.crop((0, 0, 1200, 630))
    for p in (
        docs / "ascent-infographic-banner.jpg",
        pub / "infographic-banner.jpg",
        masters / "ascent-infographic-banner.jpg",
    ):
        crop.save(p, "JPEG", quality=93, optimize=True)
        print("wrote", p)


if __name__ == "__main__":
    main()
