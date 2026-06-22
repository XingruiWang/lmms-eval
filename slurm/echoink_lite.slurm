#!/bin/bash
#SBATCH --job-name=echo_lite
#SBATCH --gres=gpu:6000_ada:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=6:00:00
#SBATCH --output=/scratch/xwang378/2025/lmms-eval/logs/echoink_lite_%A_%a.log
#SBATCH --array=0-5
cd /scratch/xwang378/2025/lmms-eval
export HF_HOME=/scratch/xwang378/hf_cache HUGGINGFACE_HUB_CACHE=/scratch/xwang378/hf_cache/hub
export HF_DATASETS_CACHE=/scratch/xwang378/hf_cache/datasets XMODBENCH=/home/xwang378/scratch/2025/AudioBench_data
export NUMBA_CACHE_DIR=/tmp/numba_$SLURM_JOB_ID PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
CFG=(a2t a2v t2a t2v v2a v2t)
C=${CFG[$SLURM_ARRAY_TASK_ID]}
/home/xwang378/.conda/envs/qwenomni3/bin/python -m lmms_eval --model echoink_interleave \
  --model_args pretrained=harryhsing/EchoInk-R1-7B \
  --tasks xmod_bench_lite_$C --batch_size 1 --log_samples \
  --output_path logs/xmod_bench_lite/results_echoink_interleave
echo "ECHOINK_LITE_${C}_DONE"
