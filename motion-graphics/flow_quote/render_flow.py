#!/usr/bin/env python3
"""
FLOW — Kinetic Quote Motion Graphic
────────────────────────────────────
1080×1920 · 30fps · 7s · Black bg → Screen blend in DaVinci/CapCut
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess, os, shutil, math

W, H   = 1080, 1920
FPS    = 30
DUR    = 7.0
FRAMES = int(DUR * FPS)   # 210

OUT_DIR   = "/home/user/robin-/motion-graphics/flow_quote"
FRAME_DIR = os.path.join(OUT_DIR, "_frames")
os.makedirs(FRAME_DIR, exist_ok=True)

ELECTRIC = (0, 210, 255)    # cyan-electric accent
WHITE    = (255, 255, 255)
SOFT     = (180, 180, 180)

# ── FONTS ─────────────────────────────────────────────────────────────────────
BOLD_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def fnt(sz):
    return ImageFont.truetype(BOLD_FONT, sz)

def tsize(draw, txt, f):
    bb = draw.textbbox((0, 0), txt, font=f)
    return bb[2]-bb[0], bb[3]-bb[1]

# ── EASING ────────────────────────────────────────────────────────────────────
def clamp(v): return max(0.0, min(1.0, v))
def prog(frame, start, dur): return clamp((frame/FPS - start) / dur)
def ease_out(t): t=clamp(t); return 1-(1-t)**3
def ease_out_back(t):
    t=clamp(t); c1,c3=1.70158,2.70158
    return 1 + c3*(t-1)**3 + c1*(t-1)**2

# ── GLOW TEXT ─────────────────────────────────────────────────────────────────
def draw_glow(img, txt, cx, cy, f, color, glow_color, glow_r=28, glow_a=180):
    """Draw text with a soft gaussian glow halo underneath."""
    d = ImageDraw.Draw(img, "RGBA")
    tw, th = tsize(d, txt, f)
    x, y = cx - tw//2, cy - th//2

    # Glow layer — blur a colored version of the text
    gl = Image.new("RGBA", (W, H), (0,0,0,0))
    gd = ImageDraw.Draw(gl, "RGBA")
    gd.text((x, y), txt, font=f, fill=(*glow_color, glow_a))
    gl = gl.filter(ImageFilter.GaussianBlur(radius=glow_r))
    img = Image.alpha_composite(img, gl)

    # Second tighter glow for intensity
    gl2 = Image.new("RGBA", (W, H), (0,0,0,0))
    gd2 = ImageDraw.Draw(gl2, "RGBA")
    gd2.text((x, y), txt, font=f, fill=(*glow_color, min(255, glow_a+60)))
    gl2 = gl2.filter(ImageFilter.GaussianBlur(radius=glow_r//3))
    img = Image.alpha_composite(img, gl2)

    # Sharp white text on top
    d2 = ImageDraw.Draw(img, "RGBA")
    d2.text((x, y), txt, font=f, fill=(*color, 255))
    return img

def draw_text_alpha(img, txt, cx, cy, f, color, alpha):
    """Draw text at given alpha."""
    if alpha <= 0: return img
    d = ImageDraw.Draw(img, "RGBA")
    tw, th = tsize(d, txt, f)
    d.text((cx-tw//2, cy-th//2), txt, font=f, fill=(*color, int(alpha)))
    return img

# ── LINE DEFINITIONS ──────────────────────────────────────────────────────────
# (start_s, text, font_size, color, glow, glow_color, y_pos)
CX = W // 2

LINES = [
    # start   text                      fs    color   glow  glow_col   y
    (0.00, "FLOW",                      210,  WHITE,  True,  ELECTRIC,  480),
    (0.55, "is a mental state",          48,  SOFT,   False, ELECTRIC,  680),
    (1.05, "where your mind",            60,  WHITE,  False, WHITE,     750),
    (1.55, "STOPS OVERTHINKING",         76,  WHITE,  True,  ELECTRIC,  840),
    (2.10, "everything,",                72,  WHITE,  False, WHITE,     930),
    (2.60, "and your body",              55,  SOFT,   False, WHITE,    1010),
    (3.10, "JUST TAKES OVER",            80,  WHITE,  True,  ELECTRIC, 1095),
    (3.60, "automatically.",             60,  WHITE,  False, WHITE,    1185),
]

HOLD_START = 4.10    # full reveal held from here
FADE_START = 6.30    # fade to black starts
FLASH_DUR  = 0.10    # white impact flash duration at t=0

# ── RENDER FRAME ──────────────────────────────────────────────────────────────
def render(frame):
    t   = frame / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))   # black bg

    # ── Impact flash on FLOW entry (first few frames)
    if t < FLASH_DUR:
        flash_a = int(220 * (1 - t/FLASH_DUR)**2)
        fl = Image.new("RGBA", (W, H), (255, 255, 255, flash_a))
        img = Image.alpha_composite(img, fl)

    # ── Thin horizontal accent line (appears with FLOW)
    line_p = ease_out(prog(frame, 0.12, 0.30))
    if line_p > 0:
        lw = int(480 * line_p)
        la = int(200 * min(line_p * 3, 1.0))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([CX - lw//2, 572, CX + lw//2, 575],
                    fill=(*ELECTRIC, la))

    # ── Each text line
    for i, (start, txt, fs, color, do_glow, glow_col, cy) in enumerate(LINES):
        p = prog(frame, start, 0.35)
        if p <= 0:
            continue

        p2    = ease_out_back(p)
        alpha = clamp(p * 3.5) * 255

        # Scale: 1.15 → 1.0 (slam effect)
        scale  = 1.0 + 0.15 * (1 - ease_out(p))
        fs_now = max(int(fs * scale), 1)

        # Global fade out
        if t >= FADE_START:
            fade_p  = (t - FADE_START) / (DUR - FADE_START)
            alpha  *= max(0.0, 1 - fade_p)

        # Slide up offset
        slide_y = int(35 * (1 - p2))

        if do_glow and p > 0.3:
            glow_a = int(min(alpha, 255) * 0.75)
            img = draw_glow(img, txt, CX, cy + slide_y,
                            fnt(fs_now), color, glow_col,
                            glow_r=30 if i==0 else 16, glow_a=glow_a)
        else:
            img = draw_text_alpha(img, txt, CX, cy + slide_y,
                                  fnt(fs_now), color, alpha)

    # ── Breathing glow pulse on FLOW during hold
    if HOLD_START <= t < FADE_START:
        pulse_p = (t - HOLD_START) / (FADE_START - HOLD_START)
        pulse_a = int(60 + 40 * math.sin(pulse_p * math.pi * 4))
        gl = Image.new("RGBA", (W, H), (0,0,0,0))
        gd = ImageDraw.Draw(gl, "RGBA")
        _, txt, fs, *_ = LINES[0]
        f0 = fnt(fs)
        tw, th = tsize(gd, txt, f0)
        gd.text((CX-tw//2, 480-th//2), txt, font=f0,
                fill=(*ELECTRIC, pulse_a))
        gl = gl.filter(ImageFilter.GaussianBlur(radius=40))
        img = Image.alpha_composite(img, gl)

    return img.convert("RGB")

# ── RENDER ALL FRAMES ─────────────────────────────────────────────────────────
print(f"Rendering {FRAMES} frames...", flush=True)
for f in range(FRAMES):
    render(f).save(os.path.join(FRAME_DIR, f"frame_{f:04d}.png"))
    if f % 30 == 0:
        print(f"  {f}/{FRAMES}  t={f/FPS:.1f}s", flush=True)

# ── ENCODE: H.264 MP4 (plays anywhere) ───────────────────────────────────────
out_mp4 = os.path.join(OUT_DIR, "flow_quote.mp4")
subprocess.run([
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", os.path.join(FRAME_DIR, "frame_%04d.png"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "slow", "-crf", "14",
    out_mp4
], capture_output=True)
print(f"  MP4 → {out_mp4}  ({os.path.getsize(out_mp4)/1e6:.1f} MB)")

# ── ENCODE: ProRes 4444 (black bg, use Screen blend in editor) ────────────────
out_mov = os.path.join(OUT_DIR, "flow_quote_screen_blend.mov")
subprocess.run([
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", os.path.join(FRAME_DIR, "frame_%04d.png"),
    "-c:v", "prores_ks", "-profile:v", "4444",
    "-pix_fmt", "yuv420p10le", "-vendor", "apl0",
    out_mov
], capture_output=True)
print(f"  MOV → {out_mov}  ({os.path.getsize(out_mov)/1e6:.1f} MB)")

shutil.rmtree(FRAME_DIR)
print("\nDone.")
