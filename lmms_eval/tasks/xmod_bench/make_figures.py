"""make_figures.py — XModBench FULL-benchmark analysis figures.

Data: xmod_scores.json["full"] (parsed from the paper master table
result.tex; see parse_full_data.py). "Gemini 2.0 Flash" is excluded per
request. Metric definitions are fixed and printed into each caption.

Configs: a2t a2v t2a t2v v2a v2t   (Vision = Image ∪ Video)
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)
SCORES = json.load(open(os.path.join(HERE, "xmod_scores.json")))["full"]

EXCLUDE = {"Gemini 2.0 Flash"}
# order by config_avg desc for a stable, readable legend
MODELS = sorted((m for m in SCORES if m not in EXCLUDE),
                key=lambda m: -sum(SCORES[m]["config"].values()))
CFG = ["a2t", "a2v", "t2a", "t2v", "v2a", "v2t"]
A2T, A2V, T2A, T2V, V2A, V2T = range(6)
FAM = ["perception", "spatial", "temporal", "linguistic", "knowledge"]
FAM_LABELS = ["Perception", "Spatial", "Temporal", "Linguistic", "Knowledge"]
cmap = plt.get_cmap("turbo")
COLORS = {m: cmap(i / max(1, len(MODELS) - 1)) for i, m in enumerate(MODELS)}

def cfg(m):  return [SCORES[m]["config"][c] for c in CFG]
def fam(m):  return [SCORES[m]["family"][f] for f in FAM]

plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans",
                     "axes.grid": True, "grid.alpha": .3, "axes.axisbelow": True})
TITLE = "XModBench (full, 61,320 samples)"


def radar():
    N = len(FAM_LABELS)
    ang = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=(8.5, 7.5), subplot_kw=dict(polar=True))
    for m in MODELS:
        v = fam(m) + fam(m)[:1]
        ax.plot(ang, v, color=COLORS[m], lw=1.9, label=m)
        ax.fill(ang, v, color=COLORS[m], alpha=.05)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(FAM_LABELS, fontsize=12, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80])
    ax.set_yticklabels(["20", "40", "60", "80"], fontsize=8, color="#888")
    ax.set_title(f"Task Competence Gaps — {TITLE}", pad=30, fontsize=14, fontweight="bold")
    ax.legend(loc="center left", bbox_to_anchor=(1.18, .5), fontsize=8.5, frameon=False)
    fig.text(.5, .02, "Spatial & temporal stay low across all models even as linguistic/perception/knowledge climb.",
             ha="center", fontsize=9, style="italic", color="#555")
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig1_task_competence_radar.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def disparity():
    def d_at(c):  return (c[A2V] + c[V2A]) / 2 - (c[T2V] + c[V2T]) / 2   # 3rd=Vision
    def d_vt(c):  return (c[V2A] + c[A2V]) / 2 - (c[T2A] + c[A2T]) / 2   # 3rd=Audio
    def d_av(c):  return (c[A2T] + c[T2A]) / 2 - (c[V2T] + c[T2V]) / 2   # 3rd=Text
    panels = [("Audio vs. Text", "(3rd modality = Vision)", d_at, "Audio", "Text"),
              ("Visual vs. Text", "(3rd modality = Audio)", d_vt, "Visual", "Text"),
              ("Audio vs. Vision", "(3rd modality = Text)", d_av, "Audio", "Vision")]
    allv = [fn(cfg(m)) for _, _, fn, _, _ in panels for m in MODELS]
    ymin = min(allv) * 1.18
    fig, axes = plt.subplots(1, 3, figsize=(17, 6.6), sharey=True)
    x = np.arange(len(MODELS))
    for ax, (title, sub, fn, hi, lo) in zip(axes, panels):
        order = sorted(MODELS, key=lambda m: fn(cfg(m)), reverse=True)
        vals = [fn(cfg(m)) for m in order]
        cols = [COLORS[m] for m in order]
        ax.bar(x, vals, color=cols, width=.62, edgecolor="white", zorder=3)
        for xi, v, cc in zip(x, vals, cols):
            ax.plot([xi, xi], [0, v], color=cc, lw=1, alpha=.25, zorder=1)
        ax.axhline(0, color="#222", lw=1.6, zorder=2)
        for xi, v, cc in zip(x, vals, cols):
            ax.text(xi, v - 1.2, f"{v:+.0f}", ha="center", va="top",
                    fontsize=8.5, fontweight="bold", color=cc)
        ax.set_xticks(x)
        ax.set_xticklabels(order, rotation=38, ha="right", fontsize=8)
        ax.set_ylim(ymin, max(2, max(allv) + 2))
        ax.set_title(f"{title}\n{sub}", fontsize=12, fontweight="bold")
        ax.grid(axis="x", visible=False)
        ax.set_ylabel(f"↑ favors {hi}   ·   ↓ favors {lo}" if ax is axes[0]
                      else f"↑ {hi} · ↓ {lo}", fontsize=9)
    fig.suptitle(f"Modality Disparity — {TITLE}  (bars drop below 0: every model is systematically worse on audio)",
                 fontsize=13, fontweight="bold", y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(f"{OUT}/fig2_modality_disparity.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def imbalance():
    pairs = [("A–T", A2T, T2A, "A→T", "T→A"),
             ("A–V", A2V, V2A, "A→V", "V→A"),
             ("V–T", V2T, T2V, "V→T", "T→V")]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6))
    for ax, (name, i, j, li, lj) in zip(axes, pairs):
        for m in MODELS:
            c = cfg(m)
            x, y = (c[i] + c[j]) / 2, abs(c[i] - c[j])
            ax.scatter(x, y, s=120, color=COLORS[m], edgecolor="white", lw=1.3, zorder=3)
            ax.annotate(m, (x, y), textcoords="offset points", xytext=(6, 5),
                        fontsize=7.5, color="#333")
        ax.set_title(f"Directional Imbalance — {name}", fontsize=12, fontweight="bold")
        ax.set_xlabel(f"pair competence = (acc {li} + acc {lj}) / 2", fontsize=10)
        ax.set_ylabel(f"imbalance = |acc {li} − acc {lj}|", fontsize=10)
        ax.set_ylim(bottom=0)
        ax.margins(x=.16)
    fig.suptitle(f"Directional Imbalance — {TITLE}  (higher = the two directions of one modality pair disagree more)",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig3_directional_imbalance.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


radar(); disparity(); imbalance()
print(f"{len(MODELS)} models (FULL, excl. {EXCLUDE}):")
for m in MODELS:
    print(f"  {m:20s} cfgAvg={SCORES[m]['config_avg']}  famAvg={SCORES[m]['family_avg']}")
print("wrote fig1/fig2/fig3 ->", OUT)
