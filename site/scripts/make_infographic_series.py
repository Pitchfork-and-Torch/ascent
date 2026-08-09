#!/usr/bin/env python3
"""ASCENT integration infographic series for Desktop + docs.

Standing: after every major ASCENT update, bump SERIES_VER, regenerate, ship site+repo.
ASCII hyphens only. Deep-space instrument palette.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
W, H = 1200, 1500
SERIES_VER = "2.0.3"
OUT_DESK = Path.home() / "Desktop" / "ASCENT-infographics"
OUT_DOCS = ROOT / "docs" / "series"


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


# Palette
BG = (10, 10, 15)
PANEL = (16, 16, 24, 255)
MINT = (0, 229, 192)
CYAN = (61, 214, 255)
AMBER = (240, 180, 41)
VIOLET = (139, 124, 255)
TEXT = (232, 234, 240)
MUTED = (139, 144, 165)
WHITE = (245, 246, 250)


def top_bar(draw):
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


def footer(draw, page: str, total: int):
    f = mono(14)
    draw.text((56, H - 70), "ascent.jonbailey.xyz  ·  Pitchfork-and-Torch  ·  MIT", font=f, fill=(*VIOLET, 255))
    draw.text((56, H - 42), "Keep every classic ASCII byte sacred.", font=font(18), fill=(*MUTED, 255))
    draw.text((W - 160, H - 42), f"{page}/{total}", font=mono(16), fill=(*MINT, 255))


def base(title: str, kicker: str):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img, "RGBA")
    top_bar(draw)
    draw.text((56, 28), kicker, font=mono(16), fill=(*MINT, 255))
    draw.text((56, 64), title, font=font(48, bold=True), fill=(*WHITE, 255))
    return img, draw


def card(draw, box, title, lines, accent=MINT):
    rr(draw, box, 12, PANEL, (*accent, 100), 2)
    draw.rectangle((box[0], box[1], box[0] + 5, box[3]), fill=(*accent, 230))
    x, y = box[0] + 18, box[1] + 14
    draw.text((x, y), title, font=font(22, bold=True), fill=(*accent, 255))
    y += 40
    for line in lines:
        draw.text((x, y), line, font=font(18), fill=(*MUTED, 255))
        y += 28


def panel_01_what():
    img, draw = base("What is ASCENT?", f"SERIES 01  ·  INTEGRATION OVERVIEW  ·  v{SERIES_VER}")
    draw.text(
        (56, 140),
        "ASCII Successor with Compatible Encoding of Named Text",
        font=font(22),
        fill=(*MUTED, 255),
    )
    rr(draw, (56, 190, W - 56, 300), 14, PANEL, (*MINT, 150), 2)
    draw.text((76, 210), "ETERNAL PARSE LAW", font=mono(14), fill=(*MINT, 255))
    draw.text(
        (76, 245),
        "if byte < 0x80  ->  classic 7-bit ASCII, width 1, forever",
        font=mono(20),
        fill=(200, 240, 220, 255),
    )
    pillars = [
        ("Sacred P0", "0x00-0x7F never remapped.\nGreppers and shebangs\nstill work.", MINT),
        ("Agents", "ROLE TOOL THINK\nSAFETY HANDOFF\non the same stream.", CYAN),
        ("Multimodal", "REF INLINE CHUNK\ncontent-addressed\nmedia units.", AMBER),
        ("Deep space", "P9 outer RS frame.\nParity fail = erase.\nNo mojibake.", VIOLET),
    ]
    for i, (t, b, c) in enumerate(pillars):
        x = 56 + (i % 2) * 560
        y = 340 + (i // 2) * 280
        card(draw, (x, y, x + 520, y + 250), t, b.split("\n"), c)
    draw.text(
        (56, 940),
        "Not \"Unicode but better.\" A wire contract for humans, agents, and deep space.",
        font=font(22),
        fill=(*TEXT, 255),
    )
    draw.text(
        (56, 1000),
        "Profiles: ASCENT-7 (identity) · E (Earth) · D (deep-space ECC) · A (archive)",
        font=font(20),
        fill=(*MUTED, 255),
    )
    footer(draw, "01", 8)
    return img


def panel_02_stack():
    img, draw = base("The integration stack", f"SERIES 02  ·  WHAT SHIPS TOGETHER  ·  v{SERIES_VER}")
    draw.text((56, 140), "One monorepo, dual registries, one wire law.", font=font(22), fill=(*MUTED, 255))
    layers = [
        ("1  PUBLIC FACE", "ascent.jonbailey.xyz  ·  Nexus Wire Lab 2.0", "Dual text/hex, composers, tour, architecture explorer", MINT),
        ("2  SPEC RC", "SPEC.md 1.0.0-rc1  ·  freeze vectors", "Parse law, planes, agent/MM/P9 forms, RC checklist", CYAN),
        ("3  PYTHON / PyPI", "pip install ascent-wire", "CLI self-test, goldens, optional ASCENT-D RS", AMBER),
        ("4  JS / npm", "npm install ascent-wire", "Same packing as Python; JS lock tests must pass", VIOLET),
        ("5  DEEP SPACE", "ASCENT-D outer frame", "D5E5C0DE + RS(255,223) + erase-on-fail", MINT),
        ("6  DUAL-MODE", "Grok + Starlink resilience", "CLOUD / EDGE / QUEUE  ·  last-mile IP  ·  local edge when API dies", AMBER),
        ("7  ADOPTION", "docs/AGENT-LOOP.md + sat architecture", "Agent frames + dual-mode client skeleton", CYAN),
    ]
    y = 180
    for title, mid, bot, col in layers:
        rr(draw, (56, y, W - 56, y + 105), 12, PANEL, (*col, 90), 2)
        draw.text((76, y + 12), title, font=mono(14), fill=(*col, 255))
        draw.text((76, y + 36), mid, font=font(22, bold=True), fill=(*WHITE, 255))
        draw.text((76, y + 70), bot, font=font(17), fill=(*MUTED, 255))
        y += 115
    footer(draw, "02", 8)
    return img


def panel_03_lab():
    img, draw = base("Nexus Wire Lab 2.0", f"SERIES 03  ·  INTERACTIVE INSTRUMENT  ·  v{SERIES_VER}")
    draw.text((56, 140), "A living playground that makes the wire tangible.", font=font(22), fill=(*MUTED, 255))
    feats = [
        ("Dual editors", "Prose and hex stay synchronized live."),
        ("Byte map", "Each byte colored by plane; click to inspect."),
        ("Agent composer", "Insert ROLE / TOOL / THINK / SAFETY frames."),
        ("Multimodal", "Build REF, INLINE, and CHUNK units."),
        ("Deep-space sim", "Wrap, inject bit noise, watch erase-on-fail."),
        ("AEGIR sketch", "PQ algorithm registry + lab envelope shape."),
        ("Architecture", "Eleven planes linked to the current stream."),
        ("Tour + codegen", "2-minute path and Python/JS/Rust snippets."),
    ]
    for i, (t, d) in enumerate(feats):
        x = 56 + (i % 2) * 560
        y = 210 + (i // 2) * 200
        card(draw, (x, y, x + 520, y + 170), t, [d, "", "Open #lab on the live site."], CYAN if i % 2 else MINT)
    footer(draw, "03", 8)
    return img


def panel_04_agent():
    img, draw = base("Agent loop on the wire", f"SERIES 04  ·  LLM INTEGRATION  ·  v{SERIES_VER}")
    draw.text((56, 140), "Control tokens travel with the prose - fenced, skippable, greppable.", font=font(20), fill=(*MUTED, 255))
    steps = [
        "1  Prose as ASCENT-7 when every character is classic ASCII",
        "2  ROLE frame names the turn owner (guide, navigator, tool-runner)",
        "3  THINK stays opaque on shared logs (private reasoning)",
        "4  TOOL frame names the call; args stay length-declared",
        "5  SAFETY wraps untrusted tool results as data, never silent control",
        "6  MM REF points at large media by hash (do not inline megabytes)",
        "7  STOP ends the turn cleanly",
    ]
    y = 200
    for s in steps:
        rr(draw, (56, y, W - 56, y + 88), 10, PANEL, (*CYAN, 70), 1)
        draw.text((76, y + 28), s, font=font(22), fill=(*TEXT, 255))
        y += 100
    rr(draw, (56, y + 20, W - 56, y + 160), 12, PANEL, (*AMBER, 100), 2)
    draw.text((76, y + 40), "Canonical ROLE=guide wire", font=mono(14), fill=(*AMBER, 255))
    draw.text((76, y + 80), "9A C1 01 00 02 00 00 06 05 67 75 69 64 65 9B", font=mono(22), fill=(*WHITE, 255))
    draw.text((76, y + 120), "Guide: docs/AGENT-LOOP.md  ·  Sample: examples/agent-loop-demo.ascent.bin", font=font(16), fill=(*MUTED, 255))
    footer(draw, "04", 8)
    return img


def panel_05_d():
    img, draw = base("ASCENT-D deep space", f"SERIES 05  ·  ERASE-ON-FAIL TRANSPORT  ·  v{SERIES_VER}")
    draw.text((56, 140), "When bit error rate stops being theoretical.", font=font(22), fill=(*MUTED, 255))
    rr(draw, (56, 200, W - 56, 420), 14, PANEL, (*MINT, 100), 2)
    draw.text((76, 220), "OUTER FRAME", font=mono(14), fill=(*MINT, 255))
    lines = [
        "sync     D5 E5 C0 DE",
        "header   profile · family · n=255 · k=223 · interleave · crc",
        "body     length:u32be  ·  logical unit",
        "ecc      RS(255,223) codewords over CRC||unit",
    ]
    yy = 260
    for line in lines:
        draw.text((76, yy), line, font=mono(22), fill=(*TEXT, 255))
        yy += 36
    cards = [
        ("OK", "Parity and CRC verify.\nUnit accepted.", MINT),
        ("RECOVERED", "Clear unit damaged.\nRS restores authority.", AMBER),
        ("ERASED", "Uncorrectable damage.\nUnit discarded cleanly.", (255, 107, 138)),
    ]
    for i, (t, b, c) in enumerate(cards):
        x = 56 + i * 370
        card(draw, (x, 460, x + 350, 720), t, b.split("\n") + ["", "No mojibake best-effort."], c)
    draw.text((56, 780), "Browser lab and Python ref share the same RS poly (0x11d) and frame layout.", font=font(20), fill=(*MUTED, 255))
    draw.text((56, 840), "Golden lock: tests/freeze_vectors.json  ·  node tests/run_js_lock.js", font=mono(16), fill=(*CYAN, 255))
    draw.text((56, 920), "Why it matters for integration", font=font(26, bold=True), fill=(*WHITE, 255))
    for i, line in enumerate([
        "Hostile or long-haul links fail closed instead of corrupting agent text.",
        "Earth re-emit strips the outer frame and keeps the logical ASCENT unit.",
        "Missions can freeze alg sets; the outer wrap stays boring on purpose.",
    ]):
        draw.text((56, 980 + i * 50), f"-  {line}", font=font(20), fill=(*MUTED, 255))
    footer(draw, "05", 8)
    return img


def panel_06_package():
    img, draw = base("Python package + golden lock", f"SERIES 06  ·  IMPLEMENTER PATH  ·  v{SERIES_VER}")
    draw.text((56, 140), "Ship the wire as a library, not only a website.", font=font(22), fill=(*MUTED, 255))
    rr(draw, (56, 200, W - 56, 520), 14, PANEL, (*CYAN, 100), 2)
    draw.text((76, 220), "INSTALL", font=mono(14), fill=(*CYAN, 255))
    cmds = [
        "pip install -e \".[deep-space]\"",
        "ascent self-test",
        "ascent encode --header --role guide \"Hello, Universe.\"",
        "python -m ascent decode --file examples/hello-universe.ascent.bin",
    ]
    yy = 270
    for c in cmds:
        draw.text((76, yy), c, font=mono(22), fill=(*WHITE, 255))
        yy += 50
    card(draw, (56, 560, 560, 900), "Package", [
        "Name: ascent-wire",
        "Import: ascent",
        "CLI: ascent",
        "Optional: reedsolo for D",
        "Vendors ref/ for wheels",
    ], AMBER)
    card(draw, (600, 560, W - 56, 900), "Golden lock", [
        "Python: test_ascent_codec.py",
        "JS: run_js_lock.js",
        "Freeze: freeze_vectors.json",
        "P9 hex must match Python",
        "1-byte RS recovery checked",
    ], MINT)
    draw.text((56, 960), "JS and Python must stay bit-identical on Cont packing, Hello Universe,", font=font(20), fill=(*MUTED, 255))
    draw.text((56, 1000), "ROLE frames, and ASCENT-D outer frames - or the integration is lying.", font=font(20), fill=(*MUTED, 255))
    footer(draw, "06", 8)
    return img


def panel_07_hello():
    img, draw = base("Hello, Universe", f"SERIES 07  ·  132-BYTE CIVILIZATION KIT  ·  v{SERIES_VER}")
    draw.text((56, 140), "One valid ASCENT-E stream that greppers can still read.", font=font(22), fill=(*MUTED, 255))
    segs = [
        ("HEADER", "ASCENT/1.0\\n", "Greppable magic", MINT),
        ("TEXT", "Hello, Universe.\\n", "Sacred P0 prose", MINT),
        ("AGENT", "ROLE=guide", "Fenced control", CYAN),
        ("MEDIA", "MM REF + hash", "Content address", AMBER),
    ]
    for i, (lab, val, note, col) in enumerate(segs):
        y = 210 + i * 180
        rr(draw, (56, y, W - 56, y + 150), 12, PANEL, (*col, 110), 2)
        draw.text((76, y + 20), f"{i+1}  {lab}", font=mono(14), fill=(*col, 255))
        draw.text((76, y + 55), val, font=mono(28), fill=(*WHITE, 255))
        draw.text((76, y + 100), note, font=font(20), fill=(*MUTED, 255))
    draw.text((56, 1000), "ascent self-test  ->  132 bytes  ·  text + agent + multimodal", font=mono(18), fill=(*CYAN, 255))
    draw.text((56, 1060), "Live: Decode Hello, Universe on the Nexus lab in one click.", font=font(20), fill=(*MUTED, 255))
    footer(draw, "07", 8)
    return img


def panel_08_map():
    img, draw = base("How the pieces connect", f"SERIES 08  ·  END-TO-END MAP  ·  v{SERIES_VER}")
    draw.text((56, 140), "From idea to agent to deep space - same law the whole way.", font=font(22), fill=(*MUTED, 255))
    flow = [
        ("YOU / LLM", "Write prose +\nintent"),
        ("ENCODE", "ascent CLI\nor JS lab"),
        ("STREAM", "P0 + P5 +\nP6 units"),
        ("OPTIONAL D", "RS wrap\nerase-safe"),
        ("DECODE", "units back\nto meaning"),
    ]
    for i, (t, b) in enumerate(flow):
        x = 40 + i * 230
        accent = MINT if (i % 2 == 0) else CYAN
        rr(draw, (x, 220, x + 200, 400), 12, PANEL, (*accent, 100), 2)
        draw.text((x + 16, 250), t, font=font(18, bold=True), fill=(*WHITE, 255))
        for j, line in enumerate(b.split("\n")):
            draw.text((x + 16, 300 + j * 30), line, font=font(16), fill=(*MUTED, 255))
        if i < len(flow) - 1:
            draw.polygon([(x + 208, 300), (x + 222, 310), (x + 208, 320)], fill=(*MUTED, 200))
    draw.text((56, 460), "Repositories and surfaces", font=font(26, bold=True), fill=(*WHITE, 255))
    rows = [
        ("GitHub", "Pitchfork-and-Torch/ascent  ·  single-commit main  ·  MIT"),
        ("Live site", "https://ascent.jonbailey.xyz/  ·  CF Pages ascent-jonbailey"),
        ("Infographic", f"docs/ + Desktop series  ·  architecture card v{SERIES_VER}"),
        ("Freeze RC", "docs/SPEC-FREEZE-1.0-RC.md  ·  tests/freeze_vectors.json"),
        ("AEGIR", "design/AEGIR.md  ·  hybrid PQ companion (DEMO golden in CI)"),
    ]
    y = 520
    for k, v in rows:
        rr(draw, (56, y, W - 56, y + 90), 10, PANEL, (*VIOLET, 60), 1)
        draw.text((76, y + 16), k, font=mono(14), fill=(*VIOLET, 255))
        draw.text((76, y + 46), v, font=font(18), fill=(*TEXT, 255))
        y += 100
    draw.text((56, 1060), "Integration promise: sacred ASCII forever; everything else ascends without burning the stairs.", font=font(18), fill=(*MUTED, 255))
    footer(draw, "08", 8)
    return img


SERIES = [
    ("01-what-is-ascent", panel_01_what),
    ("02-integration-stack", panel_02_stack),
    ("03-wire-lab", panel_03_lab),
    ("04-agent-loop", panel_04_agent),
    ("05-ascent-d", panel_05_d),
    ("06-package-golden-lock", panel_06_package),
    ("07-hello-universe", panel_07_hello),
    ("08-end-to-end-map", panel_08_map),
]


def main() -> None:
    OUT_DESK.mkdir(parents=True, exist_ok=True)
    OUT_DOCS.mkdir(parents=True, exist_ok=True)
    index_lines = [
        f"ASCENT integration infographic series v{SERIES_VER}",
        "Generated for Desktop explainers + docs/series/",
        "",
    ]
    for name, fn in SERIES:
        img = fn().convert("RGB")
        for folder in (OUT_DESK, OUT_DOCS):
            png = folder / f"{name}.png"
            jpg = folder / f"{name}.jpg"
            img.save(png, "PNG", optimize=True)
            img.save(jpg, "JPEG", quality=92, optimize=True, progressive=True)
            print("wrote", png)
        index_lines.append(f"{name}.png")
    # README on desktop
    (OUT_DESK / "README.txt").write_text(
        "\n".join(
            [
                f"ASCENT integration infographic series (v{SERIES_VER})",
                "",
                "01 What is ASCENT - parse law and pillars",
                "02 Integration stack - face, SPEC, Python, JS, D, adoption",
                "03 Nexus Wire Lab 2.0 - interactive instrument",
                "04 Agent loop - ROLE TOOL THINK SAFETY",
                "05 ASCENT-D - RS outer frame erase-on-fail",
                "06 Package + golden lock - ascent-wire and JS parity",
                "07 Hello, Universe - 132-byte sample anatomy",
                "08 End-to-end map - how pieces connect",
                "",
                "Live: https://ascent.jonbailey.xyz/",
                "GitHub: https://github.com/Pitchfork-and-Torch/ascent",
                "ASCII hyphens only on product surfaces.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Desktop folder:", OUT_DESK)


if __name__ == "__main__":
    main()
