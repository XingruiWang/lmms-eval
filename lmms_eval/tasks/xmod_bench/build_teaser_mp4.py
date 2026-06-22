"""build_teaser_mp4.py — render the XModBench teaser as a real mp4
(no browser needed): matplotlib frames -> ffmpeg. ~20s, 1280x720,
dark brand theme. Mirrors teaser_short's story.
"""
import os, subprocess, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle, FancyBboxPatch
import matplotlib.image as mpimg

OUT = "/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench/teaser_assets/_mp4frames"
MP4 = "/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench/xmodbench_teaser.mp4"
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
DOG = mpimg.imread("/tmp/dog.jpg")
BG = "#070a12"; INK = "#e8edf6"; DIM = "#8b96ad"
G1 = "#7c8cf0"; OKC = "#38d39f"; BADC = "#ff5a6e"
FPS = 20
W, H = 1280, 720
plt.rcParams["font.family"] = "DejaVu Sans"
fid = [0]

def newfig():
    fig = plt.figure(figsize=(W/100, H/100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off"); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    return fig, ax

def save(fig):
    fig.savefig(f"{OUT}/f{fid[0]:04d}.png", facecolor=BG)
    plt.close(fig); fid[0] += 1

def hold(draw, n):
    for _ in range(n):
        fig, ax = newfig(); draw(ax, 1.0); save(fig)

def anim(draw, n):
    for i in range(n):
        fig, ax = newfig(); draw(ax, (i + 1) / n); save(fig)

def ease(t):
    return 1 - (1 - t) ** 3

# ---- S1 hook ----
def s1(ax, p):
    ax.text(.5, .92, "For ", ha="right", va="center", fontsize=30, color=INK,
            fontweight="bold", transform=ax.transAxes)
    ax.text(.5, .92, "Omni-modality Language Models", ha="left", va="center",
            fontsize=30, color=G1, fontweight="bold")
    ax.text(.5, .80, "Which represents a dog?", ha="center", fontsize=17,
            color=DIM, family="monospace")
    ax.imshow(DOG, extent=(.10, .40, .34, .74), aspect="auto", zorder=2)
    ax.add_patch(FancyBboxPatch((.10, .34), .30, .40, boxstyle="round,pad=0.004",
                 ec="#2a3a5c", fc="none", lw=1.5))
    if p > .3:
        ax.text(.25, .26, "🐕  Dog  ✓", ha="center", fontsize=18, color=OKC,
                fontweight="bold")
    # waveform
    xs = np.linspace(.60, .90, 26)
    hs = (np.abs(np.sin(np.linspace(0, 6, 26))) * .14 + .02)
    ax.bar(xs, hs, width=.008, bottom=.54 - hs / 2, color=G1)
    ax.add_patch(FancyBboxPatch((.60, .34), .30, .40, boxstyle="round,pad=0.004",
                 ec="#2a3a5c", fc="#0c1226", lw=1.5, zorder=0))
    if p > .55:
        ax.text(.75, .26, '"a person talking"  ✗', ha="center", fontsize=16,
                color=BADC, fontweight="bold")
    if p > .8:
        ax.text(.5, .12, "🐕  ≠  🔊", ha="center", fontsize=34, color=BADC,
                fontweight="bold")

def s1b(ax, p):
    s1(ax, 1.0)
    ax.text(.5, .045, "A model that knows a dog by sight can’t hear one.",
            ha="center", fontsize=19, color="#cfd8ea", fontweight="bold")

# ---- S2 triangle ----
def s2(ax, p):
    ax.text(.5, .90, "Three modalities · six cross-modal directions",
            ha="center", fontsize=24, color=INK, fontweight="bold")
    N = {"A": (.5, .72, "🔊 Audio", "#5b8def"),
         "V": (.27, .30, "👁 Vision", "#8b5cf6"),
         "T": (.73, .30, "🔤 Text", "#2bc4a8")}
    pairs = [("A", "V"), ("V", "A"), ("A", "T"), ("T", "A"), ("V", "T"), ("T", "V")]
    k = int(p * len(pairs) + .001)
    for idx, (a, b) in enumerate(pairs):
        if idx >= k:
            continue
        x1, y1 = N[a][0], N[a][1]; x2, y2 = N[b][0], N[b][1]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy); px, py = -dy / L, dx / L
        rad = .35 if idx % 2 == 0 else -.35
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                     connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>",
                     mutation_scale=18, lw=2.4, color=N[a][3], alpha=.9))
    for nid, (x, y, lab, c) in N.items():
        ax.add_patch(Circle((x, y), .085, fc=c, ec=c, alpha=.18, lw=2.5))
        ax.add_patch(Circle((x, y), .085, fc="none", ec=c, lw=2.5))
        ax.text(x, y, lab, ha="center", va="center", fontsize=17,
                color=INK, fontweight="bold")

# ---- S3 families ----
FAM = [("Perception", "#5b8def"), ("Spatial", "#f6a609"), ("Temporal", "#ef5a6e"),
       ("Linguistic", "#2bc4a8"), ("Knowledge", "#8b5cf6")]
def s3(ax, p):
    ax.text(.5, .88, "Five task families · 17 subtasks", ha="center",
            fontsize=25, color=INK, fontweight="bold")
    ax.text(.5, .80, "61,320 items", ha="center", fontsize=16, color=DIM,
            family="monospace")
    n = int(p * 5 + .001)
    for i, (nm, c) in enumerate(FAM):
        if i >= n:
            continue
        y = .64 - i * .115
        ax.add_patch(FancyBboxPatch((.28, y), .44, .085,
                     boxstyle="round,pad=0.006", fc=c, ec=c, alpha=.85))
        ax.text(.30, y + .042, nm, va="center", fontsize=18, color="#0a0e1a",
                fontweight="bold")

# ---- S4 collapse bars (Qwen3-Omni) ----
BARS = [("Perception", 79.7, "#5b8def", 0), ("Spatial", 35.2, "#f6a609", 1),
        ("Temporal", 41.4, "#ef5a6e", 1), ("Linguistic", 82.5, "#2bc4a8", 0),
        ("Knowledge", 77.4, "#8b5cf6", 0)]
def s4(ax, p):
    ax.text(.5, .90, "But spatial & temporal reasoning collapses",
            ha="center", fontsize=23, color=INK, fontweight="bold")
    base = .18
    for i, (nm, v, c, dz) in enumerate(BARS):
        x = .16 + i * .15
        hh = (v / 100) * .56 * ease(p)
        col = BADC if dz else c
        ax.add_patch(FancyBboxPatch((x, base), .10, hh,
                     boxstyle="round,pad=0.002", fc=col, ec=col))
        ax.text(x + .05, base + hh + .03, f"{v:.1f}", ha="center",
                fontsize=15, color="#fff", fontweight="bold")
        ax.text(x + .05, base - .04, nm, ha="center", fontsize=12, color=DIM)
    ax.text(.5, .07, "spatial 35.2 / temporal 41.4  vs  linguistic 82.5  —  "
            "Qwen3-Omni, XModBench-Lite", ha="center", fontsize=13, color=DIM,
            family="monospace")

# ---- S5 imbalance ----
def s5(ax, p):
    ax.text(.5, .88, "The same knowledge, unequal across modalities",
            ha="center", fontsize=22, color=INK, fontweight="bold")
    for i, (lab, val, c) in enumerate([("V→T", 79.7, "#7c8cf0"),
                                       ("T→V", 66.0, "#5b6bb0")]):
        y = .58 - i * .16
        ax.text(.18, y + .035, lab, fontsize=18, color="#cbd5e0",
                family="monospace")
        w = (val / 100) * .52 * ease(p)
        ax.add_patch(FancyBboxPatch((.26, y), w, .075,
                     boxstyle="round,pad=0.002", fc=c, ec=c))
        ax.text(.26 + w - .03, y + .037, f"{val:.1f}", ha="right",
                va="center", fontsize=15, color="#fff", fontweight="bold")
    if p > .6:
        ax.text(.5, .17, "−13.7", ha="center", fontsize=46, color=BADC,
                fontweight="bold")
        ax.text(.5, .08, "CAPABILITY LOST asking the same pair the other way "
                "· Qwen3-Omni · directional imbalance",
                ha="center", fontsize=12, color="#ff9aa6", family="monospace")

# ---- S6 card ----
def s6(ax, p):
    ax.text(.5, .60, "XModBench", ha="center", fontsize=52, color=G1,
            fontweight="bold")
    ax.text(.5, .50, "Cross-modal consistency, measured.", ha="center",
            fontsize=20, color=DIM)
    ax.text(.5, .40, "ICLR 2026", ha="center", fontsize=16, color="#9db8ff",
            family="monospace")
    ax.text(.5, .33, "xingruiwang.github.io/projects/XModBench", ha="center",
            fontsize=14, color="#7fa6ff", family="monospace")

anim(s1, 26); hold(s1b, 30)
anim(s2, 28); hold(s2, 16)
anim(s3, 22); hold(s3, 16)
anim(s4, 26); hold(s4, 20)
anim(s5, 26); hold(s5, 22)
hold(s6, 40)
print(f"{fid[0]} frames")

subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{OUT}/f%04d.png",
                "-vf", "fade=t=in:st=0:d=0.4,format=yuv420p",
                "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                "-movflags", "+faststart", MP4], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("wrote", MP4, os.path.getsize(MP4) // 1024, "KB")
