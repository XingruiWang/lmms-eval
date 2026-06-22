"""progress.py — XModBench reproduction progress dashboard.

Scans logs/xmod_bench_{lite,full}/results_<model>/ and prints a
per-model × {Lite,Full} progress bar with clean / contaminated status.
"clean" = a config whose latest sample file has <3% empty responses.
Goal = every model 6/6 clean on both splits (or its architectural max).
"""
import glob
import json
import os
import sys

ROOT = "/scratch/xwang378/2025/lmms-eval/logs"
MODELS = ["qwen2_5_omni_interleave", "qwen3_omni_interleave",
          "baichuan_omni_interleave", "minicpm_o_interleave",
          "video_salmonn_2", "omnivinci_interleave"]
CFG = ["a2t", "a2v", "t2a", "t2v", "v2a", "v2t"]
COMBO2CFG = {"audio_text": "a2t", "audio_image": "a2v", "audio_video": "a2v",
             "text_audio": "t2a", "text_image": "t2v", "text_video": "t2v",
             "image_audio": "v2a", "video_audio": "v2a",
             "image_text": "v2t", "video_text": "v2t"}
ARCH_MAX = {"omnivinci_interleave": 2}  # interleaved-media architectural cap


CFG_COMBOS = {"a2t": ["audio_text"], "a2v": ["audio_image", "audio_video"],
              "t2a": ["text_audio"], "t2v": ["text_image", "text_video"],
              "v2a": ["image_audio", "video_audio"],
              "v2t": ["image_text", "video_text"]}


def _stats(f):
    n = ok = e = 0
    for l in open(f):
        d = json.loads(l)
        s = d.get("xmod_bench_score")
        if not s:
            continue
        r = d.get("filtered_resps")
        r = r[0] if isinstance(r, list) and r else r
        n += 1
        ok += s["correct"]
        if str(r).strip() == "":
            e += 1
    return (ok, e, n)


def scan(split):
    """model -> {cfg: (empty_frac, n)} (config 'present' = all its combos)."""
    out = {}
    for m in MODELS:
        base = f"{ROOT}/xmod_bench_{split}/results_{m}"
        out[m] = {}
        if not os.path.isdir(base):
            continue
        newest = {}  # unit -> file  (unit = cfg for lite, combo for full)
        for f in glob.glob(base + "/**/*samples*.jsonl", recursive=True):
            bn = os.path.basename(f)
            unit = None
            if split == "lite":
                for c in CFG:
                    if bn.endswith(f"xmod_bench_lite_{c}.jsonl"):
                        unit = c
            else:
                for cb in COMBO2CFG:
                    if bn.endswith(f"_{cb}.jsonl"):
                        unit = cb
            if unit is None:
                continue
            if unit not in newest or os.path.getmtime(f) > os.path.getmtime(newest[unit]):
                newest[unit] = f
        st = {u: _stats(fp) for u, fp in newest.items()}
        for c in CFG:
            units = [c] if split == "lite" else CFG_COMBOS[c]
            have = [u for u in units if u in st and st[u][2] > 0]
            if len(have) != len(units):
                continue  # config not fully present yet
            tot = sum(st[u][2] for u in units)
            emp = sum(st[u][1] for u in units)
            out[m][c] = (emp / tot, tot)
    return out


def bar(done, clean, total, w=18):
    fill = int(round(clean / total * w))
    part = int(round(done / total * w)) - fill
    return "█" * fill + "▓" * max(0, part) + "·" * (w - fill - max(0, part))


def render():
    lite, full = scan("lite"), scan("full")
    print("XModBench reproduction progress  (█ clean  ▓ done-but-empty>3%  · todo)")
    print("=" * 72)
    overall_clean = overall_target = 0
    for m in MODELS:
        cap = ARCH_MAX.get(m, 6)
        row = []
        for split, data in (("Lite", lite), ("Full", full)):
            cfgs = data.get(m, {})
            done = min(len(cfgs), cap)
            clean = min(sum(1 for v in cfgs.values() if v[0] < 0.03), cap)
            row.append((split, done, clean))
            overall_clean += min(clean, cap)
            overall_target += cap
        name = m.replace("_interleave", "").replace("_", "-")
        seg = "   ".join(
            f"{s} [{bar(d, c, cap)}] {c}/{cap}{'' if c == cap else f' ({d} run)'}"
            for s, d, c in row)
        flag = "  ⚠ arch-max 2/6" if m in ARCH_MAX else ""
        print(f"{name:24s} {seg}{flag}")
    pct = 100 * overall_clean / overall_target
    print("=" * 72)
    print(f"OVERALL: {overall_clean}/{overall_target} clean-config slots  "
          f"[{bar(overall_clean, overall_clean, overall_target, 30)}] {pct:.0f}%")


if __name__ == "__main__":
    render()
