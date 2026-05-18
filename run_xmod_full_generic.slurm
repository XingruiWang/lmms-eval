#!/bin/bash
# Generic XModBench FULL runner (10 modality combinations, 61,320 samples).
# Pass MODEL / PRETRAINED / ENV / MODEL_ARGS_EXTRA via --export.
#SBATCH --job-name=xmod_full
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=18:00:00
#SBATCH --output=/home/xwang378/scratch/2025/lmms-eval/logs/xmod_bench_full/%x_%A_%a.log
#SBATCH --error=/home/xwang378/scratch/2025/lmms-eval/logs/xmod_bench_full/%x_%A_%a.log

TASKS=(
    xmod_bench_audio_text   # 0
    xmod_bench_text_audio   # 1
    xmod_bench_audio_image  # 2
    xmod_bench_image_audio  # 3
    xmod_bench_image_text   # 4
    xmod_bench_text_image   # 5
    xmod_bench_audio_video  # 6
    xmod_bench_text_video   # 7
    xmod_bench_video_audio  # 8
    xmod_bench_video_text   # 9
)
TASK=${TASKS[$SLURM_ARRAY_TASK_ID]}

MODEL=${MODEL:?set MODEL}
PRETRAINED=${PRETRAINED:?set PRETRAINED}
ENV=${ENV:?set ENV}
MODEL_ARGS_EXTRA=${MODEL_ARGS_EXTRA:-device_map=auto,attn_implementation=flash_attention_2}

REPO=/home/xwang378/scratch/2025/lmms-eval
export XMODBENCH=/home/xwang378/scratch/2025/AudioBench_data
export HF_HOME=/scratch/xwang378/hf_cache
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export TRANSFORMERS_CACHE="$HF_HOME/hub"
export NUMBA_CACHE_DIR=/tmp/numba_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID:-0}
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
mkdir -p "$NUMBA_CACHE_DIR" "$HF_HOME/hub" "$HF_HOME/datasets"

echo "=== Job $SLURM_JOB_ID array=$SLURM_ARRAY_TASK_ID model=$MODEL task=$TASK ==="
echo "Node: $(hostname)  GPU: $CUDA_VISIBLE_DEVICES"
date

OUT="$REPO/logs/xmod_bench_full/results_${MODEL}"
mkdir -p "$OUT"
cd "$REPO"
module load conda
conda activate "$ENV"

python -m lmms_eval \
    --model "$MODEL" \
    --model_args pretrained=${PRETRAINED},${MODEL_ARGS_EXTRA} \
    --tasks "$TASK" \
    --batch_size 1 \
    --output_path "$OUT" \
    --log_samples \
    --log_samples_suffix "$TASK"

echo "=== Done: $TASK ==="
date
