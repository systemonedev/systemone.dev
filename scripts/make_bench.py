"""Benchmark card (LinkedIn / share asset): Kenning v0.6 vs Clef and Jev on the general suite,
as a table. Numbers are verbatim from systemone-builder docs/kenning.md (as-served cascade; the
0.720 figure needs an oracle router). Latency for v0.6 is an estimate (see footer).

    python scripts/make_bench.py [out.png]      # defaults to public/diagrams/kenning-v06-benchmark.png
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parents[1]
LOGO = REPO / "public" / "white_s1_logo.png"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "public" / "diagrams" / "kenning-v06-benchmark.png"
FONT = r"C:\Windows\Fonts\CascadiaCode.ttf"   # Cascadia Code (variable); adjust per machine

W, H, S = 1200, 1200, 2
BG, SURFACE, BORDER = "#14181c", "#1a1f25", "#2c343d"
ACCENT, ACCENT_HIGH = "#2b6cb0", "#a9c9ea"
WHITE, GRAY2, GRAY3 = "#f5f7fa", "#b6c2d1", "#8996a8"
GREEN = "#5fb37c"
COL_BAND = "#1b2838"          # faint highlight behind the v0.6 column
ZEBRA = "#171c21"
WATERMARK_OPACITY = 0.06

# label, v0.6, v0.5, clef, jev, kind
DATA = [
    ("Macro accuracy", 0.688, 0.653, 0.791, 0.830, "macro"),
    ("Agent", 0.867, 0.727, 0.793, 0.900, "fam"),
    ("Conversation", 1.000, 0.979, 1.000, 1.000, "fam"),
    ("Answer quality", 0.479, 0.479, 0.447, 0.498, "fam"),
    ("Text", 0.778, 0.756, 0.841, 0.834, "fam"),
    ("Tables", 0.740, 0.520, 0.860, 0.940, "fam"),
    ("Records", 0.654, 0.587, 0.857, 0.921, "fam"),
    ("Logs", 0.520, 0.520, 0.740, 0.720, "fam"),
    ("Latency  p50", None, None, None, None, "lat"),
]
LAT = ["~35 ms*", "35 ms", "125 ms", "152 ms"]   # v0.6 reflex | v0.5 | clef | jev
HEADERS = ["Kenning v0.6", "v0.5", "Clef-flash", "Jev"]


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


def rect(x0, y0, x1, y1, fill=None, outline=None, width=1, radius=0):
    d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=radius * S, fill=fill, outline=outline,
                        width=width * S)


# title
text(60, 54, "Kenning v0.6 vs the big engines", f(40, "Bold"))
text(60, 110, "General benchmark \u00b7 1,328 held-out items \u00b7 30 questions \u00b7 macro accuracy", f(18), GRAY2)

# geometry
FX = 60                     # family text x
C0 = 372                    # first engine column left edge
CW = (1140 - C0) / 4        # column width
centers = [C0 + CW * (i + 0.5) for i in range(4)]
TY, HH, RH = 176, 66, 80    # table top, header height, row height
bottom = TY + HH + len(DATA) * RH

# v0.6 column highlight band (behind everything in the table)
rect(C0, TY, C0 + CW, bottom, fill=COL_BAND, radius=12)

# zebra for family rows
for k, (_, *_rest) in enumerate(DATA):
    if DATA[k][5] == "fam" and k % 2 == 1:
        ry = TY + HH + k * RH
        rect(FX, ry, C0, ry + RH, fill=ZEBRA)            # left of the band only (band stays clean)
        rect(C0 + CW, ry, 1140, ry + RH, fill=ZEBRA)

# header
text(FX + 24, TY + HH / 2, "Decision family", f(16), GRAY3, anchor="lm")
for i, hdr in enumerate(HEADERS):
    text(centers[i], TY + HH / 2, hdr, f(19, "SemiBold"), ACCENT_HIGH if i == 0 else GRAY2, anchor="mm")
d.line([(FX * S, (TY + HH) * S), (1140 * S, (TY + HH) * S)], fill=BORDER, width=2 * S)

# rows
for k, (label, v6, v5, cl, jv, kind) in enumerate(DATA):
    ry = TY + HH + k * RH
    cy = ry + RH / 2
    if kind == "lat":
        d.line([(FX * S, ry * S), (1140 * S, ry * S)], fill=BORDER, width=2 * S)
    # family / row label
    lab_w = "Bold" if kind == "macro" else "SemiBold"
    text(FX + 24, cy, label, f(21 if kind == "macro" else 20, lab_w),
         WHITE if kind != "lat" else GRAY2, anchor="lm")
    if kind == "macro":
        text(centers[0], cy + 22, "as served", f(13), GRAY3, anchor="mm")
    # cells
    if kind == "lat":
        vals = LAT
        best = min(range(4), key=lambda i: float(LAT[i].strip("~ ms*")))
        for i, sval in enumerate(vals):
            if i == 0:
                col, wt = ACCENT_HIGH, "SemiBold"
            elif i == best:
                col, wt = WHITE, "SemiBold"
            else:
                col, wt = GRAY2, "Regular"
            text(centers[i], cy, sval, f(22, wt), col, anchor="mm")
        continue
    nums = [v6, v5, cl, jv]
    mx = max(nums)
    sz = 26 if kind == "macro" else 23
    for i, val in enumerate(nums):
        if i == 0:
            col = GREEN if v6 >= cl else ACCENT_HIGH
            wt = "Bold" if kind == "macro" else "SemiBold"
        elif abs(val - mx) < 1e-9:
            col, wt = WHITE, "SemiBold"
        else:
            col, wt = GRAY2, "Regular"
        text(centers[i], cy, f"{val:.3f}", f(sz, wt), col, anchor="mm")

# v0.6 band outline on top
rect(C0, TY, C0 + CW, bottom, outline=ACCENT, width=2, radius=12)

# footer
text(60, H - 84, "v0.6 = Kenning-XL cascade, served 0.688 (0.720 with an oracle router)  \u00b7  "
     "green = matches or beats Clef", f(14), GRAY3)
text(60, H - 58, "* v0.6 shown is the reflex pass (~35 ms, measured); the deliberate pass that lifts "
     "records/tables is slower  \u00b7  Apache-2.0", f(14), GRAY3)
text(W - 60, H - 58, "systemone.dev", f(20, "SemiBold"), ACCENT_HIGH, anchor="ra")

# watermark
wm = Image.open(LOGO).convert("RGBA")
wsz = 720 * S
wm = wm.resize((wsz, wsz), Image.LANCZOS)
r, g, b, aa = wm.split()
aa = aa.point(lambda v: int(v * WATERMARK_OPACITY))
wm = Image.merge("RGBA", (r, g, b, aa))
base = img.convert("RGBA")
base.alpha_composite(wm, ((img.width - wsz) // 2, (img.height - wsz) // 2 + 40 * S))
img = base.convert("RGB")

img = img.resize((W, H), Image.LANCZOS)
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, optimize=True)
print("wrote", OUT)
