#!/usr/bin/env python3
"""
Six Pillars — Progress Bar Overlay (custom timed, 58s)
────────────────────────────────────────────────────────
Format  : 1080 × 1920  |  9:16  |  30 fps  |  58 seconds
Output  : ProRes 4444 MOV with alpha channel (transparent bg)
DaVinci : drop on top layer — alpha is native, no keying needed
CapCut  : import MOV, place on overlay track
"""

from PIL import Image, ImageDraw, ImageFont
import subprocess, os, shutil, math

# ── EXACT SEGMENT TIMINGS (seconds) ──────────────────────────────────────────
SEGMENT_TIMESTAMPS = [
    (0.0,  10.0,  "PILLAR 01 / 06"),   # Hook / Intro
    (10.0, 20.0,  "PILLAR 02 / 06"),   # Technical
    (20.0, 30.0,  "PILLAR 03 / 06"),   # Tactical
    (30.0, 40.0,  "PILLAR 04 / 06"),   # Health
    (40.0, 50.0,  "PILLAR 05 / 06"),   # Physical
    (50.0, 58.0,  "PILLAR 06 / 06"),   # Mental / Holistic / Outro
]

FPS            = 30
TOTAL_DURATION = 58.0
TOTAL_FRAMES   = int(TOTAL_DURATION * FPS)   # 1740
W, H           = 1080, 1920

BAR_H          = 10
BAR_BOTTOM_PAD = 120    # px up from very bottom (safe from TikTok/IG UI)
BAR_Y0         = H - BAR_BOTTOM_PAD - BAR_H
BAR_Y1         = H - BAR_BOTTOM_PAD

NUM_SEGS       = 6
GAP            = 3      # px between segments
GLOW_DURATION  = 0.4   # seconds

# Counter position
COUNTER_RIGHT  = 32     # px from right edge
COUNTER_ABOVE  = 16     # px above bar

# ── SEGMENT X POSITIONS ───────────────────────────────────────────────────────
seg_w_base = (W - GAP * (NUM_SEGS - 1)) // NUM_SEGS
seg_widths = [seg_w_base] * NUM_SEGS
leftover   = W - GAP * (NUM_SEGS - 1) - seg_w_base * NUM_SEGS
for i in range(leftover):
    seg_widths[NUM_SEGS - 1 - i] += 1

seg_x = []
x = 0
for i, sw in enumerate(seg_widths):
    seg_x.append(x)
    x += sw + (GAP if i < NUM_SEGS - 1 else 0)

# ── OUTPUT DIRS ───────────────────────────────────────────────────────────────
OUT_DIR   = "/home/user/robin-/motion-graphics/progress_overlay"
FRAME_DIR = os.path.join(OUT_DIR, "_frames")
os.makedirs(FRAME_DIR, exist_ok=True)

# ── FONT ──────────────────────────────────────────────────────────────────────
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def draw_text_right(draw, txt, right_x, cy, fnt, rgba):
    bb = draw.textbbox((0, 0), txt, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((right_x - tw, cy - th // 2), txt, font=fnt, fill=rgba)

FNT = font(38)

# ── RENDER ONE FRAME ──────────────────────────────────────────────────────────
def render_frame(frame):
    t   = frame / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # 100% transparent bg
    draw = ImageDraw.Draw(img, "RGBA")

    WHITE_FULL = (255, 255, 255, 255)
    WHITE_DIM  = (255, 255, 255, 77)   # 30 % opacity unfilled track

    # Which segment are we in?
    active_seg   = 0
    seg_local_p  = 0.0
    counter_text = SEGMENT_TIMESTAMPS[-1][2]

    for i, (start, end, label) in enumerate(SEGMENT_TIMESTAMPS):
        if t <= end:
            active_seg   = i
            seg_local_p  = (t - start) / (end - start)
            counter_text = label
            break

    for i, (x0, sw) in enumerate(zip(seg_x, seg_widths)):
        x1 = x0 + sw

        # Unfilled track (always drawn first)
        draw.rectangle([x0, BAR_Y0, x1, BAR_Y1], fill=WHITE_DIM)

        seg_end_t = SEGMENT_TIMESTAMPS[i][1]

        if i < active_seg:
            # Completed — solid white
            draw.rectangle([x0, BAR_Y0, x1, BAR_Y1], fill=WHITE_FULL)

            # Glow pulse after completion
            since = t - seg_end_t
            if 0.0 <= since <= GLOW_DURATION:
                p = 1.0 - since / GLOW_DURATION
                for pad in range(1, 7):
                    a = int(160 * p * ((7 - pad) / 6))
                    draw.rectangle(
                        [x0, BAR_Y0 - pad, x1, BAR_Y1 + pad],
                        fill=(255, 255, 255, a))

        elif i == active_seg:
            # Filling — grow left → right
            fill_w = int(sw * seg_local_p)
            if fill_w > 0:
                draw.rectangle([x0, BAR_Y0, x0 + fill_w, BAR_Y1], fill=WHITE_FULL)

            # Leading-edge shimmer
            if 4 < fill_w < sw:
                shimmer_a = int(220 * (0.5 + 0.5 * math.sin(t * 8)))
                draw.rectangle(
                    [x0 + fill_w - 2, BAR_Y0 - 1, x0 + fill_w + 2, BAR_Y1 + 1],
                    fill=(255, 255, 255, max(0, shimmer_a)))

    # Counter text — dark shadow then white
    cy = BAR_Y0 - COUNTER_ABOVE
    draw_text_right(draw, counter_text, W - COUNTER_RIGHT + 1, cy + 1, FNT, (0, 0, 0, 90))
    draw_text_right(draw, counter_text, W - COUNTER_RIGHT,     cy,     FNT, WHITE_FULL)

    # Composite over black to resolve alpha correctly
    black = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return Image.alpha_composite(black, img)   # stays RGBA / transparent

# ── RENDER ALL FRAMES ─────────────────────────────────────────────────────────
print(f"Rendering {TOTAL_FRAMES} frames ({TOTAL_DURATION}s @ {FPS}fps)...", flush=True)
for f in range(TOTAL_FRAMES):
    render_frame(f).save(os.path.join(FRAME_DIR, f"frame_{f:04d}.png"))
    if f % (FPS * 5) == 0:
        print(f"  {f}/{TOTAL_FRAMES}  ({f/FPS:.0f}s)", flush=True)

print("Encoding ProRes 4444 with alpha...", flush=True)
out = os.path.join(OUT_DIR, "progress_bar_58s_prores4444.mov")
r = subprocess.run([
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", os.path.join(FRAME_DIR, "frame_%04d.png"),
    "-c:v", "prores_ks", "-profile:v", "4444",
    "-pix_fmt", "yuva444p10le",
    "-vendor", "apl0",
    out
], capture_output=True)

shutil.rmtree(FRAME_DIR)

if r.returncode == 0:
    print(f"Done → {out}  ({os.path.getsize(out)/1e6:.1f} MB)")
else:
    print("Encode error:", r.stderr.decode()[-400:])
