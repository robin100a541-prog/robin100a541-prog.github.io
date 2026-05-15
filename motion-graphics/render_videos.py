#!/usr/bin/env python3
"""
Render Six Pillars motion graphics as green-screen MOV files for DaVinci Resolve.
Each animation is 3 seconds @ 30fps (90 frames), 1080x1920px.
"""

from PIL import Image, ImageDraw, ImageFont
import subprocess, os, math, shutil

OUT_DIR   = "/home/user/robin-/motion-graphics/videos"
FRAME_DIR = "/home/user/robin-/motion-graphics/_frames"
W, H      = 1080, 1920
FPS       = 30
DURATION  = 3.0          # seconds
FRAMES    = int(FPS * DURATION)
GREEN     = (0, 255, 0)

os.makedirs(OUT_DIR, exist_ok=True)

# ── Helpers ──────────────────────────────────────────────────────────────────

def ease_out(t):
    """Cubic ease-out."""
    return 1 - (1 - t) ** 3

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def progress(frame, start_s, duration_s):
    """0→1 progress for an animation starting at start_s over duration_s."""
    t = frame / FPS
    return clamp((t - start_s) / duration_s)

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def blend_color(c, alpha):
    """Blend color c over green at alpha."""
    r = int(c[0] * alpha + GREEN[0] * (1 - alpha))
    g = int(c[1] * alpha + GREEN[1] * (1 - alpha))
    b = int(c[2] * alpha + GREEN[2] * (1 - alpha))
    return (r, g, b)

def try_font(size):
    for name in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if os.path.exists(name):
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()

def draw_text_centered(draw, text, y_center, font, color, img_w):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (img_w - tw) // 2
    draw.text((x, y_center - (bbox[3] - bbox[1]) // 2), text, font=font, fill=color)
    return bbox[3] - bbox[1]   # height

def draw_line_expanding(draw, cx, cy, max_w, alpha, color, thick=4):
    """Horizontal line expanding from center outward."""
    w = int(max_w * alpha)
    if w < 2:
        return
    x0, x1 = cx - w // 2, cx + w // 2
    r, g, b = color
    a_int = int(alpha * 255)
    draw.rectangle([x0, cy - thick//2, x1, cy + thick//2],
                   fill=(r, g, b, a_int))

def draw_corner(draw, x, y, flip_x, flip_y, alpha, color, size=55, thick=3):
    if alpha <= 0:
        return
    r, g, b = color
    a = int(alpha * 255)
    dx = -size if flip_x else size
    dy = -size if flip_y else size
    dt_x = -thick if flip_x else thick
    dt_y = -thick if flip_y else thick
    # horizontal arm
    x0, x1 = sorted([x, x + dx])
    y0, y1 = sorted([y, y + dt_y])
    draw.rectangle([x0, y0, x1, y1], fill=(r, g, b, a))
    # vertical arm
    x0, x1 = sorted([x, x + dt_x])
    y0, y1 = sorted([y, y + dy])
    draw.rectangle([x0, y0, x1, y1], fill=(r, g, b, a))

# ── SCENE DEFINITIONS ────────────────────────────────────────────────────────

def render_intro(frame):
    """00 — SIX PILLARS OF FOOTBALL (gold)"""
    img  = Image.new("RGBA", (W, H), (0, 255, 0, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    gold   = hex_to_rgb("#FFD700")
    white  = (255, 255, 255)
    cx, cy = W // 2, H // 2

    # ── glow orb (always)
    orb_r = 300
    pulse = 0.85 + 0.15 * math.sin(frame / FPS * 2 * math.pi * 0.33)
    for r in range(int(orb_r * pulse), 0, -6):
        a = int(55 * (1 - r / (orb_r * pulse)))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 215, 0, a))

    # ── lines
    p_line = ease_out(progress(frame, 0.2, 0.5))
    draw_line_expanding(draw, cx, cy - 220, 700, p_line, gold)
    p_line2 = ease_out(progress(frame, 0.3, 0.5))
    draw_line_expanding(draw, cx, cy + 220, 700, p_line2, gold)

    # ── "SIX"
    p_six = ease_out(progress(frame, 0.05, 0.6))
    if p_six > 0:
        fy = int(80 * (1 - p_six))
        f  = try_font(int(200 * (0.85 + 0.15 * p_six)))
        c  = blend_color(gold, p_six)
        bbox = draw.textbbox((0, 0), "SIX", font=f)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        draw.text(((W - tw) // 2, cy - 180 + fy - th // 2), "SIX", font=f, fill=c + (255,))

    # ── "PILLARS"
    p_pillars = ease_out(progress(frame, 0.18, 0.6))
    if p_pillars > 0:
        fy = int(60 * (1 - p_pillars))
        f  = try_font(int(118 * (0.9 + 0.1 * p_pillars)))
        c  = blend_color(white, p_pillars)
        bbox = draw.textbbox((0, 0), "PILLARS", font=f)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        draw.text(((W - tw) // 2, cy - th // 2 + fy), "PILLARS", font=f, fill=c + (255,))

    # ── "OF FOOTBALL"
    p_sub = ease_out(progress(frame, 0.38, 0.5))
    if p_sub > 0:
        fy = int(30 * (1 - p_sub))
        f  = try_font(46)
        c  = blend_color(gold, p_sub)
        bbox = draw.textbbox((0, 0), "OF FOOTBALL", font=f)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        draw.text(((W - tw) // 2, cy + 130 + fy), "OF FOOTBALL", font=f, fill=c + (255,))

    # ── corners
    p_corn = ease_out(progress(frame, 0.7, 0.4))
    if p_corn > 0:
        pad = 120
        draw_corner(draw, pad,     140,            False, False, p_corn, gold)
        draw_corner(draw, W - pad, 140,            True,  False, p_corn, gold)
        draw_corner(draw, pad,     H - 140,        False, True,  p_corn, gold)
        draw_corner(draw, W - pad, H - 140,        True,  True,  p_corn, gold)

    return img.convert("RGB")


def render_pillar(frame, num, name, color_hex):
    """Generic pillar card."""
    img  = Image.new("RGBA", (W, H), (0, 255, 0, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    color = hex_to_rgb(color_hex)
    white = (255, 255, 255)
    cx, cy = W // 2, H // 2

    # ── glow orb
    orb_r = 360
    pulse = 0.85 + 0.15 * math.sin(frame / FPS * 2 * math.pi * 0.31)
    for r in range(int(orb_r * pulse), 0, -8):
        a = int(45 * (1 - r / (orb_r * pulse)))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (a,))

    # ── lines
    p_lt = ease_out(progress(frame, 0.15, 0.45))
    draw_line_expanding(draw, cx, cy - 210, 680, p_lt, color)
    p_lb = ease_out(progress(frame, 0.25, 0.45))
    draw_line_expanding(draw, cx, cy + 185, 680, p_lb, color)

    # ── badge "PILLAR XX"
    p_badge = ease_out(progress(frame, 0.0, 0.45))
    if p_badge > 0:
        fx = int(40 * (1 - p_badge))
        f  = try_font(44)
        badge_text = f"PILLAR {num}"
        c  = blend_color(color, p_badge)
        bbox = draw.textbbox((0, 0), badge_text, font=f)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        bx = (W - tw) // 2 - fx
        by = cy - 270
        draw.text((bx, by), badge_text, font=f, fill=c + (255,))
        # underline
        ul_w = int(tw * 0.6)
        draw.rectangle([bx + (tw - ul_w)//2, by + th + 8,
                         bx + (tw + ul_w)//2, by + th + 11], fill=c + (255,))

    # ── "THE"
    p_the = ease_out(progress(frame, 0.18, 0.4))
    if p_the > 0:
        fy = int(20 * (1 - p_the))
        f  = try_font(42)
        c  = (int(255 * p_the),) * 3
        bbox = draw.textbbox((0, 0), "THE", font=f)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        draw.text(((W - tw) // 2, cy - 160 + fy), "THE", font=f, fill=c + (255,))

    # ── pillar name
    p_name = ease_out(progress(frame, 0.28, 0.6))
    if p_name > 0:
        fy = int(70 * (1 - p_name))
        fs = int(128 * (0.88 + 0.12 * p_name))
        f  = try_font(fs)
        c  = blend_color(white, p_name)
        bbox = draw.textbbox((0, 0), name, font=f)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        draw.text(((W - tw) // 2, cy - th // 2 + fy - 30), name, font=f, fill=c + (255,))

    # ── "PILLAR" subtitle
    p_sub = ease_out(progress(frame, 0.42, 0.5))
    if p_sub > 0:
        fy = int(30 * (1 - p_sub))
        f  = try_font(52)
        c  = blend_color(color, p_sub)
        bbox = draw.textbbox((0, 0), "PILLAR", font=f)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        draw.text(((W - tw) // 2, cy + 110 + fy), "PILLAR", font=f, fill=c + (255,))

    # ── corners
    p_corn = ease_out(progress(frame, 0.65, 0.35))
    if p_corn > 0:
        pad = 110
        draw_corner(draw, pad,     140,     False, False, p_corn, color)
        draw_corner(draw, W - pad, 140,     True,  False, p_corn, color)
        draw_corner(draw, pad,     H - 140, False, True,  p_corn, color)
        draw_corner(draw, W - pad, H - 140, True,  True,  p_corn, color)

    return img.convert("RGB")


# ── SCENES LIST ───────────────────────────────────────────────────────────────

SCENES = [
    ("00_six_pillars_intro",  None,   None,       None),
    ("01_technical_pillar",   "01",   "TECHNICAL", "#00C2FF"),
    ("02_tactical_pillar",    "02",   "TACTICAL",  "#FF6B35"),
    ("03_health_pillar",      "03",   "HEALTH",    "#39D353"),
    ("04_physical_pillar",    "04",   "PHYSICAL",  "#FF2D55"),
    ("05_mental_pillar",      "05",   "MENTAL",    "#BF5AF2"),
    ("06_holistic_pillar",    "06",   "HOLISTIC",  "#FFD700"),
]

# ── RENDER ────────────────────────────────────────────────────────────────────

for slug, num, name, color in SCENES:
    print(f"Rendering {slug}...")
    fd = os.path.join(FRAME_DIR, slug)
    os.makedirs(fd, exist_ok=True)

    for f in range(FRAMES):
        if slug == "00_six_pillars_intro":
            img = render_intro(f)
        else:
            img = render_pillar(f, num, name, color)
        img.save(os.path.join(fd, f"frame_{f:04d}.png"))

    out = os.path.join(OUT_DIR, f"{slug}.mov")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(fd, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        out
    ]
    subprocess.run(cmd, capture_output=True)
    shutil.rmtree(fd)   # clean up frames
    print(f"  → {out}")

print("\nDone! All videos in:", OUT_DIR)
