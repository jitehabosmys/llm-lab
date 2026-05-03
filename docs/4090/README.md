# 4090 阶段索引

这一阶段对应项目进入更大模型与更高质量实验的正式主线，重点是：

1. 在 `4090` 上稳定复现 `4B strict` baseline
2. 用 `8B QLoRA` 验证更大模型是否继续带来收益
3. 用 `14B QLoRA` 探查单卡训练甜点位的上沿
4. 试探 `DPO` 是否能在当前任务上带来进一步收益

## 核心结论

- `4B strict` 在 4090 上已经稳定复现，足以作为正式 baseline
- `8B QLoRA` 在训练、评测、judge 上都表现出正向收益
- `14B QLoRA` 在训练信号上明显更强，但推理与评测开始碰到基础设施边界
- `DPO` 在当前任务上可行，但收益有限且对数据质量高度敏感
- `4B` 与 `8B` 的 DPO 都有效，但增益形态不同：
  - `4B` 更像被明显拉升
  - `8B` 更像被进一步精修

## 建议阅读顺序

### 1. 环境与阶段切换

- [gpushare-4090-first-setup-checklist.md](/hy-tmp/llm-lab/docs/4090/gpushare-4090-first-setup-checklist.md)

### 2. 4B baseline

- [2026-05-01-qwen3-4b-strict-repro-on-4090.md](/hy-tmp/llm-lab/docs/4090/2026-05-01-qwen3-4b-strict-repro-on-4090.md)

### 3. 8B 主实验线

- [2026-05-01-qwen3-8b-qlora-sft-log.md](/hy-tmp/llm-lab/docs/4090/2026-05-01-qwen3-8b-qlora-sft-log.md)
- [2026-05-01-qwen3-8b-qlora-throughput-tuning.md](/hy-tmp/llm-lab/docs/4090/2026-05-01-qwen3-8b-qlora-throughput-tuning.md)

### 4. 14B 上沿探索

- [2026-05-02-qwen3-14b-qlora-sft-log.md](/hy-tmp/llm-lab/docs/4090/2026-05-02-qwen3-14b-qlora-sft-log.md)

### 5. DPO 数据与训练

- [2026-05-02-dpo-candidate-generation-smoke.md](/hy-tmp/llm-lab/docs/4090/2026-05-02-dpo-candidate-generation-smoke.md)
- [2026-05-02-final-dpo-dataset.md](/hy-tmp/llm-lab/docs/4090/2026-05-02-final-dpo-dataset.md)
- [2026-05-02-4b-8b-dpo-training-log.md](/hy-tmp/llm-lab/docs/4090/2026-05-02-4b-8b-dpo-training-log.md)
- [2026-05-02-dpo-stage-summary.md](/hy-tmp/llm-lab/docs/4090/2026-05-02-dpo-stage-summary.md)

### 6. 关键亮点与额外对照

- [2026-05-02-4b-vs-8b-base-alignment-gap.md](/hy-tmp/llm-lab/docs/4090/2026-05-02-4b-vs-8b-base-alignment-gap.md)

## 这一阶段的项目定位

如果只保留一句话：

**4090 阶段的价值在于证明 8B 是当前最平衡的主实验位、14B 是训练甜点位上沿候选，而 DPO 已被验证可行但主要瓶颈开始转向偏好数据工程。**
