"""Flow diagram (LinkedIn / share asset): a standard LLM vs a System One model (Kenning) in a
decision pipeline, with the white S1 logo composited as a faint watermark.

    python scripts/make_flow.py [out.png]      # defaults to public/diagrams/llm-vs-system-one.png
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parents[1]
LOGO = REPO / "public" / "white_s1_logo.png"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "public" / "diagrams" / "llm-vs-system-one.png"
FONT = r"C:\Windows\Fonts\CascadiaCode.ttf"   # Cascadia Code (variable); adjust per machine

W, H, S = 1200, 1200, 2
BG, SURFACE, BORDER = "#14181c", "#1a1f25", "#2c343d"
ACCENT, ACCENT_HIGH = "#2b6cb0", "#a9c9ea"
WHITE, GRAY2, GRAY3 = "#f5f7fa", "#b6c2d1", "#8996a8"
RED, AMBER, GREEN = "#e06c6c", "#d9a441", "#5fb37c"
WATERMARK_OPACITY = 0.07


def f(size, weight="Regular"):
    ft = ImageFont.truetype(FONT, size * S)
    try:
        ft.set_variation_by_name(weight)
    except Exception:
        pass
    return ft


img = Image.new("RGB", (W * S, H * S), BG)
glow = Image.new("RGB", img.size, BG)
ImageDraw.Draw(glow).ellipse([600 * S, -200 * S, 1500 * S, 700 * S], fill="#1b3350")
img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(180 * S)), 0.8)
d = ImageDraw.Draw(img)


def text(x, y, s, font, fill=WHITE, anchor="la"):
    d.text((x * S, y * S), s, font=font, fill=fill, anchor=anchor)


def box(x, y, w, h, outline=BORDER, fill=SURFACE, width=2):
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=14 * S, fill=fill, outline=outline, width=width * S)


def arrow(x, y1, y2, color=GRAY3):
    d.line([(x * S, y1 * S), (x * S, (y2 - 9) * S)], fill=color, width=3 * S)
    d.polygon([((x - 8) * S, (y2 - 12) * S), ((x + 8) * S, (y2 - 12) * S), (x * S, y2 * S)], fill=color)


# title
text(60, 56, "Same decision, two architectures", f(40, "Bold"))
text(60, 112, '"Is this email phishing?", in an automated pipeline', f(22), GRAY2)

COLS = [(60, "Standard LLM (generative)", RED), (630, "System One model (Kenning)", ACCENT_HIGH)]
for x, title, color in COLS:
    text(x, 172, title, f(25, "Bold"), color)

CW = 510
llm = [
    ("Write a prompt", 'You are a classifier. ONLY RETURN JSON:\n{"label": ..., "confidence": ...}', GRAY2),
    ("Generate text, token by token", "seconds per decision", AMBER),
    ("Parse the JSON", "malformed? missing fence? \u2192 retry", AMBER),
    ("Validate the label", 'invented "suspicious_maybe"? \u2192 fallback', AMBER),
    ('Read "confidence": 0.95', "a number the model wrote down,\nnot a measured probability", RED),
]
sys1 = [
    ("Send state + typed questions", "your JSON as-is + Noul / Choice / Score", GRAY2),
    ("One pass scores every option", "~35 ms on one consumer GPU", GREEN),
    ("A probability for every answer", None, GREEN),
    ("Act on calibrated thresholds", "\u2265 0.90 act  \u00b7  \u2264 0.10 close\neverything else \u2192 a person", GREEN),
]

y0, step, bh = 222, 152, 116
for i, (title, sub, color) in enumerate(llm):
    y = y0 + i * step
    box(60, y, CW, bh)
    text(84, y + 20, title, f(22, "SemiBold"))
    for j, line in enumerate(sub.split("\n")):
        text(84, y + 56 + j * 26, line, f(17), color)
    if i < len(llm) - 1:
        arrow(60 + CW // 2, y + bh, y + step)

heights = [bh, bh, bh + 36, bh]
span = 4 * step + bh                      # same top and bottom as the left column
gap = (span - sum(heights)) / 3
tops = [y0 + sum(heights[:k]) + k * gap for k in range(4)]
for i, (title, sub, color) in enumerate(sys1):
    y = int(tops[i])
    h = heights[i]
    box(630, y, CW, h, outline=ACCENT if i else BORDER)
    text(654, y + 20, title, f(22, "SemiBold"))
    if sub:
        for j, line in enumerate(sub.split("\n")):
            text(654, y + 56 + j * 26, line, f(17), color)
    else:
        bars = [("yes", 0.90, ACCENT), ("no", 0.10, "#55616f")]
        for j, (lab, p, c) in enumerate(bars):
            by = y + 60 + j * 34
            text(654, by, lab, f(17), GRAY2)
            bx = 790
            d.rounded_rectangle([bx * S, (by + 2) * S, (bx + 260) * S, (by + 20) * S], radius=9 * S, fill="#23292f")
            d.rounded_rectangle([bx * S, (by + 2) * S, (bx + int(260 * p)) * S, (by + 20) * S], radius=9 * S, fill=c)
            text(bx + 270, by, f"{p:.2f}", f(17), WHITE)
    if i < len(sys1) - 1:
        arrow(630 + CW // 2, y + h, int(tops[i + 1]), ACCENT)

# summary row
ys = y0 + 5 * step - 10
box(60, ys, CW, 132, outline=RED)
for j, line in enumerate(["seconds per decision", "a parser and a retry loop", "output can be malformed or invented", "confidence you can't trust"]):
    text(84, ys + 18 + j * 27, "\u00d7 " + line, f(18), GRAY2)
box(630, ys, CW, 132, outline=ACCENT)
for j, line in enumerate(["milliseconds per decision", "nothing to parse, nothing to retry", "always one of your options", "probabilities you can measure"]):
    text(654, ys + 18 + j * 27, "\u2713 " + line, f(18), WHITE)

# footer
text(60, H - 62, "Kenning v0.6 \u00b7 open source (Apache-2.0) \u00b7 real output from the quickstart email", f(17), GRAY3)
text(W - 60, H - 62, "systemone.dev", f(20, "SemiBold"), ACCENT_HIGH, anchor="ra")

# watermark: faint white S1 logo, centered
wm = Image.open(LOGO).convert("RGBA")
wsz = 760 * S
wm = wm.resize((wsz, wsz), Image.LANCZOS)
r, g, b, aa = wm.split()
aa = aa.point(lambda v: int(v * WATERMARK_OPACITY))
wm = Image.merge("RGBA", (r, g, b, aa))
base = img.convert("RGBA")
base.alpha_composite(wm, ((img.width - wsz) // 2, (img.height - wsz) // 2))
img = base.convert("RGB")

img = img.resize((W, H), Image.LANCZOS)
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, optimize=True)
print("wrote", OUT)
