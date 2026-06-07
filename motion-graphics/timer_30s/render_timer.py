#!/usr/bin/env python3
"""
30-Second Countdown Timer — Clean Loading Bar Overlay
──────────────────────────────────────────────────────
Format  : 1080 × 1920 | 9:16 | 30 fps | 30 seconds
Output  : ProRes 4444 MOV with alpha (transparent bg) + H.264 preview
DaVinci/CapCut: drop on overlay track — alpha is native, no keying needed

Design  : big countdown number, circular depleting ring, clean horizontal
          loading bar beneath — premium minimalist, electric-cyan accent.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess, os, shutil, math

W, H   = 1080, 1920
FPS    = 30
DUR    = 30.0
FRAMES = int(DUR * FPS)   # 900
CX, CY = W // 2, H // 2 - 80

ELECTRIC = (0, 210, 255)
WHITE    = (255, 255, 255)
DIM      = (255, 255, 255, 60)

OUT_DIR   = "/home/user/robin-/motion-graphics/timer_30s"
FRAME_DIR = os.path.join(OUT_DIR, "_frames")
os.makedirs(FRAME_DIR, exist_ok=True)

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
def font(sz):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

def tsize(d, txt, f):
    bb = d.textbbox((0, 0), txt, font=f)
    return bb[2]-bb[0], bb[3]-bb[1]

def draw_center(d, txt, cx, cy, f, fill):
    tw, th = tsize(d, txt, f)
    d.text((cx - tw//2, cy - th//2), txt, font=f, fill=fill)

# ── Easing ────────────────────────────────────────────────────────────────────
def clamp(v): return max(0.0, min(1.0, v))
def ease_out(t): t = clamp(t); return 1 - (1-t)**3

# ── Ring geometry ─────────────────────────────────────────────────────────────
RING_R   = 270
RING_W   = 14

def ring_bbox(r):
    return [CX-r, CY-r, CX+r, CY+r]

# ── Loading bar geometry ──────────────────────────────────────────────────────
BAR_W   = 640
BAR_H   = 10
BAR_X0  = CX - BAR_W // 2
BAR_X1  = CX + BAR_W // 2
BAR_Y   = CY + 430

FNT_NUM   = font(260)
FNT_LABEL = font(40)

# ── Render one frame ──────────────────────────────────────────────────────────
def render(frame):
    t = frame / FPS
    remaining = max(0.0, DUR - t)
    secs_left = math.ceil(remaining) if remaining > 0 else 0
    progress  = clamp(t / DUR)              # 0 → 1 (elapsed)
    remain_p  = 1.0 - progress              # 1 → 0 (remaining)

    img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    # ── Soft glow halo behind ring (pulses gently) ───────────────────────────
    pulse = 0.5 + 0.5 * math.sin(t * 2.4)
    glow_a = int(70 + 35 * pulse)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl, "RGBA")
    gd.ellipse(ring_bbox(RING_R + 6), outline=(*ELECTRIC, glow_a), width=RING_W)
    gl = gl.filter(ImageFilter.GaussianBlur(radius=26))
    img = Image.alpha_composite(img, gl)

    # ── Track ring (dim, full circle) ────────────────────────────────────────
    draw.ellipse(ring_bbox(RING_R), outline=(255, 255, 255, 45), width=RING_W)

    # ── Progress arc (depletes clockwise from top, electric glow) ────────────
    start_angle = -90
    end_angle   = -90 + 360 * remain_p
    if remain_p > 0.001:
        # Glow pass (wider, soft)
        gl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd2 = ImageDraw.Draw(gl2, "RGBA")
        gd2.arc(ring_bbox(RING_R), start_angle, end_angle,
                fill=(*ELECTRIC, 200), width=RING_W + 10)
        gl2 = gl2.filter(ImageFilter.GaussianBlur(radius=10))
        img = Image.alpha_composite(img, gl2)

        # Crisp arc
        d2 = ImageDraw.Draw(img, "RGBA")
        d2.arc(ring_bbox(RING_R), start_angle, end_angle,
               fill=(*WHITE, 255), width=RING_W)

        # Leading-edge dot (bright node at arc tip)
        ang_rad = math.radians(end_angle)
        tip_x = CX + RING_R * math.cos(ang_rad)
        tip_y = CY + RING_R * math.sin(ang_rad)
        dot_r = 16
        dl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dl, "RGBA")
        dd.ellipse([tip_x-dot_r-8, tip_y-dot_r-8, tip_x+dot_r+8, tip_y+dot_r+8],
                   fill=(*ELECTRIC, 160))
        dl = dl.filter(ImageFilter.GaussianBlur(radius=10))
        img = Image.alpha_composite(img, dl)
        d3 = ImageDraw.Draw(img, "RGBA")
        d3.ellipse([tip_x-dot_r, tip_y-dot_r, tip_x+dot_r, tip_y+dot_r],
                   fill=(*WHITE, 255))

    # ── Countdown number (center, glow + crisp) ──────────────────────────────
    num_txt = str(secs_left)
    d4 = ImageDraw.Draw(img, "RGBA")

    # Pop scale on each whole-second tick
    tick_frac = t - math.floor(t)
    pop = 1.0 + 0.10 * (1 - ease_out(tick_frac * 3.0))
    fs_now = max(int(260 * pop), 10)
    f_num  = font(fs_now)

    # Glow layer
    gl3 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd3 = ImageDraw.Draw(gl3, "RGBA")
    tw, th = tsize(gd3, num_txt, f_num)
    gd3.text((CX-tw//2, CY-th//2), num_txt, font=f_num, fill=(*ELECTRIC, 160))
    gl3 = gl3.filter(ImageFilter.GaussianBlur(radius=22))
    img = Image.alpha_composite(img, gl3)

    d5 = ImageDraw.Draw(img, "RGBA")
    draw_center(d5, num_txt, CX, CY, f_num, (*WHITE, 255))

    # "SECONDS" label under number
    label_a = 200
    draw_center(d5, "SECONDS", CX, CY + 165, FNT_LABEL, (*ELECTRIC, label_a))

    # ── Loading bar (depletes left → right empties as time runs out) ─────────
    d6 = ImageDraw.Draw(img, "RGBA")
    # Track
    d6.rounded_rectangle([BAR_X0, BAR_Y, BAR_X1, BAR_Y + BAR_H],
                         radius=BAR_H//2, fill=(255, 255, 255, 40))
    # Fill — shrinks from full to empty as time elapses
    fill_w = int(BAR_W * remain_p)
    if fill_w > 2:
        # Glow pass
        gl4 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd4 = ImageDraw.Draw(gl4, "RGBA")
        gd4.rounded_rectangle([BAR_X0, BAR_Y, BAR_X0 + fill_w, BAR_Y + BAR_H],
                              radius=BAR_H//2, fill=(*ELECTRIC, 180))
        gl4 = gl4.filter(ImageFilter.GaussianBlur(radius=8))
        img = Image.alpha_composite(img, gl4)

        d7 = ImageDraw.Draw(img, "RGBA")
        d7.rounded_rectangle([BAR_X0, BAR_Y, BAR_X0 + fill_w, BAR_Y + BAR_H],
                             radius=BAR_H//2, fill=(*WHITE, 255))

        # Shimmer at leading edge
        shimmer_a = int(200 * (0.5 + 0.5*math.sin(t * 9)))
        d7.rectangle([BAR_X0+fill_w-2, BAR_Y-2, BAR_X0+fill_w+2, BAR_Y+BAR_H+2],
                     fill=(255, 255, 255, max(0, shimmer_a)))

    # "TIME REMAINING" micro-label above bar
    d8 = ImageDraw.Draw(img, "RGBA")
    draw_center(d8, "TIME REMAINING", CX, BAR_Y - 34, font(28), (255, 255, 255, 110))

    # ── Flash pulse on final 3 seconds (urgency cue) ─────────────────────────
    if secs_left <= 3 and remaining > 0:
        flash_p = 1.0 - (t - math.floor(t))
        flash_a = int(50 * flash_p * (4 - secs_left) / 3)
        fl = Image.new("RGBA", (W, H), (255, 80, 80, max(0, flash_a)))
        img = Image.alpha_composite(img, fl)

    # ── End state — "TIME'S UP" reveal ────────────────────────────────────────
    if remaining <= 0:
        end_p = clamp((t - DUR) / 0.6)
        a = int(255 * ease_out(end_p))
        d9 = ImageDraw.Draw(img, "RGBA")
        draw_center(d9, "TIME'S UP", CX, CY, font(120), (*ELECTRIC, a))

    return img

# ── Render all frames ─────────────────────────────────────────────────────────
print(f"Rendering {FRAMES} frames ({DUR:.0f}s @ {FPS}fps)...", flush=True)
for f in range(FRAMES):
    render(f).save(os.path.join(FRAME_DIR, f"frame_{f:04d}.png"))
    if f % (FPS * 5) == 0:
        print(f"  {f}/{FRAMES}  ({f/FPS:.0f}s)", flush=True)

# ── Encode: ProRes 4444 with alpha (for overlay) ─────────────────────────────
print("Encoding ProRes 4444 with alpha...", flush=True)
out_mov = os.path.join(OUT_DIR, "timer_30s_prores4444.mov")
r = subprocess.run([
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", os.path.join(FRAME_DIR, "frame_%04d.png"),
    "-c:v", "prores_ks", "-profile:v", "4444",
    "-pix_fmt", "yuva444p10le", "-vendor", "apl0",
    out_mov
], capture_output=True)
if r.returncode == 0:
    print(f"  MOV → {out_mov}  ({os.path.getsize(out_mov)/1e6:.1f} MB)")
else:
    print("  MOV encode error:", r.stderr.decode()[-400:])

# ── Encode: H.264 preview (over black, for quick viewing) ────────────────────
print("Encoding H.264 preview...", flush=True)
out_mp4 = os.path.join(OUT_DIR, "timer_30s_PREVIEW.mp4")
r2 = subprocess.run([
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", os.path.join(FRAME_DIR, "frame_%04d.png"),
    "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}",
    "-filter_complex", "[1:v][0:v]overlay=shortest=1,format=yuv420p",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-t", str(DUR),
    out_mp4
], capture_output=True)
if r2.returncode == 0:
    print(f"  MP4 → {out_mp4}  ({os.path.getsize(out_mp4)/1e6:.1f} MB)")
else:
    print("  MP4 encode error:", r2.stderr.decode()[-400:])

shutil.rmtree(FRAME_DIR)
print("\nDone.")
