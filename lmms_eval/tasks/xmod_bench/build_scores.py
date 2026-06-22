"""build_scores.py — combined Full+Lite per-model scores for the website.

FULL  ← result.tex (paper master table; via parse_full_data logic)
LITE  ← benchmark/all_model_result_lite.json (author's Lite result file:
         model → family → subtask → {6 configs})

Emits xmod_scores.json = {"full": {...}, "lite": {...}}, each model:
  {config:{6}, family:{5}, config_avg, family_avg}
"Gemini 2.0 Flash" and "random" are excluded.
"""
import json
import re
from pathlib import Path

ROOT = Path("/home/xwang378/scratch/2025/AudioBench")
HERE = Path("/scratch/xwang378/2025/lmms-eval/lmms_eval/tasks/xmod_bench")
OUT = HERE / "xmod_scores.json"

CFG = ["a2t", "a2v", "t2a", "t2v", "v2a", "v2t"]
CFG_JSON = {"audio_text": "a2t", "audio_vision": "a2v", "text_audio": "t2a",
            "text_vision": "t2v", "vision_audio": "v2a", "vision_text": "v2t"}
FAM = ["perception", "spatial", "temporal", "linguistic", "knowledge"]
# author's lite json uses 'speech'/'external' for linguistic/knowledge
FAM_JSON = {"perception": "perception", "spatial": "spatial",
            "temporal": "temporal", "linguistic": "speech", "knowledge": "external"}


def finalize(d):
    d["config_avg"] = round(sum(d["config"].values()) / 6, 1)
    d["family_avg"] = round(sum(d["family"].values()) / len(d["family"]), 1)
    return d


# ---------- FULL from result.tex ----------
def parse_full():
    tex = (ROOT / "benchmark/scripts/metric/result.tex").read_text()
    blocks = re.findall(r"\\begin\{tabular\}.*?\\end\{tabular\}", tex, re.S)
    sections = [["overall", "perception"], ["spatial", "temporal"],
                ["linguistic", "knowledge"]]
    name = {"PandaGPT": "PandaGPT", "Unified-IO 2": "Unified-IO 2",
            "Unified-IO 2 XL": "Unified-IO 2 XL", "Unified-IO 2 XXL": "Unified-IO 2 XXL",
            "VideoLLaMA 2": "VideoLLaMA 2", "VITA": "VITA",
            "Baichuan Omni 1.5": "Baichuan-Omni-1.5", "EchoInk-R1": "EchoInk-R1",
            "Qwen2.5-Omni": "Qwen2.5-Omni", "Gemini 1.5 Pro": "Gemini 1.5 Pro",
            "Gemini 2.0 Flash": "Gemini 2.0 Flash", "Gemini 2.5 Flash": "Gemini 2.5 Flash",
            "Gemini 2.5 Pro": "Gemini 2.5 Pro"}
    out = {}
    for bi, block in enumerate(blocks):
        left, right = sections[bi]
        for line in block.splitlines():
            if "\\perfcell" not in line:
                continue
            raw = line.split("&", 1)[0].strip()
            if raw not in name or name[raw] == "Gemini 2.0 Flash":
                continue
            cells = line.split("\\\\")[0].split("&")[1:]
            def num(c):
                m = re.search(r"[-+]?\d*\.?\d+", c)
                return float(m.group()) if m else None
            v = [num(c) for c in cells]
            d = out.setdefault(name[raw], {"config": {}, "family": {}})
            if left == "overall":
                d["config"] = dict(zip(CFG, v[0:6]))
            else:
                d["family"][left] = v[6]
            d["family"][right] = v[14]
    return {m: finalize(d) for m, d in out.items()}


# ---------- LITE from all_model_result_lite.json ----------
def parse_lite():
    raw = json.load(open(ROOT / "benchmark/all_model_result_lite.json"))
    disp = {"echoink": "EchoInk-R1", "gemini-1.5-pro": "Gemini 1.5 Pro",
            "gemini-2.0-pro": "Gemini 2.0 Pro", "gemini-2.5-flash": "Gemini 2.5 Flash",
            "gemini-2.5-pro": "Gemini 2.5 Pro", "qwen2.5_omni": "Qwen2.5-Omni",
            "qwen3-omni": "Qwen3-Omni", "qwen2.5_vl": "Qwen2.5-VL",
            "internvl3": "InternVL3", "omnivinci": "OmniVinci", "vita": "VITA",
            "panda": "PandaGPT", "anygpt": "AnyGPT", "reka": "Reka"}
    out = {}
    # vision-only models have no audio path → excluded from the 6-way
    # cross-modal tables (consistent with the paper).
    skip = {"random", "gemini-2.0-flash", "qwen2.5_vl", "internvl3", "anygpt"}
    for key, fams in raw.items():
        if key in skip or key not in disp:
            continue
        cfg_sum = {c: [0.0, 0] for c in CFG}
        fam_acc = {}
        for fkey, jfam in FAM_JSON.items():
            cells = fams.get(jfam, {})
            fvals = []
            for sub, cfgvals in cells.items():
                for jc, acc in cfgvals.items():
                    c = CFG_JSON.get(jc)
                    if c is None or acc is None:
                        continue
                    cfg_sum[c][0] += acc
                    cfg_sum[c][1] += 1
                    fvals.append(acc)
            if fvals:
                fam_acc[fkey] = round(sum(fvals) / len(fvals), 1)
        if len(fam_acc) < 5:
            continue
        config = {c: round(cfg_sum[c][0] / cfg_sum[c][1], 1) if cfg_sum[c][1] else 0.0
                  for c in CFG}
        out[disp[key]] = finalize({"config": config, "family": fam_acc})
    return out


data = {"full": parse_full(), "lite": parse_lite()}
OUT.write_text(json.dumps(data, indent=1))
print(f"wrote {OUT}")
for split in ("full", "lite"):
    print(f"\n[{split}] {len(data[split])} models")
    for m, d in sorted(data[split].items(), key=lambda kv: -kv[1]["config_avg"]):
        print(f"  {m:20s} cfgAvg={d['config_avg']:5}  famAvg={d['family_avg']:5}")
