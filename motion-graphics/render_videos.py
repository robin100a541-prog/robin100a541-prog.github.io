#!/usr/bin/env python3
"""
Six Pillars — Premium Glass Card motion graphics.
Black background, 1080x1920, 30fps, 3s.
DaVinci Resolve: place above footage → Inspector → Composite Mode → SCREEN
"""

from PIL import Image, ImageDraw, ImageFont
import subprocess, os, math, shutil

OUT_DIR   = "/home/user/robin-/motion-graphics/videos"
FRAME_DIR = "/home/user/robin-/motion-graphics/_frames"
W, H      = 1080, 1920
FPS       = 30
FRAMES    = 90   # 3 seconds

os.makedirs(OUT_DIR, exist_ok=True)

# ── Easing ────────────────────────────────────────────────────────────────────

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def prog(frame, start_s, dur_s):
    return clamp((frame / FPS - start_s) / dur_s)

def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3

def ease_out_back(t):
    """Cubic ease-out with slight overshoot — snappy premium pop."""
    t = clamp(t)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

# ── Font ──────────────────────────────────────────────────────────────────────

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def tsize(draw, txt, fnt):
    bb = draw.textbbox((0, 0), txt, font=fnt)
    return bb[2] - bb[0], bb[3] - bb[1]

def draw_tc(draw, txt, cx, cy, fnt, rgb, a=255):
    tw, th = tsize(draw, txt, fnt)
    r, g, b = rgb
    draw.text((cx - tw // 2, cy - th // 2), txt, font=fnt, fill=(r, g, b, a))

# ── Compositing fix ───────────────────────────────────────────────────────────

def finalize(img):
    """Properly composite RGBA layers over black background → RGB."""
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    return Image.alpha_composite(black, img).convert("RGB")

# ── Glass panel ───────────────────────────────────────────────────────────────

def draw_glass(draw, cx, cy, pw, ph, pop_p, accent_rgb, radius=30):
    """
    Premium frosted-glass card.  pop_p 0→1 drives spring scale-in.
    Works with Screen blend mode in DaVinci — dark panel frosting,
    bright white border/glow, full-brightness text.
    """
    scale = clamp(ease_out_back(pop_p), 0.0, 1.08)
    w  = int(pw * scale)
    h  = int(ph * scale)
    if w < 4 or h < 4:
        return 0, 0, W, H
    x0 = cx - w // 2;  y0 = cy - h // 2
    x1 = cx + w // 2;  y1 = cy + h // 2

    fade = clamp(pop_p * 2.2)   # alpha envelope
    r, g, b = accent_rgb

    # ── Colour glow halo (soft layers outward)
    for i in range(8, 0, -1):
        pad = i * 10
        a   = int(40 * fade * (i / 8))
        draw.rounded_rectangle(
            [x0-pad, y0-pad, x1+pad, y1+pad],
            radius=radius+pad, fill=(r, g, b, a))

    # ── White soft halo (depth / inner light)
    for i in range(5, 0, -1):
        pad = i * 5
        a   = int(18 * fade)
        draw.rounded_rectangle(
            [x0-pad, y0-pad, x1+pad, y1+pad],
            radius=radius+pad, fill=(255, 255, 255, a))

    # ── Glass body fill (frosted, very subtle over black)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius,
                           fill=(255, 255, 255, int(38 * fade)))

    # ── Top-edge specular highlight (glass catching light)
    hl = min(h // 5, 70)
    if x1-2 > x0+2 and y0+hl > y0+2:
        draw.rounded_rectangle([x0+2, y0+2, x1-2, y0+hl],
                               radius=radius,
                               fill=(255, 255, 255, int(45 * fade)))

    # ── Crisp white border
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius,
                           outline=(255, 255, 255, int(200 * fade)), width=2)

    # ── Accent colour bar at bottom of panel
    lw = int(w * 0.52)
    draw.rectangle([cx - lw//2, y1-5, cx + lw//2, y1-2],
                   fill=(r, g, b, int(230 * fade)))

    return x0, y0, x1, y1

# ── Text reveal ───────────────────────────────────────────────────────────────

def reveal(draw, txt, cx, cy, fnt, rgb, p, slide=30):
    if p <= 0:
        return
    p2 = ease_out(p)
    a  = int(255 * clamp(p * 2.5))
    draw_tc(draw, txt, cx, cy + int(slide * (1 - p2)), fnt, rgb, a)

# ── hex to rgb ────────────────────────────────────────────────────────────────

def h2r(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# ── Scene renderers ───────────────────────────────────────────────────────────

def render_intro(frame):
    img  = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img, "RGBA")
    gold = (255, 215, 0)
    cx, cy = W // 2, H // 2

    # Glass card
    pop_p = prog(frame, 0.0, 0.40)
    draw_glass(draw, cx, cy, 840, 540, pop_p, gold)

    fade = clamp(pop_p * 2.2)

    # Thin divider line inside card
    div_p = ease_out(prog(frame, 0.20, 0.28))
    if div_p > 0:
        lw = int(560 * div_p)
        a  = int(90 * div_p)
        draw.rectangle([cx - lw//2, cy - 12, cx + lw//2, cy - 9],
                       fill=(255, 255, 255, a))

    # "SIX"
    reveal(draw, "SIX",         cx, cy - 135, font(200), gold,        prog(frame, 0.08, 0.35), slide=50)
    # "PILLARS"
    reveal(draw, "PILLARS",     cx, cy + 55,  font(122), (255,255,255), prog(frame, 0.20, 0.35), slide=35)
    # "OF FOOTBALL"
    reveal(draw, "OF FOOTBALL", cx, cy + 148, font(42),  gold,        prog(frame, 0.32, 0.32), slide=22)

    return finalize(img)


def render_pillar(frame, num, name, color_hex):
    img  = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img, "RGBA")
    acc   = h2r(color_hex)
    white = (255, 255, 255)
    mid   = (190, 190, 190)
    cx, cy = W // 2, H // 2

    # Auto font size so long names fit
    name_fs = {
        "TECHNICAL": 108, "PHYSICAL": 108,
        "TACTICAL":  122, "HOLISTIC": 116,
        "HEALTH":    148, "MENTAL":   148,
    }.get(name, 118)

    # Glass card
    pop_p = prog(frame, 0.0, 0.38)
    draw_glass(draw, cx, cy, 860, 570, pop_p, acc)

    # "PILLAR XX" badge
    p_b = prog(frame, 0.10, 0.30)
    if p_b > 0:
        p2 = ease_out(p_b)
        a  = int(255 * clamp(p_b * 2.5))
        fx = int(24 * (1 - p2))
        f  = font(40)
        txt = f"PILLAR  {num}"
        tw, th = tsize(draw, txt, f)
        bx = cx - tw // 2 - fx
        by = cy - 202
        r, g, b = acc
        draw.text((bx, by), txt, font=f, fill=(r, g, b, a))
        uw = int(tw * 0.52)
        draw.rectangle([cx - uw//2, by+th+5, cx + uw//2, by+th+8],
                        fill=(r, g, b, int(a * 0.65)))

    # Thin divider
    div_p = ease_out(prog(frame, 0.18, 0.26))
    if div_p > 0:
        lw = int(490 * div_p)
        draw.rectangle([cx - lw//2, cy-148, cx + lw//2, cy-145],
                       fill=(255, 255, 255, int(60 * div_p)))

    # "THE"
    reveal(draw, "THE",    cx, cy - 105, font(36),     mid,   prog(frame, 0.18, 0.28), slide=18)
    # Main name
    reveal(draw, name,     cx, cy + 8,   font(name_fs),white, prog(frame, 0.26, 0.36), slide=45)
    # "PILLAR" subtitle
    reveal(draw, "PILLAR", cx, cy + 148, font(50),     acc,   prog(frame, 0.36, 0.32), slide=25)

    return finalize(img)

# ── Scenes ────────────────────────────────────────────────────────────────────

SCENES = [
    ("00_six_pillars_intro", None, None,        None),
    ("01_technical_pillar",  "01", "TECHNICAL", "#00C2FF"),
    ("02_tactical_pillar",   "02", "TACTICAL",  "#FF6B35"),
    ("03_health_pillar",     "03", "HEALTH",    "#39D353"),
    ("04_physical_pillar",   "04", "PHYSICAL",  "#FF2D55"),
    ("05_mental_pillar",     "05", "MENTAL",    "#BF5AF2"),
    ("06_holistic_pillar",   "06", "HOLISTIC",  "#FFD700"),
]

# ── Render ────────────────────────────────────────────────────────────────────

for slug, num, name, color in SCENES:
    print(f"Rendering {slug}...", flush=True)
    fd = os.path.join(FRAME_DIR, slug)
    os.makedirs(fd, exist_ok=True)

    for f in range(FRAMES):
        img = render_intro(f) if not num else render_pillar(f, num, name, color)
        img.save(os.path.join(fd, f"frame_{f:04d}.png"))

    out = os.path.join(OUT_DIR, f"{slug}.mov")
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(fd, "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "16",
        out
    ], capture_output=True)
    shutil.rmtree(fd)
    print(f"  → {out}  ({os.path.getsize(out)/1e6:.1f} MB)", flush=True)

print("\nDone. DaVinci Resolve: clip above footage → Composite Mode → SCREEN")
