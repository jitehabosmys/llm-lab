# qwen-diagnosis-alignment

`qwen-diagnosis-alignment` 是一个围绕中文“训练 / 部署问题诊断助手”的数据构建、监督微调与偏好优化实验项目。

项目目标是回答以下问题：

- 如何为一个强结构化工程诊断任务构造高质量训练数据
- 在单卡资源约束下，模型继续 scale up 到什么位置仍值得
- `DPO` 在当前任务里是否能带来额外收益
- 推理基础设施在更大模型上会遇到哪些现实边界

## 项目内容

当前仓库已经包含：

- `SFT` 数据构建与清洗脚本
- `LLaMA-Factory` 可直接使用的数据视图
- `0.5B / 3B / 4B / 8B / 14B` 多轮训练记录
- `HF` 自动规则评测与 `LLM-as-a-judge` 工作流
- 第一版 `DPO` 数据生成、合并、筛选与训练流程
- 较完整的实验文档、排障文档与总结文档

## 核心任务

输入通常包含：

- 用户问题
- 环境信息
- 命令
- 报错日志

输出为一个严格结构化 JSON，核心字段包括：

- `category`
- `severity`
- `summary`
- `root_cause`
- `missing_info`
- `next_steps`


## 主要结果

到当前阶段，项目已经得到的结论：

### 1. 模型规模继续扩大是有收益的

从早期 `0.5B / 3B / 4B` 到后续 `8B / 14B`，训练与评测都显示：

- `3B` 明显优于 `0.5B`
- `4B strict` 明显优于 `3B strict`
- `8B QLoRA` 在训练信号和 judge 上继续优于 `4B`
- `14B QLoRA` 在训练信号上进一步优于 `8B`

### 2. `8B` 是单卡 `4090` 条件下最平衡的主实验位

在单卡 `4090` 条件下：

- `8B` 训练稳定
- 评测链路完整
- 推理仍然可控
- 相比 `4B` 有清晰增益


### 3. `14B` 是训练甜点位上沿候选

`14B` 在训练上表现出明显更强的信号，但在推理与评测阶段开始明显碰到：

- `HF + PEFT` 推理装载问题
- 单卡显存边界
- `vLLM` 与当前 CUDA / 模型配置的兼容窗口问题

因此它更像一个训练甜点位上沿候选，而不是当前这套基础设施上可无缝接管主线的稳定推理位。

### 4. DPO 可行，但收益有限且更依赖数据工程

当前 DPO 实验说明：

- `4B` 和 `8B` 都能从偏好数据中学到有效信号
- `4B` 更像被明显拉升
- `8B` 更像在强基线上被进一步精修

但整体看，DPO 的收益比 SFT 更依赖：

- pair 质量
- 偏好目标是否清晰
- judge 是否稳定

当前主要瓶颈已经从“训练能不能跑”转向“偏好数据工程是否足够好”。

## 目录结构

### 数据

- `data/sft_train_final.jsonl`
- `data/sft_train_final.json`
- `data/llamafactory/`
- `data/dpo/`

### 配置

- `configs/llamafactory/`

### 脚本

- `scripts/`

### 文档

- `docs/5060ti/`
- `docs/4090/`
- `docs/overview/`

## 文档入口

如果想快速了解项目，建议按下面顺序读：

### 第一层：快速总览

- [项目总览](docs/overview/project-overview.md)
- [关键结论](docs/overview/key-findings.md)
- [模型结果速查表](docs/overview/model-results-cheatsheet.md)

### 第二层：阶段索引

- [5060Ti 阶段索引](docs/5060ti/README.md)
- [4090 阶段索引](docs/4090/README.md)

### 第三层：专题说明

- [数据获取与合成 Pipeline](docs/overview/data-pipeline.md)
- [基础设施与 Troubleshooting](docs/overview/infra-and-troubleshooting.md)
- [常用命令行速查表](docs/overview/cli-cheatsheet.md)
- [LoRA 与 QLoRA 说明](docs/overview/lora-qlora-explained.md)
- [训练与推理配置参数说明](docs/overview/config-rationale.md)

## Acknowledgements

本项目的训练与评测流程建立在开源 `LLaMA-Factory` 框架之上；模型微调则大量依赖 `LoRA / QLoRA` 这类参数高效微调方法。


