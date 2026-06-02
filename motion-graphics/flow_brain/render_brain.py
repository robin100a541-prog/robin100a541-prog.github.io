#!/usr/bin/env python3
"""
FLOW STATE — Premium Brain Neural Visualization v2
1920×1080 · 30fps · 10s · YouTube 16:9

Color arc:
  0–1.5s  → fade-in, brain materialises from void
  1.5–3s  → crimson/orange chaos (overthinking storm)
  3–5.5s  → electric-purple transition (mind slowing)
  5.5–10s → gold nodes + cyan streams (full flow state)
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import subprocess, os, shutil, math

W, H   = 1920, 1080
FPS    = 30
DUR    = 10.0
FRAMES = int(DUR * FPS)   # 300
CX, CY = W // 2, H // 2
BRX, BRY = 390, 308

OUT_DIR   = "/home/user/robin-/motion-graphics/flow_brain"
FRAME_DIR = os.path.join(OUT_DIR, "_frames")
os.makedirs(FRAME_DIR, exist_ok=True)

rng = np.random.default_rng(42)

# ── Helpers ───────────────────────────────────────────────────────────────────
def clamp(v, lo=0.0, hi=1.0): return max(lo, min(hi, v))
def ease_in_out(t): t=clamp(t); return t*t*(3-2*t)
def ease_out(t):    t=clamp(t); return 1-(1-t)**3
def lerp(a, b, t):  return a*(1-clamp(t)) + b*clamp(t)
def lerp_col(a, b, t):
    t = clamp(t)
    return tuple(int(a[i]*(1-t) + b[i]*t) for i in range(3))

# ── Premium colour palette ────────────────────────────────────────────────────
BG           = (2,  3,  12)
CHAOS_COL    = (255,  55,  30)    # deep crimson-orange
TRANS_COL    = (160,  40, 255)    # electric purple
FLOW_COL     = (  0, 210, 255)    # electric cyan
GOLD_COL     = (255, 200,  50)    # synaptic gold
WHITE        = (255, 255, 255)

# ── Brain silhouette ──────────────────────────────────────────────────────────
def brain_polygon(cx, cy, rx, ry, n=600):
    pts = []
    for i in range(n):
        theta = 2*math.pi*i/n
        r  = 1.0
        r += 0.085 * math.sin(5  * theta + 0.20)
        r += 0.055 * math.sin(9  * theta + 1.10)
        r += 0.032 * math.sin(14 * theta + 2.30)
        r += 0.018 * math.sin(20 * theta + 0.70)
        r += 0.010 * math.sin(28 * theta + 1.90)
        flat = 1.0 - 0.14 * max(0, -math.sin(theta))**1.5
        asym = 1.0 + 0.025 * math.cos(theta)
        pts.append((cx + rx * r * flat * asym * math.cos(theta),
                    cy + ry * r * flat *          math.sin(theta)))
    return pts

BRAIN_PTS = brain_polygon(CX, CY, BRX, BRY)

# ── Neural pathways ───────────────────────────────────────────────────────────
def npt(dx, dy): return (CX+dx, CY+dy)

RAW_PATHS = [
    # Left hemisphere
    [npt(-20,-10), npt(-85,-95), npt(-160,-148), npt(-238,-158), npt(-300,-112), npt(-335,-22)],
    [npt(-20,-10), npt(-95,-52), npt(-178,-72),  npt(-258,-58),  npt(-322, 28)],
    [npt(-20,-10), npt(-88, 38), npt(-178, 72),  npt(-245, 82),  npt(-312, 62)],
    [npt(-20,-10), npt(-72,-105),npt(-138,-168), npt(-205,-198), npt(-245,-188)],
    [npt(-20,-10), npt(-125,-82),npt(-218,-125), npt(-288,-148)],
    [npt(-20,-10), npt(-115, 28),npt(-218,  32), npt(-288,  18)],
    [npt(-20,-10), npt(-65,  82),npt(-148, 132), npt(-235, 122), npt(-298,  82)],
    # Right hemisphere
    [npt( 20,-10), npt( 85,-95), npt( 160,-148), npt( 238,-158), npt( 300,-112), npt( 335,-22)],
    [npt( 20,-10), npt( 95,-52), npt( 178,-72),  npt( 258,-58),  npt( 322, 28)],
    [npt( 20,-10), npt( 88, 38), npt( 178, 72),  npt( 245, 82),  npt( 312, 62)],
    [npt( 20,-10), npt( 72,-105),npt( 138,-168), npt( 205,-198), npt( 245,-188)],
    [npt( 20,-10), npt( 125,-82),npt( 218,-125), npt( 288,-148)],
    [npt( 20,-10), npt( 115, 28),npt( 218,  32), npt( 288,  18)],
    [npt( 20,-10), npt(  65, 82),npt( 148, 132), npt( 235, 122), npt( 298,  82)],
    # Corpus callosum cross-connections
    [npt(-242,-82), npt(-122,-38), npt(0,-18), npt( 122,-38), npt( 242,-82)],
    [npt(-222, 62), npt(-112, 32), npt(0, 22), npt( 112, 32), npt( 222, 62)],
    [npt(-185,-152),npt( -88,-112), npt(0,-92), npt(  88,-112), npt( 185,-152)],
]

def interpolate_path(waypts, n=180):
    if len(waypts) < 2: return waypts
    segs    = len(waypts) - 1
    pts_per = max(2, n // segs)
    out     = []
    for i in range(segs):
        p0, p1 = waypts[i], waypts[i+1]
        for k in range(pts_per):
            tt = k / pts_per
            out.append((p0[0]*(1-tt)+p1[0]*tt, p0[1]*(1-tt)+p1[1]*tt))
    out.append(waypts[-1])
    return out

PATHS_DENSE = [interpolate_path(p, 180) for p in RAW_PATHS]
N_PATHS     = len(PATHS_DENSE)
NODES       = list({tuple(p[0]) for p in RAW_PATHS} | {tuple(p[-1]) for p in RAW_PATHS})

# ── Particles ─────────────────────────────────────────────────────────────────
N_PART   = 900
TAIL_LEN = 14

px = rng.uniform(CX - BRX*0.85, CX + BRX*0.85, N_PART)
py = rng.uniform(CY - BRY*0.85, CY + BRY*0.85, N_PART)
vx = rng.uniform(-7, 7, N_PART)
vy = rng.uniform(-7, 7, N_PART)

part_path_idx = rng.integers(0, N_PATHS, N_PART)
part_path_pos = rng.uniform(0, 1, N_PART)
part_path_spd = rng.uniform(0.004, 0.012, N_PART)
part_size     = rng.uniform(0.8, 2.8, N_PART)

path_targets = np.zeros((N_PART, 2))
for i in range(N_PART):
    pi  = part_path_idx[i]
    idx = int(part_path_pos[i] * (len(PATHS_DENSE[pi])-1))
    path_targets[i] = PATHS_DENSE[pi][idx]

px_hist = np.tile(px, (TAIL_LEN, 1)).copy()
py_hist = np.tile(py, (TAIL_LEN, 1)).copy()

# Energy ring emission times (flow phase)
RING_TIMES = [5.5, 6.4, 7.3, 8.2, 9.1]

# ── Precompute brain base (static) ────────────────────────────────────────────
print("Precomputing premium brain base...", flush=True)

def make_brain_base():
    base = Image.new("RGBA", (W, H), (*BG, 255))

    # Deep cosmic background — layered purple nebula
    cosmic = Image.new("RGBA", (W, H), (0,0,0,0))
    cd     = ImageDraw.Draw(cosmic)
    nebula_specs = [
        (1000, 600, ( 55,  0, 110), 0.22),
        ( 720, 432, ( 35, 10,  95), 0.28),
        ( 500, 300, ( 18, 18,  85), 0.32),
        ( 340, 204, (  8, 25,  75), 0.25),
        ( 200, 120, (  4, 35,  65), 0.18),
    ]
    for rx, ry, col, a_mult in nebula_specs:
        for s in range(6, 0, -1):
            frac = s / 6
            a = int(255 * a_mult * frac)
            cd.ellipse([CX-int(rx*frac*1.75), CY-int(ry*frac),
                        CX+int(rx*frac*1.75), CY+int(ry*frac)],
                       fill=(*col, a))
    cosmic = cosmic.filter(ImageFilter.GaussianBlur(radius=90))
    base   = Image.alpha_composite(base, cosmic)

    # Ambient star dust
    star_l = Image.new("RGBA", (W, H), (0,0,0,0))
    sd     = ImageDraw.Draw(star_l)
    srng   = np.random.default_rng(77)
    sx = srng.uniform(0, W, 280).astype(int)
    sy = srng.uniform(0, H, 280).astype(int)
    sa = srng.integers(15, 65, 280)
    sr = srng.uniform(0.4, 1.6, 280)
    for i in range(280):
        r = sr[i]
        sd.ellipse([sx[i]-r, sy[i]-r, sx[i]+r, sy[i]+r],
                   fill=(160, 190, 255, int(sa[i])))
    base = Image.alpha_composite(base, star_l)

    pts_i = [(int(x), int(y)) for x,y in BRAIN_PTS]

    # Multi-layer premium brain glow (7 layers: purple→blue→cyan)
    glow_specs = [
        (90, ( 65,  0, 130), 0.09),
        (70, ( 45, 15, 165), 0.13),
        (52, ( 22, 55, 215), 0.17),
        (38, ( 10,115, 255), 0.22),
        (24, (  0,165, 255), 0.30),
        (14, (  0,205, 255), 0.42),
        ( 6, (140,235, 255), 0.58),
    ]
    for gr, col, am in glow_specs:
        gl = Image.new("RGBA", (W, H), (0,0,0,0))
        gd = ImageDraw.Draw(gl)
        gd.polygon(pts_i, outline=(*col, int(255*am)), fill=None)
        gl = gl.filter(ImageFilter.GaussianBlur(radius=gr))
        base = Image.alpha_composite(base, gl)

    # Crisp brain outline — triple pass
    out_l = Image.new("RGBA", (W, H), (0,0,0,0))
    od    = ImageDraw.Draw(out_l)
    od.polygon(pts_i, outline=(0,  170, 255,  70), fill=None)  # soft halo
    od.polygon(pts_i, outline=(90, 200, 255, 200), fill=None)  # main
    od.polygon(pts_i, outline=(220,245, 255, 140), fill=None)  # bright core
    base = Image.alpha_composite(base, out_l)

    # Subtle interior fill
    fill_l = Image.new("RGBA", (W, H), (0,0,0,0))
    fd     = ImageDraw.Draw(fill_l)
    fd.polygon(pts_i, fill=(6, 18, 55, 20))
    base   = Image.alpha_composite(base, fill_l)

    # Gyri / sulci texture arcs
    gyri_l = Image.new("RGBA", (W, H), (0,0,0,0))
    gyd    = ImageDraw.Draw(gyri_l)
    for acx, acy, arx, ary, a0, a1 in [
        (CX-145, CY-65,  148, 95,  195, 345),
        (CX-125, CY+45,  105, 65,  188, 358),
        (CX-185, CY-105,  95, 65,  215, 332),
        (CX- 82, CY-128, 115, 72,  198, 352),
        (CX+145, CY-65,  148, 95,  195, 345),
        (CX+125, CY+45,  105, 65,  188, 358),
        (CX+185, CY-105,  95, 65,  215, 332),
        (CX+ 82, CY-128, 115, 72,  198, 352),
    ]:
        gyd.arc([acx-arx, acy-ary, acx+arx, acy+ary], a0, a1,
                fill=(45, 95, 195, 20), width=1)
    gyri_l = gyri_l.filter(ImageFilter.GaussianBlur(radius=1.8))
    base   = Image.alpha_composite(base, gyri_l)

    # Hemisphere divider
    div_l = Image.new("RGBA", (W, H), (0,0,0,0))
    dd    = ImageDraw.Draw(div_l)
    for dy in range(-BRY+55, BRY-55, 3):
        dd.ellipse([CX-2, CY+dy-2, CX+2, CY+dy+2], fill=(75, 135, 255, 26))
    div_l = div_l.filter(ImageFilter.GaussianBlur(radius=3))
    base  = Image.alpha_composite(base, div_l)

    # Dim path skeleton
    path_l = Image.new("RGBA", (W, H), (0,0,0,0))
    pd     = ImageDraw.Draw(path_l)
    for path in PATHS_DENSE:
        pts2 = [(int(x), int(y)) for x,y in path]
        if len(pts2) > 1:
            pd.line(pts2, fill=(18, 52, 135, 48), width=1)
    path_l = path_l.filter(ImageFilter.GaussianBlur(radius=1))
    base   = Image.alpha_composite(base, path_l)

    # Cinematic vignette (precomputed with NumPy)
    yy, xx = np.mgrid[0:H, 0:W]
    nx_v   = (xx - W/2) / (W/2)
    ny_v   = (yy - H/2) / (H/2)
    dist   = np.sqrt(nx_v**2 * 0.7 + ny_v**2)    # wider horizontally
    v_a    = np.clip((dist - 0.52) / 0.48, 0, 1)**1.8
    vig_arr         = np.zeros((H, W, 4), dtype=np.uint8)
    vig_arr[:,:, 3] = (v_a * 195).astype(np.uint8)
    VIG = Image.fromarray(vig_arr, 'RGBA')
    base = Image.alpha_composite(base, VIG)

    return base

BRAIN_BASE = make_brain_base()
print("  Done.", flush=True)

# ── Per-frame render ──────────────────────────────────────────────────────────
def render(frame, cur_px, cur_py, px_hist, py_hist):
    t    = frame / FPS
    # flow 0→1 over 1.5s→5.0s
    flow = ease_in_out(clamp((t - 1.5) / 3.5))

    img = BRAIN_BASE.copy()

    # ── 1. Neural path streaks ────────────────────────────────────────────
    streak_l = Image.new("RGBA", (W, H), (0,0,0,0))
    sd       = ImageDraw.Draw(streak_l)
    STREAK   = 28

    for pi, path in enumerate(PATHS_DENSE):
        off   = pi * 0.32 + 0.55
        spd   = lerp(0.85 + 0.45*math.sin(pi*1.7), 0.28 + 0.10*math.sin(pi*2.1), flow)
        n_pul = 2 if flow < 0.4 else 1

        for k in range(n_pul):
            pulse_t  = (t * spd + off + k/n_pul) % 1.0
            head_idx = int(pulse_t * (len(path)-1))

            if flow < 0.42:
                col_h = lerp_col(CHAOS_COL, TRANS_COL, flow/0.42)
            else:
                col_h = lerp_col(TRANS_COL, FLOW_COL, (flow-0.42)/0.58)

            flicker = 1.0 if flow > 0.55 else max(0.25, abs(math.sin(t*28+pi*3.1+k*1.7)))

            for s in range(min(STREAK, head_idx)):
                idx       = head_idx - s
                px_s, py_s = path[idx]
                frac      = (1 - s/STREAK)**2
                a         = int(240 * frac * flicker)
                w         = max(1, int(3.5 * frac))
                sd.ellipse([px_s-w, py_s-w, px_s+w, py_s+w], fill=(*col_h, a))

    streak_l = streak_l.filter(ImageFilter.GaussianBlur(radius=3.5))
    img      = Image.alpha_composite(img, streak_l)

    # ── 2. Synaptic nodes (gold in flow, red-flash in chaos) ──────────────
    node_l = Image.new("RGBA", (W, H), (0,0,0,0))
    nd     = ImageDraw.Draw(node_l)
    for ni, (nx, ny) in enumerate(NODES):
        pulse = 0.5 + 0.5*math.sin(t*(2.0+ni*0.38) + ni*1.12)
        if flow < 0.38:
            flash = abs(math.sin(t*13+ni*2.8))
            col_n = lerp_col(CHAOS_COL, WHITE, flash * 0.6)
            a_n   = int(200 * flash)
        else:
            gold_t = clamp((flow-0.38)/0.62)
            col_n  = lerp_col(WHITE, GOLD_COL, gold_t)
            a_n    = int(145 * pulse)
        r_out = int(9 + 6*pulse*flow)
        nd.ellipse([nx-r_out, ny-r_out, nx+r_out, ny+r_out],
                   fill=(*col_n, int(a_n*0.38)))
        nd.ellipse([nx-4, ny-4, nx+4, ny+4],
                   fill=(*col_n, min(255, a_n)))

    node_l = node_l.filter(ImageFilter.GaussianBlur(radius=4))
    img    = Image.alpha_composite(img, node_l)

    # ── 3. Particles with comet tails ────────────────────────────────────
    p_l  = Image.new("RGBA", (W, H), (0,0,0,0))
    pdd  = ImageDraw.Draw(p_l)

    if flow < 0.5:
        col_p = lerp_col(CHAOS_COL, TRANS_COL, flow*2)
    else:
        col_p = lerp_col(TRANS_COL, FLOW_COL, (flow-0.5)*2)

    # Tail layers: oldest → newest
    for tail_i in range(TAIL_LEN-1, -1, -1):
        tf    = (TAIL_LEN - tail_i) / TAIL_LEN
        t_a   = int(175 * tf**2.0 * (0.28 + 0.72*flow))
        t_sz  = max(1, round(2.2 * tf))
        if t_a < 5: continue

        tx_arr = px_hist[tail_i]*(1-flow) + path_targets[:,0]*flow
        ty_arr = py_hist[tail_i]*(1-flow) + path_targets[:,1]*flow

        for i in range(N_PART):
            tx, ty = float(tx_arr[i]), float(ty_arr[i])
            if 8 < tx < W-8 and 8 < ty < H-8:
                pdd.ellipse([tx-t_sz, ty-t_sz, tx+t_sz, ty+t_sz],
                            fill=(*col_p, t_a))

    # Head
    cx_arr  = cur_px*(1-flow) + path_targets[:,0]*flow
    cy_arr  = cur_py*(1-flow) + path_targets[:,1]*flow
    head_col = lerp_col(col_p, WHITE, flow*0.55)
    head_a   = int(235 * (0.38 + 0.62*flow))
    for i in range(N_PART):
        cx_i, cy_i = float(cx_arr[i]), float(cy_arr[i])
        sz = max(1, round(part_size[i] * (0.7 + 0.5*flow)))
        if 8 < cx_i < W-8 and 8 < cy_i < H-8:
            pdd.ellipse([cx_i-sz, cy_i-sz, cx_i+sz, cy_i+sz],
                        fill=(*head_col, head_a))

    p_l = p_l.filter(ImageFilter.GaussianBlur(radius=1.8))
    img = Image.alpha_composite(img, p_l)

    # ── 4. Energy rings (flow reveal) ─────────────────────────────────────
    if flow > 0.45:
        ring_l = Image.new("RGBA", (W, H), (0,0,0,0))
        rd     = ImageDraw.Draw(ring_l)
        for rt in RING_TIMES:
            since = t - rt
            if 0 <= since <= 2.2:
                prog  = since / 2.2
                rad   = int(prog * 520)
                alpha = int(140 * (1-prog)**2 * flow)
                if alpha > 3 and rad > 6:
                    rd.ellipse([CX-rad, CY-rad, CX+rad, CY+rad],
                               outline=(*FLOW_COL, alpha), width=2)
                    r2 = max(1, rad-12)
                    rd.ellipse([CX-r2, CY-r2, CX+r2, CY+r2],
                               outline=(255, 255, 255, int(alpha*0.35)), width=1)
        ring_l = ring_l.filter(ImageFilter.GaussianBlur(radius=4.5))
        img    = Image.alpha_composite(img, ring_l)

    # ── 5. Brain breathing glow (pulsing interior light) ──────────────────
    if flow > 0.28:
        breath   = 0.5 + 0.5*math.sin(t * 1.35)
        glow_val = int(68 * (flow-0.28)/0.72 * breath)
        if glow_val > 3:
            bl   = Image.new("RGBA", (W, H), (0,0,0,0))
            bd   = ImageDraw.Draw(bl)
            pts_i = [(int(x), int(y)) for x,y in BRAIN_PTS]
            bd.polygon(pts_i, fill=(0, 145, 255, glow_val))
            bl   = bl.filter(ImageFilter.GaussianBlur(radius=38))
            img  = Image.alpha_composite(img, bl)

    # ── 6. Fade in / fade out ─────────────────────────────────────────────
    if t < 1.4:
        fade = (1 - t/1.4)**1.6
        black = Image.new("RGBA", (W, H), (0,0,0,int(255*fade)))
        img   = Image.alpha_composite(img, black)
    if t > 9.2:
        fade  = (t - 9.2) / 0.8
        black = Image.new("RGBA", (W, H), (0,0,0,int(255*clamp(fade))))
        img   = Image.alpha_composite(img, black)

    return img.convert("RGB"), flow

# ── Main render loop ──────────────────────────────────────────────────────────
print(f"Rendering {FRAMES} frames...", flush=True)

cur_px = px.copy();  cur_py = py.copy()
cur_vx = vx.copy();  cur_vy = vy.copy()

for f in range(FRAMES):
    t    = f / FPS
    flow = ease_in_out(clamp((t - 1.5) / 3.5))

    # Update chaos particles
    cs = 1.0 - flow
    if cs > 0.005:
        cur_px += cur_vx * cs
        cur_py += cur_vy * cs
        cur_vx += rng.uniform(-1.8, 1.8, N_PART) * cs
        cur_vy += rng.uniform(-1.8, 1.8, N_PART) * cs
        cur_vx  = np.clip(cur_vx, -9, 9)
        cur_vy  = np.clip(cur_vy, -9, 9)
        cur_vx  = np.where((cur_px < CX-BRX*0.8) | (cur_px > CX+BRX*0.8), -cur_vx, cur_vx)
        cur_vy  = np.where((cur_py < CY-BRY*0.8) | (cur_py > CY+BRY*0.8), -cur_vy, cur_vy)
        cur_px  = np.clip(cur_px, CX-BRX*0.85, CX+BRX*0.85)
        cur_py  = np.clip(cur_py, CY-BRY*0.85, CY+BRY*0.85)

    # Advance flow particles along paths
    if flow > 0.008:
        part_path_pos[:] = (part_path_pos + part_path_spd * flow) % 1.0
        for i in range(N_PART):
            pi  = part_path_idx[i]
            idx = int(part_path_pos[i] * (len(PATHS_DENSE[pi])-1))
            path_targets[i] = PATHS_DENSE[pi][idx]

    # Update comet tail history
    px_hist = np.roll(px_hist, 1, axis=0)
    py_hist = np.roll(py_hist, 1, axis=0)
    px_hist[0] = cur_px*(1-flow) + path_targets[:,0]*flow
    py_hist[0] = cur_py*(1-flow) + path_targets[:,1]*flow

    img, fl = render(f, cur_px, cur_py, px_hist, py_hist)
    img.save(os.path.join(FRAME_DIR, f"frame_{f:04d}.png"))

    if f % 30 == 0:
        print(f"  {f}/{FRAMES}  t={t:.1f}s  flow={fl:.2f}", flush=True)

# ── Encode ────────────────────────────────────────────────────────────────────
print("Encoding...", flush=True)
mp4 = os.path.join(OUT_DIR, "flow_brain.mp4")
subprocess.run([
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", os.path.join(FRAME_DIR, "frame_%04d.png"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "slow", "-crf", "13",
    mp4
], capture_output=True)
print(f"  MP4 → {mp4}  ({os.path.getsize(mp4)/1e6:.1f} MB)")
shutil.rmtree(FRAME_DIR)
print("Done.")
