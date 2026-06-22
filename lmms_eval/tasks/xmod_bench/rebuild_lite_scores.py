"""rebuild_lite_scores.py — assemble the website Lite leaderboard from the
BEST available source per model, then sync xmod_scores.json + the inlined
DATA in the project page.

priority: real lmms-eval Lite run  >  our clean full-derived  >
          results-current full gate-derived  >  author lite json
Only models we actually Lite-ran on lmms-eval are kept as-is; everything
else is (re)derived faithfully from per-sample full where possible.
"""
import collections
import glob
import json
import os

LL = "/scratch/xwang378/2025/lmms-eval/logs/xmod_bench_lite"
SCORES = "/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench/xmod_scores.json"
IDX = "/scratch/xwang378/2025/xingruiwang.github.io/projects/XModBench/index.html"
CFG = ["a2t", "a2v", "t2a", "t2v", "v2a", "v2t"]
FAMS = ["perception", "spatial", "temporal", "linguistic", "knowledge"]
FAM = {"01_perception": "perception", "02_spatial": "spatial",
       "03_speech": "linguistic", "04_temporal": "temporal",
       "05_Exteral": "knowledge"}

# real lmms-eval Lite runs: dir -> display name (empty>3% configs dropped)
REAL = {"qwen2_5_omni_interleave": "Qwen2.5-Omni",
        "qwen3_omni_interleave": "Qwen3-Omni",
        "baichuan_omni_interleave": "Baichuan-Omni-1.5",
        "minicpm_o_interleave": "MiniCPM-o-2.6",
        "omnivinci_interleave": "OmniVinci",
        "video_salmonn_2": "video-SALMONN-2"}
# gate-derived from results-current per-sample full
GATE = {"gemini-2.5-pro": "Gemini 2.5 Pro", "gemini-2.5-flash": "Gemini 2.5 Flash",
        "gemini-2.0-pro": "Gemini 2.0 Pro"}


def avg(d):
    v = [x for x in d.values() if x is not None]
    return round(sum(v) / len(v), 1) if v else None


def from_real(dirn):
    base = f"{LL}/results_{dirn}"
    cfg_n = collections.Counter(); cfg_ok = collections.Counter()
    cfg_e = collections.Counter()
    fam_n = collections.Counter(); fam_ok = collections.Counter()
    seen = {}
    for f in glob.glob(base + "/**/*samples*xmod_bench_lite_*.jsonl", recursive=True):
        c = f.split("xmod_bench_lite_")[-1].split(".")[0]
        if c not in seen or os.path.getmtime(f) > os.path.getmtime(seen[c]):
            seen[c] = f
    for c, f in seen.items():
        n = ok = e = 0
        fa = collections.Counter(); fo = collections.Counter()
        for l in open(f):
            d = json.loads(l)
            s = d.get("xmod_bench_score")
            if not s:
                continue
            r = d.get("filtered_resps")
            r = r[0] if isinstance(r, list) and r else r
            n += 1; ok += s["correct"]
            if str(r).strip() == "":
                e += 1
            fa[s["family"]] += 1; fo[s["family"]] += s["correct"]
        if n and e / n < 0.03:                       # clean configs only
            cfg_n[c] = n; cfg_ok[c] = ok
            for k in fa:
                fam_n[k] += fa[k]; fam_ok[k] += fo[k]
    config = {c: round(100 * cfg_ok[c] / cfg_n[c], 1) for c in CFG if cfg_n[c]}
    family = {k: round(100 * fam_ok[k] / fam_n[k], 1) for k in FAMS if fam_n[k]}
    if not config:
        return None
    return {"config": config, "family": family,
            "config_avg": avg(config), "family_avg": avg(family), "src": "real"}


def from_gate(slug):
    rep = f"{LL}/results_gate_{slug}/samples.report.json"
    if not os.path.exists(rep):
        return None
    r = json.load(open(rep))
    config = {c: round(r[c]["acc_over_covered"], 1) for c in CFG
              if r.get(c) and r[c]["acc_over_covered"] is not None}
    fam_ok = collections.Counter(); fam_c = collections.Counter()
    for c in CFG:
        for fm, dd in r.get(c, {}).get("by_family", {}).items():
            if dd["covered"]:
                fam_ok[fm] += dd["acc"] * dd["covered"] / 100
                fam_c[fm] += dd["covered"]
    family = {k: round(100 * fam_ok[k] / fam_c[k], 1) for k in FAMS if fam_c[k]}
    if not config:
        return None
    return {"config": config, "family": family,
            "config_avg": avg(config), "family_avg": avg(family), "src": "gate"}


d = json.load(open(SCORES))
lite = {}
# (no Qwen2.5-Omni*: we have a real lmms-eval Lite run for Qwen2.5-Omni,
#  so the full-derived Lite duplicate is not published)
# 2. real lmms-eval Lite runs
for dirn, name in REAL.items():
    r = from_real(dirn)
    if r:
        lite[name] = r
# 3. gate-derived geminis
for slug, name in GATE.items():
    g = from_gate(slug)
    if g:
        lite[name] = g
# (no author-json fallback: all_model_result_lite.json is the OLD lite
#  sample set and must never be published — valid Lite = real lmms-eval
#  run | our clean full-derived | gate-derived from per-sample full)

d["lite"] = {k: {kk: vv for kk, vv in v.items()} for k, v in lite.items()}
json.dump(d, open(SCORES, "w"), indent=1)

import re
mini = json.dumps(d, separators=(",", ":"))
s = open(IDX).read()
s2 = re.sub(r"const DATA = \{.*?\};", "const DATA = " + mini + ";", s, count=1, flags=re.S)
assert s2 != s, "inline DATA not replaced"
open(IDX, "w").write(s2)
print("Lite leaderboard rebuilt:")
for k, v in d["lite"].items():
    print(f"  {k:20s} cfgAvg={v.get('config_avg')}  src={v.get('src')}")
