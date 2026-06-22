#!/bin/bash
#SBATCH --job-name=vs72_lite
#SBATCH --gres=gpu:6000_ada:4
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=6:00:00
#SBATCH --output=/scratch/xwang378/2025/lmms-eval/logs/vs72_lite_%A_%a.log
#SBATCH --array=0-5
# video-SALMONN-2+ 72B: ~144 GB bf16 → 4×48 GB ada (192 GB) with device_map=auto.
# Same wrapper as 7B (already has CUDA_HOME auto-set fix).
cd /scratch/xwang378/2025/lmms-eval
export HF_HOME=/scratch/xwang378/hf_cache HUGGINGFACE_HUB_CACHE=/scratch/xwang378/hf_cache/hub
export HF_DATASETS_CACHE=/scratch/xwang378/hf_cache/datasets XMODBENCH=/home/xwang378/scratch/2025/AudioBench_data
export NUMBA_CACHE_DIR=/tmp/numba_$SLURM_JOB_ID PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
CFG=(a2t a2v t2a t2v v2a v2t)
C=${CFG[$SLURM_ARRAY_TASK_ID]}
/home/xwang378/.conda/envs/qwenomni3/bin/python -m lmms_eval --model video_salmonn_2 \
  --model_args pretrained=tsinghua-ee/video-SALMONN-2_plus_72B,device_map=auto \
  --tasks xmod_bench_lite_$C --batch_size 1 --log_samples \
  --output_path logs/xmod_bench_lite/results_video_salmonn_2_72B
echo "VS72_LITE_${C}_DONE"
