#!/usr/bin/env python3
"""
Six Pillars — Progress Bar Overlay
─────────────────────────────────────────────────────────────────────
Format  : 1080 × 1920 px  |  9:16  |  30 fps
Output  : transparent PNG sequence  +  ProRes 4444 MOV (alpha channel)
Usage   : place clip above all footage in DaVinci / Premiere / CapCut
          NO blend mode change needed — alpha is baked in.

Configure SECONDS_PER_PILLAR to match your actual edit.
"""

from PIL import Image, ImageDraw, ImageFont
import subprocess, os, shutil, math

# ── CONFIG ────────────────────────────────────────────────────────────────────
SECONDS_PER_PILLAR = 8       # change to match your video timing
FPS                = 30
W, H               = 1080, 1920
NUM_SEGS           = 6
BAR_H              = 8       # px — thin, premium feel
BAR_BOTTOM_PAD     = 40      # px from very bottom edge
COUNTER_PAD_RIGHT  = 28      # px from right edge
COUNTER_PAD_ABOVE  = 18      # px above the bar
GLOW_DURATION      = 0.45    # seconds the glow plays after segment fills

# ── DERIVED ───────────────────────────────────────────────────────────────────
TOTAL_DURATION = SECONDS_PER_PILLAR * NUM_SEGS
FRAMES         = int(TOTAL_DURATION * FPS)
BAR_Y0         = H - BAR_BOTTOM_PAD - BAR_H
BAR_Y1         = H - BAR_BOTTOM_PAD
GAP            = 2   # px between segments
seg_w_base     = (W - GAP * (NUM_SEGS - 1)) // NUM_SEGS
# distribute any leftover pixels across the rightmost segments
seg_widths     = [seg_w_base] * NUM_SEGS
leftover       = W - GAP * (NUM_SEGS - 1) - seg_w_base * NUM_SEGS
for i in range(leftover):
    seg_widths[NUM_SEGS - 1 - i] += 1

seg_x = []
x = 0
for i, sw in enumerate(seg_widths):
    seg_x.append(x)
    x += sw + (GAP if i < NUM_SEGS - 1 else 0)

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

def text_right(draw, txt, right_x, cy, fnt, rgba):
    bb = draw.textbbox((0, 0), txt, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((right_x - tw, cy - th // 2), txt, font=fnt, fill=rgba)

# ── RENDER SINGLE FRAME ───────────────────────────────────────────────────────
def render_frame(frame):
    img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # fully transparent
    draw = ImageDraw.Draw(img, "RGBA")

    t                = frame / FPS
    active_seg       = min(int(t / SECONDS_PER_PILLAR), NUM_SEGS - 1)
    seg_local_t      = (t % SECONDS_PER_PILLAR) / SECONDS_PER_PILLAR  # 0→1
    pillar_num       = min(active_seg + 1, NUM_SEGS)

    WHITE_FULL = (255, 255, 255, 255)
    WHITE_HALF = (255, 255, 255, 128)   # 50 % — unfilled track

    # ── Draw each segment ────────────────────────────────────────────────────
    for i in range(NUM_SEGS):
        x0 = seg_x[i]
        x1 = x0 + seg_widths[i]
        sw = seg_widths[i]

        # ── Base track (always drawn, 50 % white)
        draw.rectangle([x0, BAR_Y0, x1, BAR_Y1], fill=WHITE_HALF)

        if i < active_seg:
            # Completed segment — solid white
            draw.rectangle([x0, BAR_Y0, x1, BAR_Y1], fill=WHITE_FULL)

            # Glow / pulse after completion
            completion_t = SECONDS_PER_PILLAR * (i + 1)
            since        = t - completion_t
            if 0 <= since <= GLOW_DURATION:
                glow_p = 1.0 - (since / GLOW_DURATION)          # 1→0
                glow_a = int(180 * glow_p)
                # Layered outward glow
                for pad in range(1, 6):
                    a = max(0, glow_a - pad * 30)
                    draw.rectangle(
                        [x0, BAR_Y0 - pad, x1, BAR_Y1 + pad],
                        fill=(255, 255, 255, a))

        elif i == active_seg:
            # Active segment — fill grows left→right
            fill_w = int(sw * seg_local_t)
            if fill_w > 0:
                draw.rectangle([x0, BAR_Y0, x0 + fill_w, BAR_Y1], fill=WHITE_FULL)

            # Leading-edge pulse (bright sliver at the fill head)
            if fill_w > 2:
                pulse_a = int(200 * (0.6 + 0.4 * math.sin(t * 6)))
                draw.rectangle(
                    [x0 + fill_w - 2, BAR_Y0 - 1, x0 + fill_w + 1, BAR_Y1 + 1],
                    fill=(255, 255, 255, max(0, pulse_a)))
        # else: future segment — already drawn as 50 % track above

    # ── Counter ──────────────────────────────────────────────────────────────
    counter_txt = f"PILLAR {pillar_num:02d} / 06"
    counter_y   = BAR_Y0 - COUNTER_PAD_ABOVE
    f_sm        = font(38)
    # Subtle text shadow (slight dark offset so it reads over light footage)
    text_right(draw, counter_txt,
               W - COUNTER_PAD_RIGHT + 1, counter_y + 1,
               f_sm, (0, 0, 0, 80))
    text_right(draw, counter_txt,
               W - COUNTER_PAD_RIGHT, counter_y,
               f_sm, WHITE_FULL)

    return img


# ── RENDER ALL FRAMES ─────────────────────────────────────────────────────────
print(f"Rendering {FRAMES} frames ({TOTAL_DURATION:.0f}s @ {FPS}fps)...")
for f in range(FRAMES):
    img = render_frame(f)
    img.save(os.path.join(FRAME_DIR, f"frame_{f:04d}.png"))
    if f % (FPS * 2) == 0:
        print(f"  {f}/{FRAMES}  ({f/FPS:.1f}s)", flush=True)

print("Frames done. Encoding video...")

# ── ENCODE: ProRes 4444 with alpha ────────────────────────────────────────────
out_prores = os.path.join(OUT_DIR, "progress_overlay_prores4444.mov")
result = subprocess.run([
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", os.path.join(FRAME_DIR, "frame_%04d.png"),
    "-c:v", "prores_ks",
    "-profile:v", "4444",
    "-pix_fmt", "yuva444p10le",
    "-vendor", "apl0",
    out_prores
], capture_output=True)

if result.returncode == 0:
    print(f"  ProRes 4444 → {out_prores}  ({os.path.getsize(out_prores)/1e6:.1f} MB)")
else:
    print("  ProRes 4444 encode failed, falling back to PNG sequence only.")
    print(result.stderr.decode()[-300:])

# ── Also zip the PNG sequence for CapCut / mobile editors ────────────────────
zip_path = os.path.join(OUT_DIR, "progress_overlay_png_sequence.zip")
subprocess.run(["zip", "-j", "-q", zip_path,
                *[os.path.join(FRAME_DIR, f"frame_{f:04d}.png") for f in range(FRAMES)]],
               capture_output=True)
print(f"  PNG sequence zip → {zip_path}  ({os.path.getsize(zip_path)/1e6:.1f} MB)")

shutil.rmtree(FRAME_DIR)
print("\nDone!")
print(f"  DaVinci / Premiere : use progress_overlay_prores4444.mov (alpha built-in)")
print(f"  CapCut / mobile    : import PNG sequence from the zip")
