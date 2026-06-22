#!/bin/bash
#SBATCH --job-name=gem3_lite
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --output=/scratch/xwang378/2025/lmms-eval/logs/gem3_lite_%A_%a.log
#SBATCH --array=0-7
# 0=3.1-pro a2v  1=3.1-pro t2a  2=3.1-pro t2v  3=3.1-pro v2a  4=3.1-pro v2t
# 5=3.5-flash t2v  6=3.5-flash v2a  7=3.5-flash v2t
cd /scratch/xwang378/2025/lmms-eval
export GOOGLE_API_KEY=$(grep -oE 'Google_API_Key_1=.*' /home/xwang378/scratch/2025/AudioBench/.envs | cut -d= -f2- | tr -d ' "')
export XMODBENCH=/home/xwang378/scratch/2025/AudioBench_data
MODELS=(gemini-3.1-pro-preview gemini-3.1-pro-preview gemini-3.1-pro-preview gemini-3.1-pro-preview gemini-3.1-pro-preview \
        gemini-3.5-flash gemini-3.5-flash gemini-3.5-flash)
CFGS=(a2v t2a t2v v2a v2t \
      t2v v2a v2t)
MV=${MODELS[$SLURM_ARRAY_TASK_ID]}
C=${CFGS[$SLURM_ARRAY_TASK_ID]}
TAG=$(echo "$MV" | tr './' '__')
/home/xwang378/.conda/envs/qwenomni3/bin/python -m lmms_eval --model gemini_genai_api \
  --model_args model_version=$MV,interleave=True \
  --tasks xmod_bench_lite_$C --batch_size 1 --log_samples \
  --output_path logs/xmod_bench_lite/results_gemini_genai_api_$TAG
echo "GEM3_LITE_${MV}_${C}_DONE"
