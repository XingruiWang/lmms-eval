#!/bin/bash
# Upload reproduced eval logs (per-sample jsonl + summary.json) to the
# XModBench HF dataset under eval_logs/<model>/<split>/.
#
# Usage: ./upload_eval_logs.sh <model> <split:lite|full>
#   ./upload_eval_logs.sh qwen2_5_omni_interleave lite
set -euo pipefail
MODEL=${1:?model}; SPLIT=${2:?split lite|full}
REPO=/home/xwang378/scratch/2025/lmms-eval
SRC="$REPO/logs/xmod_bench_${SPLIT}/results_${MODEL}"
[ -d "$SRC" ] || { echo "no results dir: $SRC"; exit 1; }

# Collect newest per-config sample file + any summary.json into a staging dir
STAGE=$(mktemp -d)
for f in $(ls -t "$SRC"/*/*samples_*.jsonl 2>/dev/null); do
  base=$(basename "$f" | sed -E 's/^[0-9_]+samples_//')
  [ -e "$STAGE/$base" ] || cp "$f" "$STAGE/$base"
done
"$REPO/.venv/bin/python" "$REPO/lmms_eval/tasks/xmod_bench/summarize.py" \
  --logs "$STAGE/" --out "$STAGE/summary.json" >/dev/null 2>&1 || true

"$REPO/.venv/bin/python" - "$MODEL" "$SPLIT" "$STAGE" <<'PY'
import sys
from huggingface_hub import HfApi
model, split, stage = sys.argv[1:4]
HfApi().upload_folder(
    folder_path=stage,
    path_in_repo=f"eval_logs/{model}/{split}",
    repo_id="RyanWW/XModBench",
    repo_type="dataset",
    commit_message=f"eval logs: {model} ({split})",
)
print(f"uploaded eval_logs/{model}/{split}")
PY
rm -rf "$STAGE"
