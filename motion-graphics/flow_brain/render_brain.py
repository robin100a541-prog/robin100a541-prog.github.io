#!/usr/bin/env python3
"""
FLOW STATE — Brain Neural Visualization
1920×1080 · 30fps · 8s · YouTube 16:9
No text. Pure visual. Brain silhouette + neural flows + particles.

Narrative arc:
  0-2s  → Brain appears, neural chaos (overthinking — fast erratic flashes)
  2-4s  → Chaos slows, pathways start to glow, particles find streams
  4-8s  → Full FLOW — smooth synchronized streams, brain breathing with light
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import subprocess, os, shutil, math

W, H   = 1920, 1080
FPS    = 30
DUR    = 8.0
FRAMES = int(DUR * FPS)   # 240
CX, CY = W // 2, H // 2
BRX    = 340    # brain x-radius
BRY    = 272    # brain y-radius

OUT_DIR   = "/home/user/robin-/motion-graphics/flow_brain"
FRAME_DIR = os.path.join(OUT_DIR, "_frames")
os.makedirs(FRAME_DIR, exist_ok=True)

rng = np.random.default_rng(42)

# ── Colour helpers ────────────────────────────────────────────────────────────
def lerp_col(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i]*(1-t) + b[i]*t) for i in range(3))

def clamp(v, lo=0.0, hi=1.0): return max(lo, min(hi, v))
def ease_in_out(t): t=clamp(t); return t*t*(3-2*t)
def ease_out(t): t=clamp(t); return 1-(1-t)**3

# ── Brain silhouette polygon ──────────────────────────────────────────────────
def brain_polygon(cx, cy, n=400):
    pts = []
    for i in range(n):
        theta = 2*math.pi*i/n
        # Organic base with gyri bumps
        r  = 1.0
        r += 0.070 * math.sin(5 * theta + 0.2)
        r += 0.045 * math.sin(9 * theta + 1.1)
        r += 0.025 * math.sin(14* theta + 2.3)
        r += 0.015 * math.sin(20* theta + 0.7)
        # Flatten bottom (brainstem area)
        flat = 1.0 - 0.12 * max(0, -math.sin(theta))**1.5
        # Slight left-right asymmetry (realistic)
        asym = 1.0 + 0.02 * math.cos(theta)
        pts.append((cx + BRX * r * flat * asym * math.cos(theta),
                    cy + BRY * r * flat * math.sin(theta)))
    return pts

BRAIN_PTS = brain_polygon(CX, CY)

# ── Neural pathway waypoints (screen coords) ──────────────────────────────────
def npt(dx, dy): return (CX + dx, CY + dy)

RAW_PATHS = [
    # Left hemisphere — major gyri arcs
    [npt(-20,-10), npt(-100,-120), npt(-200,-160), npt(-295,-110), npt(-330,-20)],
    [npt(-20,-10), npt(-130, -60), npt(-255, -55), npt(-320, 30)],
    [npt(-20,-10), npt(-115,  50), npt(-240,  80), npt(-310, 60)],
    [npt(-20,-10), npt( -90,-140), npt(-160,-200), npt(-230,-190)],
    [npt(-20,-10), npt(-180, -90), npt(-280,-150)],
    [npt(-20,-10), npt(-160,  30), npt(-280,  10)],
    # Right hemisphere
    [npt( 20,-10), npt( 100,-120), npt( 200,-160), npt( 295,-110), npt( 330,-20)],
    [npt( 20,-10), npt( 130, -60), npt( 255, -55), npt( 320, 30)],
    [npt( 20,-10), npt( 115,  50), npt( 240,  80), npt( 310, 60)],
    [npt( 20,-10), npt(  90,-140), npt( 160,-200), npt( 230,-190)],
    [npt( 20,-10), npt( 180, -90), npt( 280,-150)],
    [npt( 20,-10), npt( 160,  30), npt( 280,  10)],
    # Corpus callosum (cross-hemisphere)
    [npt(-240,-80), npt(-120,-30), npt(0,-15), npt(120,-30), npt(240,-80)],
    [npt(-220, 60), npt(-110, 30), npt(0, 20), npt(110, 30), npt(220, 60)],
]

def interpolate_path(waypts, n=120):
    """Linear interpolation along waypoints → list of (x,y) at n steps."""
    if len(waypts) < 2: return waypts
    segs    = len(waypts) - 1
    pts_per = max(2, n // segs)
    out     = []
    for i in range(segs):
        p0, p1 = waypts[i], waypts[i+1]
        for k in range(pts_per):
            t = k / pts_per
            out.append((p0[0]*(1-t)+p1[0]*t, p0[1]*(1-t)+p1[1]*t))
    out.append(waypts[-1])
    return out

PATHS_DENSE = [interpolate_path(p, 140) for p in RAW_PATHS]
N_PATHS     = len(PATHS_DENSE)

# All path points for spatial reference
ALL_PATH_PTS = np.array([(x,y) for p in PATHS_DENSE for x,y in p])

# ── Node positions (path endpoints + intersections) ──────────────────────────
NODES = list({tuple(p[0]) for p in RAW_PATHS} |
             {tuple(p[-1]) for p in RAW_PATHS})

# ── Particle system ───────────────────────────────────────────────────────────
N_PART    = 600
# Start: random positions scattered inside brain bbox
px = rng.uniform(CX - BRX*0.85, CX + BRX*0.85, N_PART)
py = rng.uniform(CY - BRY*0.85, CY + BRY*0.85, N_PART)
# Random velocities for chaos phase
vx = rng.uniform(-6, 6, N_PART)
vy = rng.uniform(-6, 6, N_PART)

# Target positions: distribute along paths for flow phase
path_targets = []
for _ in range(N_PART):
    pi   = rng.integers(0, N_PATHS)
    idx  = rng.integers(0, len(PATHS_DENSE[pi]))
    pt   = PATHS_DENSE[pi][idx]
    # Assign a slightly randomised phase offset for visual variety
    path_targets.append(pt)
path_targets = np.array(path_targets)

# Flow path offsets (each particle advances along a path)
part_path_idx  = rng.integers(0, N_PATHS, N_PART)
part_path_pos  = rng.uniform(0, 1, N_PART)   # 0→1 position along path
part_path_spd  = rng.uniform(0.003, 0.009, N_PART)   # speed

# ── Precompute static brain base ───────────────────────────────────────────────
print("Precomputing brain base layer...", flush=True)

def make_brain_base():
    base = Image.new("RGBA", (W, H), (3, 5, 14, 255))

    # Subtle radial background vignette
    bg_layer = Image.new("RGBA", (W, H), (0,0,0,0))
    bg_d = ImageDraw.Draw(bg_layer)
    for r in range(550, 0, -10):
        a = int(25 * (1 - r/550)**1.5)
        bg_d.ellipse([CX-r*1.8, CY-r, CX+r*1.8, CY+r], fill=(20, 35, 90, a))
    base = Image.alpha_composite(base, bg_layer)

    pts_i = [(int(x), int(y)) for x,y in BRAIN_PTS]

    # Multi-layer glow (wide → tight)
    for glow_r, col, a_mult in [
        (55, (30, 80, 255),  0.12),
        (35, (50, 120, 255), 0.20),
        (18, (80, 160, 255), 0.35),
        ( 8, (120,190,255),  0.60),
    ]:
        gl = Image.new("RGBA", (W, H), (0,0,0,0))
        gd = ImageDraw.Draw(gl)
        gd.polygon(pts_i, outline=(*col, int(255*a_mult)), fill=None)
        gl = gl.filter(ImageFilter.GaussianBlur(radius=glow_r))
        base = Image.alpha_composite(base, gl)

    # Crisp brain outline
    out_l = Image.new("RGBA", (W, H), (0,0,0,0))
    od    = ImageDraw.Draw(out_l)
    od.polygon(pts_i, outline=(160, 210, 255, 220), fill=None)
    base  = Image.alpha_composite(base, out_l)

    # Very subtle fill (slight interior glow)
    fill_l = Image.new("RGBA", (W, H), (0,0,0,0))
    fd     = ImageDraw.Draw(fill_l)
    fd.polygon(pts_i, fill=(15, 30, 80, 22))
    base   = Image.alpha_composite(base, fill_l)

    # Hemisphere dividing line (corpus callosum guide)
    div_l = Image.new("RGBA", (W, H), (0,0,0,0))
    dd    = ImageDraw.Draw(div_l)
    for dy in range(-BRY+40, BRY-40, 4):
        dd.ellipse([CX-3, CY+dy-3, CX+3, CY+dy+3],
                   fill=(100, 160, 255, 35))
    div_l = div_l.filter(ImageFilter.GaussianBlur(radius=4))
    base  = Image.alpha_composite(base, div_l)

    # Dim neural path lines (static skeleton)
    path_l = Image.new("RGBA", (W, H), (0,0,0,0))
    pd     = ImageDraw.Draw(path_l)
    for path in PATHS_DENSE:
        pts2 = [(int(x), int(y)) for x,y in path]
        if len(pts2) > 1:
            pd.line(pts2, fill=(30, 70, 160, 60), width=1)
    path_l = path_l.filter(ImageFilter.GaussianBlur(radius=1))
    base   = Image.alpha_composite(base, path_l)

    return base

BRAIN_BASE = make_brain_base()
print("  Brain base done.", flush=True)

# ── Per-frame render ──────────────────────────────────────────────────────────
def render(frame, px, py, vx, vy, part_path_pos):
    t    = frame / FPS
    # Phase blend: 0=chaos, 1=flow
    flow = ease_in_out(clamp((t - 1.5) / 2.5))   # ramps 1.5s→4s

    img  = BRAIN_BASE.copy()

    # ── Neural pathway pulses ─────────────────────────────────────────────────
    pulse_layer = Image.new("RGBA", (W, H), (0,0,0,0))
    pd = ImageDraw.Draw(pulse_layer)

    for pi, path in enumerate(PATHS_DENSE):
        # Each path has a travelling pulse
        phase_off = pi * 0.23 + 0.7
        # In chaos: pulse moves fast + jitters; in flow: slow + smooth
        speed_chaos = 0.8 + 0.4 * math.sin(pi * 1.7)
        speed_flow  = 0.25 + 0.15 * math.sin(pi * 2.1)
        speed       = speed_chaos*(1-flow) + speed_flow*flow
        pulse_t     = (t * speed + phase_off) % 1.0

        # In chaos phase, also fire random sparks
        n_pulses = 3 if flow < 0.5 else 1
        for k in range(n_pulses):
            pt_off = (pulse_t + k/n_pulses) % 1.0
            idx    = int(pt_off * (len(path)-1))
            px_p, py_p = path[idx]

            # Color: white-ish in chaos → cyan in flow
            col = lerp_col((220, 230, 255), (0, 210, 255), flow)
            # Brightness flickers in chaos phase
            flicker = 1.0 if flow > 0.6 else (0.5 + 0.5*math.sin(t*40+pi*3.1))
            a       = int(200 * flicker * (0.4 + 0.6*flow))

            r_pulse = int(lerp_col((2,2,2),(4,4,4),flow)[0])  # tight glow
            pd.ellipse([px_p-r_pulse, py_p-r_pulse, px_p+r_pulse, py_p+r_pulse],
                       fill=(*col, a))

    pulse_layer = pulse_layer.filter(ImageFilter.GaussianBlur(radius=4))
    img = Image.alpha_composite(img, pulse_layer)

    # ── Node pulses ────────────────────────────────────────────────────────────
    node_layer = Image.new("RGBA", (W, H), (0,0,0,0))
    nd = ImageDraw.Draw(node_layer)
    for ni, (nx, ny) in enumerate(NODES):
        pulse = 0.5 + 0.5*math.sin(t * (2.5 + ni*0.4))
        chaos_bright = 0.4 + 0.6*(1-flow) * abs(math.sin(t*8+ni*2))
        a_node = int(120 * pulse * (0.3 + 0.7*flow) + 80 * chaos_bright)
        col_n  = lerp_col((255, 255, 255), (0, 200, 255), flow)
        nd.ellipse([nx-4, ny-4, nx+4, ny+4], fill=(*col_n, min(255, a_node)))
    node_layer = node_layer.filter(ImageFilter.GaussianBlur(radius=3))
    img = Image.alpha_composite(img, node_layer)

    # ── Particles ──────────────────────────────────────────────────────────────
    p_layer = Image.new("RGBA", (W, H), (0,0,0,0))
    pdd = ImageDraw.Draw(p_layer)

    for i in range(N_PART):
        # Chaos: use random-walk px/py; Flow: follow path
        fx = float(px[i])*(1-flow) + float(path_targets[i,0])*flow
        fy = float(py[i])*(1-flow) + float(path_targets[i,1])*flow

        if not (50 < fx < W-50 and 50 < fy < H-50):
            continue

        col_p = lerp_col((255, 250, 255), (0, 200, 255), flow)
        # Smaller in flow (more precise), jittery in chaos
        sz  = 2 if flow > 0.5 else int(1 + 2*abs(math.sin(t*15+i*0.1)))
        a_p = int(180 * (0.5 + 0.5*flow))
        pdd.ellipse([fx-sz, fy-sz, fx+sz, fy+sz], fill=(*col_p, a_p))

    p_layer = p_layer.filter(ImageFilter.GaussianBlur(radius=2))
    img = Image.alpha_composite(img, p_layer)

    # ── Brain-wide energy pulse during flow (periodic breathing glow) ──────────
    if flow > 0.3:
        breath   = 0.5 + 0.5*math.sin(t * 1.6)
        glow_val = int(40 * (flow - 0.3) / 0.7 * breath)
        if glow_val > 2:
            breath_l = Image.new("RGBA", (W, H), (0,0,0,0))
            bd = ImageDraw.Draw(breath_l)
            pts_i = [(int(x), int(y)) for x,y in BRAIN_PTS]
            bd.polygon(pts_i, fill=(0, 150, 255, glow_val))
            breath_l = breath_l.filter(ImageFilter.GaussianBlur(radius=30))
            img = Image.alpha_composite(img, breath_l)

    # ── Fade-in at start ───────────────────────────────────────────────────────
    if t < 1.0:
        black = Image.new("RGBA", (W, H), (0,0,0,int(255*(1-t))))
        img   = Image.alpha_composite(img, black)

    return img.convert("RGB"), flow

# ── Main render loop ──────────────────────────────────────────────────────────
print(f"Rendering {FRAMES} frames...", flush=True)

cur_px = px.copy()
cur_py = py.copy()
cur_vx = vx.copy()
cur_vy = vy.copy()
cur_pos = part_path_pos.copy()

for f in range(FRAMES):
    t    = f / FPS
    flow = ease_in_out(clamp((t - 1.5) / 2.5))

    # Update particle positions
    # Chaos phase: random walk, bouncing inside brain region
    chaos_scale = 1.0 - flow
    if chaos_scale > 0.01:
        cur_px += cur_vx * chaos_scale
        cur_py += cur_vy * chaos_scale
        # Add jitter in chaos
        cur_vx += rng.uniform(-1.5, 1.5, N_PART) * chaos_scale
        cur_vy += rng.uniform(-1.5, 1.5, N_PART) * chaos_scale
        # Contain within brain area
        cur_vx = np.clip(cur_vx, -8, 8)
        cur_vy = np.clip(cur_vy, -8, 8)
        # Reflect off brain bbox
        cur_vx = np.where((cur_px < CX-BRX*0.8) | (cur_px > CX+BRX*0.8),
                          -cur_vx, cur_vx)
        cur_vy = np.where((cur_py < CY-BRY*0.8) | (cur_py > CY+BRY*0.8),
                          -cur_vy, cur_vy)
        cur_px = np.clip(cur_px, CX-BRX*0.85, CX+BRX*0.85)
        cur_py = np.clip(cur_py, CY-BRY*0.85, CY+BRY*0.85)

    # Flow phase: advance along path
    if flow > 0.01:
        cur_pos = (cur_pos + part_path_spd * flow) % 1.0
        for i in range(N_PART):
            pi  = part_path_idx[i]
            idx = int(cur_pos[i] * (len(PATHS_DENSE[pi])-1))
            path_targets[i] = PATHS_DENSE[pi][idx]

    img, _ = render(f, cur_px, cur_py, cur_vx, cur_vy, cur_pos)
    img.save(os.path.join(FRAME_DIR, f"frame_{f:04d}.png"))

    if f % 30 == 0:
        print(f"  {f}/{FRAMES}  t={t:.1f}s  flow={flow:.2f}", flush=True)

# ── Encode ────────────────────────────────────────────────────────────────────
print("Encoding...", flush=True)

mp4 = os.path.join(OUT_DIR, "flow_brain.mp4")
subprocess.run([
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", os.path.join(FRAME_DIR, "frame_%04d.png"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "slow", "-crf", "14",
    mp4
], capture_output=True)
print(f"  MP4 → {mp4}  ({os.path.getsize(mp4)/1e6:.1f} MB)")

shutil.rmtree(FRAME_DIR)
print("Done.")
