#!/bin/bash
#SBATCH --job-name=gemma4_full
#SBATCH --gres=gpu:6000_ada:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=10:00:00
#SBATCH --output=/scratch/xwang378/2025/lmms-eval/logs/gemma4_full_%A_%a.log
#SBATCH --array=0-9
cd /scratch/xwang378/2025/lmms-eval
export HF_HOME=/scratch/xwang378/hf_cache HUGGINGFACE_HUB_CACHE=/scratch/xwang378/hf_cache/hub
export HF_DATASETS_CACHE=/scratch/xwang378/hf_cache/datasets XMODBENCH=/home/xwang378/scratch/2025/AudioBench_data
export NUMBA_CACHE_DIR=/tmp/numba_$SLURM_JOB_ID PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
COMBOS=(audio_text audio_image audio_video text_audio text_image text_video image_audio image_text video_audio video_text)
C=${COMBOS[$SLURM_ARRAY_TASK_ID]}
/home/xwang378/.conda/envs/gemma4/bin/python -m lmms_eval --model gemma4_interleave \
  --model_args pretrained=google/gemma-4-E4B-it \
  --tasks xmod_bench_$C --batch_size 1 --log_samples \
  --output_path logs/xmod_bench_full/results_gemma4_interleave
echo "GEMMA4_FULL_${C}_DONE"
