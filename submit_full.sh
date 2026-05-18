#!/bin/bash
# Submit the FULL XModBench sweep (10 modality combos, 61,320 samples) for one
# model. Mirrors submit_lite.sh's resource-aware split:
#   no-video combos (audio_text=0, text_audio=1)        -> $LIGHT_GRES
#   media-heavy combos (2..9: image/video options)      -> $HEAVY_GRES
#
# Usage:
#   [LIGHT_GRES=..] [HEAVY_GRES=..] ./submit_full.sh MODEL PRETRAINED ENV [EXTRA]
set -euo pipefail
MODEL=${1:?MODEL}; PRETRAINED=${2:?PRETRAINED}; ENV=${3:?ENV}
EXTRA=${4:-device_map=auto,attn_implementation=flash_attention_2}
LIGHT_GRES=${LIGHT_GRES:-gpu:a5000:4}
HEAVY_GRES=${HEAVY_GRES:-gpu:a5000:4}

mkdir -p /home/xwang378/scratch/2025/lmms-eval/logs/xmod_bench_full
COMMON="--export=ALL,MODEL=${MODEL},PRETRAINED=${PRETRAINED},ENV=${ENV},MODEL_ARGS_EXTRA=${EXTRA} \
        --job-name=xf_${MODEL} run_xmod_full_generic.slurm"

echo "[$MODEL] no-video combos audio_text,text_audio -> $LIGHT_GRES"
sbatch --array=0,1 --gres="$LIGHT_GRES" $COMMON

echo "[$MODEL] media combos (image/video) -> $HEAVY_GRES"
sbatch --array=2-9 --gres="$HEAVY_GRES" $COMMON

echo "Submitted. Watch: squeue -u $USER"
