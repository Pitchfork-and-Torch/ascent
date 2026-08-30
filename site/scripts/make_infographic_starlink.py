#!/usr/bin/env python3
"""Horizontal ASCENT x Starlink interface infographic (exact text via Pillow).

ASCII hyphens only. Outputs docs/, site/public/, assets/masters/, Desktop.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
# Wide landscape for decks / README / Desktop
W, H = 2400, 1100
VERSION = "2.0.3"


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


def arrow(draw, x0, y, x1, col):
    """Simple right arrow mid-height."""
    mid = y
    draw.line([(x0, mid), (x1 - 10, mid)], fill=(*col, 220), width=3)
    draw.polygon(
        [(x1 - 12, mid - 8), (x1, mid), (x1 - 12, mid + 8)],
        fill=(*col, 220),
    )


def main() -> None:
    mint = (0, 229, 192)
    cyan = (61, 214, 255)
    amber = (240, 180, 41)
    violet = (139, 124, 255)
    text = (232, 234, 240)
    muted = (139, 144, 165)
    panel = (16, 16, 24, 255)
    panel2 = (20, 22, 32, 255)
    bg = (10, 10, 15)

    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img, "RGBA")

    # Top gradient bar
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
        draw.line([(x, 0), (x, 8)], fill=(r, g, b, 255))

    f_badge = mono(18)
    f_title = font(52, bold=True)
    f_sub = font(22)
    f_h = font(20, bold=True)
    f_body = font(18)
    f_mono = mono(16)
    f_small = mono(14)
    f_tiny = mono(13)

    # Header
    draw.text(
        (56, 28),
        f"ASCENT  x  STARLINK  ·  INTERFACE MAP  ·  v{VERSION}  ·  MIT",
        font=f_badge,
        fill=(*mint, 255),
    )
    draw.text((56, 68), "How Starlink carries ASCENT", font=f_title, fill=(*text, 255))
    draw.text(
        (56, 132),
        "Starlink is the last-mile IP pipe. ASCENT is the wire + agent session. Grok stays cloud compute (or local edge).",
        font=f_sub,
        fill=(*muted, 255),
    )

    # Truth strip
    rr(draw, (56, 180, W - 56, 248), 14, panel, (*mint, 120), 2)
    draw.text(
        (76, 200),
        "TRUTH:  dish != GPU   ·   laser mesh extends gateway reach (does not host Grok)   ·   stock kit only (no RF reverse-engineer)",
        font=f_mono,
        fill=(180, 245, 220, 255),
    )

    # --- Main horizontal stack ---
    draw.text((56, 280), "DATA PATH  (left to right)", font=f_h, fill=(*text, 255))

    stages = [
        ("1  TERMINAL", "Operator TUI\nCLI / daemon", "local PC", mint),
        ("2  ASCENT WIRE", "P0 prose + P5\nROLE TOOL STOP", "optional P9 RS", cyan),
        ("3  SESSION CRYPTO", "TLS 1.3 / QUIC\nHTTPS to API", "keys OOB / P7", violet),
        ("4  IP UNDERLAY", "Ethernet / Wi-Fi\nrouter failover", "fiber OR sat", amber),
        ("5  STARLINK", "User terminal\nKu RF to LEO", "ISL mesh optional", cyan),
        ("6  EGRESS", "Gateway + PoP\npublic Internet", "must be alive", amber),
        ("7  BRAIN", "api.x.ai Grok\nOR edge LLM", "CLOUD / EDGE", mint),
    ]

    n = len(stages)
    gap = 18
    margin = 56
    usable = W - 2 * margin - (n - 1) * gap
    cw = usable // n
    y0, ch = 320, 280
    centers = []

    for i, (title, body, foot, col) in enumerate(stages):
        x = margin + i * (cw + gap)
        centers.append(x + cw // 2)
        rr(draw, (x, y0, x + cw, y0 + ch), 16, panel, (*col, 130), 2)
        draw.rectangle((x, y0, x + 6, y0 + ch), fill=(*col, 230))
        draw.text((x + 16, y0 + 16), title, font=f_small, fill=(*col, 255))
        by = y0 + 56
        for line in body.split("\n"):
            draw.text((x + 16, by), line, font=f_body, fill=(*text, 255))
            by += 28
        draw.text((x + 16, y0 + ch - 40), foot, font=f_tiny, fill=(*muted, 255))

    # Arrows between stage tops
    for i in range(n - 1):
        x0 = margin + i * (cw + gap) + cw
        x1 = margin + (i + 1) * (cw + gap)
        arrow(draw, x0 + 2, y0 + ch // 2, x1 - 2, muted)

    # Layer labels under stack
    draw.text((56, 620), "WHAT EACH LAYER OWNS", font=f_h, fill=(*text, 255))

    owns = [
        ("ASCENT owns", "Parse law (byte < 0x80 = ASCII forever)\nAgent frames, MM REF, ASCENT-D erase-on-fail\nSession ADUs and queue files", mint),
        ("Starlink owns", "RF link, satellite mesh, last-mile IP\nDish power + sky + account\nPath to a live SpaceX gateway / PoP", cyan),
        ("Grok / edge owns", "Inference only (cloud GPUs or local model)\nNot on the dish; not inside ASCENT bytes\nAPI key + TLS endpoint reachability", amber),
    ]
    ow = (W - 112 - 2 * 20) // 3
    for i, (t, b, col) in enumerate(owns):
        x = 56 + i * (ow + 20)
        rr(draw, (x, 656, x + ow, 820), 14, panel2, (*col, 100), 2)
        draw.text((x + 20, 672), t, font=f_h, fill=(*col, 255))
        by = 712
        for line in b.split("\n"):
            draw.text((x + 20, by), line, font=f_body, fill=(*muted, 255))
            by += 28

    # Modes row
    draw.text((56, 850), "DUAL-MODE WHEN THE PATH CHANGES", font=f_h, fill=(*text, 255))
    modes = [
        ("CLOUD", "api.x.ai reachable\nvia fiber or Starlink", mint),
        ("EDGE", "API down; local\nOllama / edge model", cyan),
        ("QUEUE", "Link flaps; spool\nASCENT ADUs to disk", amber),
        ("DEAD", "No power / sky / model\nhonest fail", violet),
    ]
    mw = (W - 112 - 3 * 16) // 4
    for i, (lab, desc, col) in enumerate(modes):
        x = 56 + i * (mw + 16)
        rr(draw, (x, 886, x + mw, 1000), 12, panel, (*col, 120), 2)
        draw.text((x + 18, 902), lab, font=f_mono, fill=(*col, 255))
        by = 938
        for line in desc.split("\n"):
            draw.text((x + 18, by), line, font=f_body, fill=(*muted, 255))
            by += 26

    # Footer
    draw.text(
        (56, 1030),
        "ascent.jonbailey.xyz  ·  docs/GROK-ASCENT-STARLINK-ARCHITECTURE.md  ·  examples/ascent_starlink_client/",
        font=f_mono,
        fill=(*cyan, 255),
    )
    draw.text(
        (56, 1062),
        "Phase 0 lab  ·  Phase 1 dual-mode CLI (stock kit)  ·  Phase 2 edge+DTN lab  ·  Phase 3 partnership only",
        font=f_tiny,
        fill=(*muted, 200),
    )
    draw.text((W - 220, 1062), f"v{VERSION}", font=f_mono, fill=(*mint, 255))

    out = img.convert("RGB")
    docs = ROOT / "docs"
    pub = ROOT / "site" / "public"
    masters = ROOT / "assets" / "masters"
    desk = Path.home() / "Desktop" / "ASCENT-infographics"
    for d in (docs, pub, masters, desk):
        d.mkdir(parents=True, exist_ok=True)

    names = [
        "ascent-starlink-interface.png",
        "ascent-starlink-interface.jpg",
    ]
    targets = []
    for name in names:
        targets += [
            docs / name,
            pub / name,
            masters / name,
            desk / name,
        ]
    for p in targets:
        if p.suffix.lower() == ".png":
            out.save(p, "PNG", optimize=True)
        else:
            out.save(p, "JPEG", quality=93, optimize=True, progressive=True)
        print("wrote", p, p.stat().st_size)

    # Also a 1200-wide half-scale for tight embeds
    half = out.resize((1200, 550), Image.Resampling.LANCZOS)
    for p in (
        docs / "ascent-starlink-interface-1200.jpg",
        pub / "ascent-starlink-interface-1200.jpg",
        desk / "ascent-starlink-interface-1200.jpg",
    ):
        half.save(p, "JPEG", quality=92, optimize=True)
        print("wrote", p)


if __name__ == "__main__":
    main()
