#!/bin/bash
#SBATCH --job-name=bai_video
#SBATCH --gres=gpu:6000_ada:4
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=10:00:00
#SBATCH --output=/scratch/xwang378/2025/lmms-eval/logs/bai_video_%A_%a.log
#SBATCH --array=0-1
# 0 = audio_video, 1 = text_video — the two combos with 4 video options where
# Baichuan OOM'd at default max_num_frames=32 × 4 videos = 128 frames on a single
# 48 GB card (550+544 empty in 152449 run). Multi-GPU device_map=auto splits
# the model so vision-heavy items fit.
cd /scratch/xwang378/2025/lmms-eval
export HF_HOME=/scratch/xwang378/hf_cache HUGGINGFACE_HUB_CACHE=/scratch/xwang378/hf_cache/hub
export HF_DATASETS_CACHE=/scratch/xwang378/hf_cache/datasets XMODBENCH=/home/xwang378/scratch/2025/AudioBench_data
export NUMBA_CACHE_DIR=/tmp/numba_$SLURM_JOB_ID PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_HOME=/scratch/xwang378/envs/baichuan
COMBOS=(audio_video text_video)
C=${COMBOS[$SLURM_ARRAY_TASK_ID]}
/scratch/xwang378/envs/baichuan/bin/python -m lmms_eval --model baichuan_omni_interleave \
  --model_args pretrained=baichuan-inc/Baichuan-Omni-1d5,device_map=auto \
  --tasks xmod_bench_$C --batch_size 1 --log_samples \
  --output_path logs/xmod_bench_full/results_baichuan_omni_interleave
echo "BAICHUAN_VIDEO_${C}_DONE"
