# 5060Ti 阶段索引

这一阶段对应项目的早期探索与流程打通，重点不是训出最终最强模型，而是：

1. 跑通数据构建、SFT、评测、judge、DPO 候选采集全链路
2. 验证 `strict_json_prompt` 是否值得成为正式主线
3. 判断从 `0.5B` 往 `3B / 4B` scale up 是否有收益

## 核心结论

- `0.5B` 是流程验证模型，不是后续主实验主力
- `3B` 明显优于 `0.5B`
- `4B strict lora` 明显优于 `3B strict lora`
- `strict_json_prompt` 已经收束成正式协议主线
- `vLLM` 在这一阶段主要还是候选基础设施，不是正式主评测链

## 建议阅读顺序

### 1. 阶段总览

- [2026-05-01-project-status-before-4090.md](/hy-tmp/llm-lab/docs/5060ti/2026-05-01-project-status-before-4090.md)
- [2026-04-30-next-phase-plan.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-30-next-phase-plan.md)

### 2. 数据与 prompt 设计

- [data-construction-log.md](/hy-tmp/llm-lab/docs/5060ti/data-construction-log.md)
- [2026-04-30-why-strict-prompt.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-30-why-strict-prompt.md)
- [2026-04-30-strict-prompt-observations.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-30-strict-prompt-observations.md)

### 3. 训练记录

- [2026-04-29-qwen25-05b-full-lora-sft-log.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-29-qwen25-05b-full-lora-sft-log.md)
- [2026-04-30-qwen25-3b-sft-log.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-30-qwen25-3b-sft-log.md)
- [2026-04-30-qwen3-4b-sft-log.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-30-qwen3-4b-sft-log.md)

### 4. 自动评测与 judge

- [inference-eval-workflow.md](/hy-tmp/llm-lab/docs/5060ti/inference-eval-workflow.md)
- [pairwise-judge-workflow.md](/hy-tmp/llm-lab/docs/5060ti/pairwise-judge-workflow.md)
- [2026-04-29-inference-eval-results.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-29-inference-eval-results.md)
- [2026-04-29-inference-failure-analysis.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-29-inference-failure-analysis.md)
- [2026-04-29-pairwise-judge-results.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-29-pairwise-judge-results.md)
- [2026-04-30-qwen25-05b-vs-3b-pairwise-results.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-30-qwen25-05b-vs-3b-pairwise-results.md)
- [2026-05-01-qwen25-3b-vs-qwen3-4b-strict-pairwise-results.md](/hy-tmp/llm-lab/docs/5060ti/2026-05-01-qwen25-3b-vs-qwen3-4b-strict-pairwise-results.md)

### 5. 推理基础设施与运维

- [gpu-strategy-5060ti-vs-4090.md](/hy-tmp/llm-lab/docs/5060ti/gpu-strategy-5060ti-vs-4090.md)
- [gpushare-training-workflow.md](/hy-tmp/llm-lab/docs/5060ti/gpushare-training-workflow.md)
- [gpushare-5060ti-sft-playbook.md](/hy-tmp/llm-lab/docs/5060ti/gpushare-5060ti-sft-playbook.md)
- [2026-05-01-vllm-smoke-plan.md](/hy-tmp/llm-lab/docs/5060ti/2026-05-01-vllm-smoke-plan.md)
- [2026-05-01-hf-vs-vllm-observations.md](/hy-tmp/llm-lab/docs/5060ti/2026-05-01-hf-vs-vllm-observations.md)
- [2026-05-01-hf-vs-vllm-compare.md](/hy-tmp/llm-lab/docs/5060ti/2026-05-01-hf-vs-vllm-compare.md)
- [2026-04-29-troubleshooting.md](/hy-tmp/llm-lab/docs/5060ti/2026-04-29-troubleshooting.md)

## 这一阶段的项目定位

如果只保留一句话：

**5060Ti 阶段的价值在于把整个实验闭环跑通，并明确 strict 主线成立、3B/4B scale up 值得继续。**
