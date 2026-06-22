"""lite_from_full.py — derive a model's XModBench-Lite scores from its
*full* per-sample logs, no re-run. Lite is a deterministic stratified
subsample of the full combo JSONLs (make_lite, seed 42); our lmms-eval
full sample logs carry doc_id == line index of data/<combo>.jsonl, so
each Lite row maps EXACTLY to one full prediction by fingerprint.

Usage: lite_from_full.py <model_dir_name>
  (model_dir_name under logs/xmod_bench_full/results_<name>)
"""
import collections
import glob
import json
import os
import sys

DATA = "/home/xwang378/scratch/2025/AudioBench_data/data"
LITE = "/home/xwang378/scratch/2025/AudioBench_data/data_lite"
FULL = "/scratch/xwang378/2025/lmms-eval/logs/xmod_bench_full"
CONFIGS = {"a2t": ["audio_text"], "a2v": ["audio_image", "audio_video"],
           "t2a": ["text_audio"], "t2v": ["text_image", "text_video"],
           "v2a": ["image_audio", "video_audio"],
           "v2t": ["image_text", "video_text"]}
FAM = {"01_perception": "perception", "02_spatial": "spatial",
       "03_speech": "linguistic", "04_temporal": "temporal",
       "05_Exteral": "knowledge"}


def fam_of(sub):
    return FAM.get(sub.split("/", 1)[0], "other")


def fp(r):
    return json.dumps([r["subtask"], r["conditions"], r["options"],
                       r["correct_answer"]], sort_keys=True)


def main(model):
    base = f"{FULL}/results_{model}"
    # combo -> {doc_id: correct} from full sample logs
    full = {}
    for f in glob.glob(base + "/**/*samples*.jsonl", recursive=True):
        bn = os.path.basename(f)
        combo = next((c for combos in CONFIGS.values() for c in combos
                      if bn.endswith(f"_{c}.jsonl")), None)
        if combo is None:
            continue
        m = full.setdefault(combo, {})
        for line in open(f):
            d = json.loads(line)
            s = d.get("xmod_bench_score")
            if s is None:
                continue
            m[d["doc_id"]] = s["correct"]
    if not full:
        print(f"no full logs for {model}")
        return
    # combo -> {fingerprint: line_index}
    fpmap = {}
    for combo in {c for cs in CONFIGS.values() for c in cs}:
        p = f"{DATA}/{combo}.jsonl"
        if not os.path.exists(p):
            continue
        d = {}
        for i, line in enumerate(open(p)):
            d[fp(json.loads(line))] = i
        fpmap[combo] = d

    by_cfg = collections.Counter()
    ok_cfg = collections.Counter()
    by_fam = collections.Counter()
    ok_fam = collections.Counter()
    cov = miss = 0
    for cfg, combos in CONFIGS.items():
        lp = f"{LITE}/{cfg}.jsonl"
        if not os.path.exists(lp):
            continue
        for line in open(lp):
            r = json.loads(line)
            key = fp(r)
            hit = None
            for cb in combos:
                idx = fpmap.get(cb, {}).get(key)
                if idx is not None and cb in full and idx in full[cb]:
                    hit = full[cb][idx]
                    break
            if hit is None:
                miss += 1
                continue
            cov += 1
            fam = fam_of(r["subtask"])
            by_cfg[cfg] += 1
            ok_cfg[cfg] += hit
            by_fam[fam] += 1
            ok_fam[fam] += hit

    print(f"=== {model}: Lite derived from full logs ===")
    print(f"covered {cov} / {cov + miss} Lite samples\n")
    cavg = []
    for c in ["a2t", "a2v", "t2a", "t2v", "v2a", "v2t"]:
        if by_cfg[c]:
            a = 100 * ok_cfg[c] / by_cfg[c]
            cavg.append(a)
            print(f"  {c}: {a:5.1f}  (n={by_cfg[c]})")
    if cavg:
        print(f"  config Avg = {sum(cavg) / len(cavg):.1f}")
    print()
    favg = []
    for fm in ["perception", "spatial", "temporal", "linguistic", "knowledge"]:
        if by_fam[fm]:
            a = 100 * ok_fam[fm] / by_fam[fm]
            favg.append(a)
            print(f"  {fm:11s} {a:5.1f}  (n={by_fam[fm]})")
    if favg:
        print(f"  family Avg = {sum(favg) / len(favg):.1f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "qwen2_5_omni_interleave")
