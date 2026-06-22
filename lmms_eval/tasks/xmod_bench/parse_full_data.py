"""parse_full_data.py — extract the paper's master table (result.tex) into
a shared JSON used by both the static figures and the website D3 viz.

result.tex layout: 3 tabular blocks, each two 8-col sections
(6 configs + Avg + Std). Sections in order:
  block1: Overall | Task1 Perception
  block2: Task2 Spatial | Task3 Temporal
  block3: Task4 Linguistic | Task5 External Knowledge
"""
import json
import re
from pathlib import Path

TEX = Path("/home/xwang378/scratch/2025/AudioBench/benchmark/scripts/metric/result.tex")
OUT = Path("/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench/xmod_scores.json")

CFG = ["a2t", "a2v", "t2a", "t2v", "v2a", "v2t"]
SECTIONS = [
    ["overall", "perception"],
    ["spatial", "temporal"],
    ["linguistic", "knowledge"],
]
NAME = {  # normalize to the names used on the site
    "PandaGPT": "PandaGPT", "Unified-IO 2": "Unified-IO 2",
    "Unified-IO 2 XL": "Unified-IO 2 XL", "Unified-IO 2 XXL": "Unified-IO 2 XXL",
    "VideoLLaMA 2": "VideoLLaMA 2", "VITA": "VITA",
    "Baichuan Omni 1.5": "Baichuan-Omni-1.5", "EchoInk-R1": "EchoInk-R1",
    "Qwen2.5-Omni": "Qwen2.5-Omni", "Gemini 1.5 Pro": "Gemini 1.5 Pro",
    "Gemini 2.0 Flash": "Gemini 2.0 Flash", "Gemini 2.5 Flash": "Gemini 2.5 Flash",
    "Gemini 2.5 Pro": "Gemini 2.5 Pro",
}

tex = TEX.read_text()
blocks = re.findall(r"\\begin\{tabular\}.*?\\end\{tabular\}", tex, re.S)
assert len(blocks) == 3, f"expected 3 tabular blocks, got {len(blocks)}"

data: dict[str, dict] = {}
for bi, block in enumerate(blocks):
    left, right = SECTIONS[bi]
    for line in block.splitlines():
        if "\\perfcell" not in line:
            continue
        raw = line.split("&", 1)[0].strip()
        if raw not in NAME:
            continue
        model = NAME[raw]
        # split into cells; each cell may be \textbf{\perfcell{N}} / \perfcell{N}
        # / {N}. Pull the first number from each. Layout per data row:
        # Model & [6 cfg, Avg, Std]_left & [6 cfg, Avg, Std]_right
        cells = line.split("\\\\")[0].split("&")[1:]
        def num(c):
            m = re.search(r"[-+]?\d*\.?\d+", c)
            return float(m.group()) if m else None
        vals = [num(c) for c in cells]
        seg_l, avg_l = vals[0:6], vals[6]
        seg_r, avg_r = vals[8:14], vals[14]
        assert None not in seg_l + seg_r and avg_l is not None and avg_r is not None, (model, vals)
        d = data.setdefault(model, {"config": {}, "family": {}})
        if left == "overall":
            d["config"] = dict(zip(CFG, seg_l))
        else:
            d["family"][left] = avg_l
        d["family"][right] = avg_r

for m, d in data.items():
    d["family_avg"] = round(sum(d["family"].values()) / len(d["family"]), 1)
    d["config_avg"] = round(sum(d["config"].values()) / 6, 1)

OUT.write_text(json.dumps({"full": data}, indent=1))
print(f"wrote {OUT}  ({len(data)} models, FULL)")
for m, d in data.items():
    print(f"  {m:22s} cfg={d['config']}  fam={d['family']}")
