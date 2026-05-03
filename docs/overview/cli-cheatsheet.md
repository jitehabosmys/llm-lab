# 常用命令行速查表

这份文档整理当前项目里最常用的命令行，分成两类：

1. 通用 Linux / 云服务器操作
2. 当前项目里的训练、推理、评测、DPO、监控命令

目标不是替代详细流程文档，而是提供一个“随手可查”的速查表。

相关文档：

- [project-overview.md](/hy-tmp/llm-lab/docs/overview/project-overview.md)
- [infra-and-troubleshooting.md](/hy-tmp/llm-lab/docs/overview/infra-and-troubleshooting.md)

## 1. 通用 Linux / 服务器命令

### 登录与基础检查

```bash
# 通过 SSH 登录远程机器
ssh -p <端口> root@<主机>

# 查看当前登录用户
whoami

# 查看系统 / 内核信息
uname -a

# 查看 GPU、驱动、显存占用
nvidia-smi

# 查看磁盘挂载与剩余空间
df -h

# 查看内存与 swap 使用
free -h
```

### 目录与文件

```bash
# 查看当前所在目录
pwd

# 详细列出当前目录内容（含隐藏文件）
ls -la

# 查找两层目录内的文件并排序，适合快速浏览结构
find . -maxdepth 2 -type f | sort

# 查看 /hy-tmp 下各目录占用大小，并按大小排序
du -sh /hy-tmp/* 2>/dev/null | sort -h
```

### GPU 监控

```bash
# 一次性查看 GPU 状态
nvidia-smi

# 每秒刷新一次完整 GPU 状态
watch -n 1 nvidia-smi

# 只看最关键的 GPU 指标：利用率、显存、功耗
watch -n 1 'nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader,nounits'

# 只看当前哪些进程在占 GPU 显存
watch -n 1 'nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader'
```

### tmux

```bash
# 新建一个名为 train 的 tmux 会话
tmux new -s train

# 重新连接到 train 会话
tmux attach -t train

# 列出当前所有 tmux 会话
tmux ls
```

### Git

```bash
# 简洁查看工作区变更
git status --short

# 查看各文件改动规模统计
git diff --stat

# 把某个文件加入暂存区
git add <file>

# 提交当前暂存区
git commit -m "feat(scope): message"

# 查看远程仓库地址
git remote -v
```

---

## 2. 项目路径约定

当前项目里最常用的几个目录：

```bash
/hy-tmp/llm-lab
/hy-tmp/LLaMA-Factory
/hy-tmp/models
/hy-tmp/outputs
/hy-tmp/logs
```

两个主要 Python 环境：

```bash
/hy-tmp/llm-lab/.venv
/hy-tmp/LLaMA-Factory/.venv
```

---

## 3. 环境与依赖

### 激活 `llm-lab` 环境

```bash
# 进入项目仓库
cd /hy-tmp/llm-lab

# 激活项目自己的 Python 虚拟环境
source .venv/bin/activate
```

### 激活 `LLaMA-Factory` 环境

```bash
# 进入 LLaMA-Factory 仓库
cd /hy-tmp/LLaMA-Factory

# 激活 LLaMA-Factory 自己的 Python 虚拟环境
source .venv/bin/activate
```

### 安装 / 同步依赖

```bash
# 根据 pyproject.toml / uv.lock 同步 llm-lab 环境
cd /hy-tmp/llm-lab
uv sync
```

```bash
# 在 LLaMA-Factory 环境里安装本体和 metrics 依赖
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
pip install -e .
pip install -r requirements/metrics.txt
```

### 检查关键包

```bash
# 确认 llm-lab 环境里的 openai / anthropic 包可用
cd /hy-tmp/llm-lab
source .venv/bin/activate
python -c "import openai, anthropic; print('ok')"
```

```bash
# 确认训练环境里的 torch / transformers / peft 正常
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
python -c "import torch, transformers, peft; print(torch.__version__)"
llamafactory-cli version
```

---

## 4. 训练命令

### 0.5B full SFT

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train /hy-tmp/llm-lab/configs/llamafactory/5060ti_qwen25_05b_full_lora_sft.yaml
```

### 3B full strict SFT

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train /hy-tmp/llm-lab/configs/llamafactory/5090ti_qwen25_3b_full_lora_sft_strict_json_prompt.yaml
```

### 4B full strict SFT

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train /hy-tmp/llm-lab/configs/llamafactory/5090ti_qwen3_4b_full_lora_sft_strict_json_prompt.yaml
```

### 8B smoke / full QLoRA

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
  /hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_8b_smoke_qlora_sft_strict_json_prompt.yaml \
  model_name_or_path=/hy-tmp/models/Qwen/Qwen3-8B
```

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
  /hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_8b_full_qlora_sft_strict_json_prompt.yaml \
  model_name_or_path=/hy-tmp/models/Qwen/Qwen3-8B
```

### 8B throughput 优化版

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
  /hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_8b_full_qlora_sft_strict_json_prompt_bs2.yaml \
  model_name_or_path=/hy-tmp/models/Qwen/Qwen3-8B
```

### 14B smoke / full QLoRA

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
  /hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_14b_smoke_qlora_sft_strict_json_prompt.yaml \
  model_name_or_path=/hy-tmp/models/Qwen/Qwen3-14B
```

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
  /hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_14b_full_qlora_sft_strict_json_prompt.yaml \
  model_name_or_path=/hy-tmp/models/Qwen/Qwen3-14B
```

---

## 5. HF 自动评测

### 4B strict SFT 小样本 / 全量

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
python /hy-tmp/llm-lab/scripts/run_inference_eval.py --matrix qwen3_4b_strict_json_prompt --max-samples 10
```

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
python /hy-tmp/llm-lab/scripts/run_inference_eval.py --matrix qwen3_4b_strict_json_prompt --max-samples 48
```

### 8B strict（显式 variant）

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
python /hy-tmp/llm-lab/scripts/run_inference_eval.py \
  --eval-data /hy-tmp/llm-lab/data/llamafactory/diagnosis_sft_strict_json_prompt_eval_alpaca.json \
  --variant qwen3_8b_strict_json_prompt_base=/hy-tmp/llm-lab/configs/llamafactory/qwen3_8b_base_hf_infer_strict_json_prompt.yaml \
  --variant qwen3_8b_strict_json_prompt_lora=/hy-tmp/llm-lab/configs/llamafactory/qwen3_8b_full_qlora_hf_infer_strict_json_prompt.yaml \
  --max-samples 48
```

### 4B / 8B DPO 后评测

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
python /hy-tmp/llm-lab/scripts/run_inference_eval.py \
  --eval-data /hy-tmp/llm-lab/data/llamafactory/diagnosis_sft_strict_json_prompt_eval_alpaca.json \
  --variant qwen3_4b_strict_json_prompt_sft=/hy-tmp/llm-lab/configs/llamafactory/qwen3_4b_full_lora_hf_infer_strict_json_prompt.yaml \
  --variant qwen3_4b_strict_json_prompt_dpo=/hy-tmp/llm-lab/configs/llamafactory/qwen3_4b_lora_dpo_hf_infer_strict_json_prompt.yaml \
  --max-samples 48
```

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
python /hy-tmp/llm-lab/scripts/run_inference_eval.py \
  --eval-data /hy-tmp/llm-lab/data/llamafactory/diagnosis_sft_strict_json_prompt_eval_alpaca.json \
  --variant qwen3_8b_strict_json_prompt_sft=/hy-tmp/llm-lab/configs/llamafactory/qwen3_8b_full_qlora_hf_infer_strict_json_prompt.yaml \
  --variant qwen3_8b_strict_json_prompt_dpo=/hy-tmp/llm-lab/configs/llamafactory/qwen3_8b_qlora_dpo_hf_infer_strict_json_prompt.yaml \
  --max-samples 48
```

---

## 6. Pairwise judge

### 4B SFT vs 4B DPO

```bash
cd /hy-tmp/llm-lab
source .venv/bin/activate
python scripts/run_pairwise_judge.py \
  --candidate-a /hy-tmp/outputs/llm-lab-inference-eval/20260502_194100/qwen3_4b_strict_json_prompt_sft_results.jsonl \
  --candidate-b /hy-tmp/outputs/llm-lab-inference-eval/20260502_194100/qwen3_4b_strict_json_prompt_dpo_results.jsonl \
  --label-a qwen3_4b_strict_json_prompt_sft \
  --label-b qwen3_4b_strict_json_prompt_dpo \
  --concurrency 4 \
  --use-reference
```

### 8B SFT vs 8B DPO

```bash
cd /hy-tmp/llm-lab
source .venv/bin/activate
python scripts/run_pairwise_judge.py \
  --candidate-a /hy-tmp/outputs/llm-lab-inference-eval/20260502_195624/qwen3_8b_strict_json_prompt_sft_results.jsonl \
  --candidate-b /hy-tmp/outputs/llm-lab-inference-eval/20260502_195624/qwen3_8b_strict_json_prompt_dpo_results.jsonl \
  --label-a qwen3_8b_strict_json_prompt_sft \
  --label-b qwen3_8b_strict_json_prompt_dpo \
  --concurrency 4 \
  --use-reference
```

### 4B SFT / DPO vs 8B base

```bash
cd /hy-tmp/llm-lab
source .venv/bin/activate
python scripts/run_pairwise_judge.py \
  --candidate-a /hy-tmp/outputs/llm-lab-inference-eval/20260502_194100/qwen3_4b_strict_json_prompt_sft_results.jsonl \
  --candidate-b /hy-tmp/outputs/llm-lab-inference-eval/20260501_225714/qwen3_8b_strict_json_prompt_base_results.jsonl \
  --label-a qwen3_4b_strict_json_prompt_sft \
  --label-b qwen3_8b_strict_json_prompt_base \
  --concurrency 4 \
  --use-reference
```

```bash
cd /hy-tmp/llm-lab
source .venv/bin/activate
python scripts/run_pairwise_judge.py \
  --candidate-a /hy-tmp/outputs/llm-lab-inference-eval/20260502_194100/qwen3_4b_strict_json_prompt_dpo_results.jsonl \
  --candidate-b /hy-tmp/outputs/llm-lab-inference-eval/20260501_225714/qwen3_8b_strict_json_prompt_base_results.jsonl \
  --label-a qwen3_4b_strict_json_prompt_dpo \
  --label-b qwen3_8b_strict_json_prompt_base \
  --concurrency 4 \
  --use-reference
```

---

## 7. DPO 数据生成与整理

### 候选生成 + judge

```bash
cd /hy-tmp/llm-lab
source .venv/bin/activate
python scripts/generate_dpo_candidates.py \
  --input-data /hy-tmp/llm-lab/data/llamafactory/diagnosis_sft_strict_json_prompt_train_alpaca.json \
  --output-dir /hy-tmp/llm-lab/data/dpo/generated_pairs_smoke \
  --max-samples 20 \
  --sample-concurrency 2 \
  --flush-every 10 \
  --temperature 0.2 \
  --max-output-tokens 700 \
  --use-reference
```

### 合并多批次 DPO 结果

```bash
cd /hy-tmp/llm-lab
source .venv/bin/activate
python scripts/merge_dpo_generation_outputs.py \
  --input-dirs \
    /hy-tmp/llm-lab/data/dpo/generated_pairs_smoke \
    /hy-tmp/llm-lab/data/dpo/generated_pairs_ds_dsp_99 \
    /hy-tmp/llm-lab/data/dpo/generated_pairs_ds_dsp_100 \
    /hy-tmp/llm-lab/data/dpo/generated_pairs_ds_dsp_200 \
    /hy-tmp/llm-lab/data/dpo/generated_pairs_ds_dsp_250 \
  --output-dir /hy-tmp/llm-lab/data/dpo/merged_ds_dsp_max2 \
  --prefer-latest \
  --max-per-sample-id 2
```

### 从 judge 结果导出正式 DPO 数据

```bash
cd /hy-tmp/llm-lab
source .venv/bin/activate
python scripts/build_dpo_dataset_from_judged_pairs.py \
  --input-file /hy-tmp/llm-lab/data/dpo/merged_ds_dsp_max2/judge_results.jsonl \
  --output-dir /hy-tmp/llm-lab/data/dpo/final_ds_dsp \
  --max-per-sample-id 2
```

---

## 8. DPO 训练

### 4B DPO（high only）

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
  /hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_4b_lora_dpo_strict_json_prompt.yaml \
  2>&1 | tee /hy-tmp/logs/qwen3-4b-lora-dpo-strict-json-prompt-4090.log
```

### 8B DPO（high only）

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
  /hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_8b_qlora_dpo_strict_json_prompt.yaml \
  2>&1 | tee /hy-tmp/logs/qwen3-8b-qlora-dpo-strict-json-prompt-4090.log
```

### 4B / 8B DPO（high + medium）

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
  /hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_4b_lora_dpo_strict_json_prompt_highplusmedium.yaml
```

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 llamafactory-cli train \
  /hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_8b_qlora_dpo_strict_json_prompt_highplusmedium.yaml
```

---

## 9. 14B 相关

### 14B strict base HF 小样本探针

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
python /hy-tmp/llm-lab/scripts/run_inference_eval.py \
  --eval-data /hy-tmp/llm-lab/data/llamafactory/diagnosis_sft_strict_json_prompt_eval_alpaca.json \
  --variant qwen3_14b_strict_json_prompt_base=/hy-tmp/llm-lab/configs/llamafactory/qwen3_14b_base_hf_infer_strict_json_prompt.yaml \
  --max-samples 10
```

### 14B lora 单卡强制推理尝试（当前主要用于排障）

```bash
cd /hy-tmp/LLaMA-Factory
source .venv/bin/activate
export LLAMAFACTORY_INFER_SINGLE_CUDA=1
python /hy-tmp/llm-lab/scripts/run_inference_eval.py \
  --eval-data /hy-tmp/llm-lab/data/llamafactory/diagnosis_sft_strict_json_prompt_eval_alpaca.json \
  --variant qwen3_14b_strict_json_prompt_lora=/hy-tmp/llm-lab/configs/llamafactory/qwen3_14b_full_qlora_hf_infer_strict_json_prompt.yaml \
  --max-samples 1
```

---

## 10. 实用提醒

### 1. 大模型评测前先看显存

```bash
# 持续观察 GPU 利用率、显存和功耗，适合训练或推理时开一个单独终端盯着看
cd /hy-tmp/llm-lab
watch -n 1 'nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader,nounits'
```

### 2. 检查磁盘空间

```bash
# 查看 /hy-tmp 总体剩余空间
cd /hy-tmp/llm-lab
df -h /hy-tmp

# 看 /hy-tmp 下各目录谁最占空间
du -sh /hy-tmp/* 2>/dev/null | sort -h
```

### 3. 检查模型目录是否完整

```bash
# 看 8B 模型目录总大小
cd /hy-tmp/llm-lab
du -sh /hy-tmp/models/Qwen/Qwen3-8B

# 列出 8B 模型目录里的关键文件，确认分片 / tokenizer / config 是否齐全
find /hy-tmp/models/Qwen/Qwen3-8B -maxdepth 1 -type f | sort
```

```bash
# 看 14B 模型目录总大小
cd /hy-tmp/llm-lab
du -sh /hy-tmp/models/Qwen/Qwen3-14B

# 列出 14B 模型目录里的关键文件，确认是否完整下载
find /hy-tmp/models/Qwen/Qwen3-14B -maxdepth 1 -type f | sort
```

## 11. 一句话总结

如果只记一条：

**当前项目最常用的命令，基本都围绕四件事：训练、HF 自动评测、pairwise judge、DPO 数据与训练。**
