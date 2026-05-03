# 模型核心结果速查表

这份文档只保留各个关键模型最值得记住的信息：

1. 训练核心指标
2. 自动规则评测的代表性结果
3. 该模型在当前任务上最突出的行为特征

它不是完整实验日志的替代，而是一个便于快速回顾的“结果索引”。

## 1. Qwen2.5-0.5B-Instruct + LoRA

阶段定位：

- 流程验证模型

训练结果：

- `train_loss = 2.1676`
- `eval_loss = 1.9353`
- `train_runtime = 0:06:52`

关键行为：

- 在 base 状态下，默认 prompt 路线的 JSON 输出能力很弱
- 它的价值主要在于：
  - 证明数据可训
  - 证明 SFT / 评测 / judge / DPO 候选采集全链可跑

一句话：

- **0.5B 证明了流程能跑，但不是后续值得继续投入的主实验模型。**

## 2. Qwen2.5-3B-Instruct + LoRA

阶段定位：

- 从流程验证走向正式主实验候选的第一跳

训练结果：

- smoke:
  - `train_loss = 1.7067`
  - `eval_loss = 1.6775`
- full:
  - `train_loss = 1.9460`
  - `eval_loss = 1.6482`
  - `train_runtime ≈ 9m53s`

自动规则评测（默认 prompt）：

- `3B base`
  - `json_parse_success = 43 / 48 = 89.58%`
  - `schema_valid = 0 / 48`
- `3B lora`
  - `json_parse_success = 47 / 48 = 97.92%`
  - `schema_valid = 47 / 48 = 97.92%`
  - `category_matches_reference = 74.47%`
  - `severity_matches_reference = 65.96%`

关键行为：

- 3B base 已经开始表现出较强的“看起来像 JSON”的能力
- 但要稳定命中目标 schema，仍然依赖 LoRA 对齐
- 相比 0.5B，3B 在当前任务上已经不是一个量级

一句话：

- **3B 是第一个明确说明 scale up 有意义的模型档位。**

## 3. Qwen3-4B-Instruct-2507 + strict LoRA

阶段定位：

- 5060Ti 阶段的最强正式 baseline
- 4090 阶段的稳定复现基线

训练结果（4090 复现版）：

- smoke:
  - `train_loss = 1.4019`
  - `eval_loss = 1.5081`
- full:
  - `train_loss = 1.7212`
  - `eval_loss = 1.4024`
  - `train_runtime = 0:06:49`

自动规则评测（strict）：

- `4B base`
  - `json_parse_success = 48 / 48`
  - `schema_valid = 1 / 48 = 2.08%`
- `4B strict lora`
  - `json_parse_success = 48 / 48`
  - `schema_valid = 48 / 48`
  - `category_matches_reference = 77.08%`
  - `severity_matches_reference = 64.58%`

关键行为：

- base 已经能生成可解析 JSON，但不会稳定 obey schema
- strict lora 后：
  - 结构完全稳定
  - 输出更短
  - 推理更快

一句话：

- **4B strict lora 是当前项目里第一个“结构稳定、内容也够强”的正式 baseline。**

## 4. Qwen3-8B + strict QLoRA

阶段定位：

- 当前训练、评测、judge、成本之间最平衡的主实验位

训练结果：

- smoke:
  - `train_loss = 1.4574`
  - `eval_loss = 1.4259`
- full:
  - `train_loss = 1.7031`
  - `eval_loss = 1.3887`
  - `train_runtime = 0:09:15`

吞吐优化版（`bs=2 / grad_acc=16`）：

- `train_loss = 1.7034`
- `eval_loss = 1.3890`
- `train_runtime = 0:06:06`

自动规则评测（strict, no-think 正确关闭后）：

- `8B base`
  - `json_parse_success = 48 / 48`
  - `schema_valid = 48 / 48`
  - `category_matches_reference = 41.67%`
  - `severity_matches_reference = 58.33%`
- `8B qlora`
  - `json_parse_success = 47 / 48`
  - `schema_valid = 47 / 48`
  - `category_matches_reference = 70.21%`
  - `severity_matches_reference = 63.83%`

关键行为：

- 如果没有真正关闭 thinking，8B base 会统一泄露 `<think>`，导致 strict 评测被污染
- 正确使用：
  - `template: qwen3`
  - `enable_thinking: false`
  之后，8B base 的结构遵循能力其实很强
- 8B qlora 相比 4B strict lora 在内容质量上保持稳健领先，但领先幅度已开始收缩

一句话：

- **8B 是当前项目里最像“主实验位”的模型：有收益、能跑通、还能完整评测。**

## 5. Qwen3-14B + strict QLoRA

阶段定位：

- 当前资源约束下的训练甜点位上沿候选

训练结果：

- smoke:
  - `train_loss = 1.1824`
  - `eval_loss = 1.4863`
  - `train_runtime = 0:06:33`
- full:
  - `train_loss = 1.5571`
  - `eval_loss = 1.2974`
  - `train_runtime = 0:11:28`

关键行为：

- 训练层面：
  - 14B 可以在单卡 4090 上稳定 QLoRA
  - full 训练信号明显优于 8B
- 推理层面：
  - HF + PEFT + auto device map 遇到装载层 bug
  - 强制单卡 `cuda:0` 后，base model 加载阶段就开始逼近显存边界
  - 旧版 vLLM 与新版 Qwen3 config 又存在兼容问题

一句话：

- **14B 训练很强，但在当前这套单卡 HF/vLLM 推理栈上已经明显碰到基础设施边界。**

## 6. 4B DPO

阶段定位：

- 用于验证小模型是否更容易从偏好数据中获得明显收益

训练结果（high only）：

- `train_loss = 0.8568`
- `train_runtime = 0:03:19`

自动规则评测（SFT vs DPO）：

- `schema_valid`
  - SFT: `48 / 48`
  - DPO: `48 / 48`
- `category_matches_reference`
  - SFT: `77.08%`
  - DPO: `77.08%`
- `severity_matches_reference`
  - SFT: `64.58%`
  - DPO: `62.50%`

pairwise judge（SFT vs DPO）：

- `DPO wins = 18`
- `SFT wins = 6`
- `tie = 24`
- 去掉 tie 后：
  - `DPO win rate = 75%`
- `overall score delta = +0.1875`

关键行为：

- 自动规则评测几乎看不出提升
- 但 judge 明确认为 DPO 后版本在：
  - actionability
  - missing_info_quality
  - overall engineering quality
  上更强
- 4B 对当前 DPO 数据的训练响应最明显

一句话：

- **4B DPO 说明：小模型更容易被当前偏好数据“明显拉升”。**

## 7. 8B DPO

阶段定位：

- 验证更强基线上的 DPO 是否更多体现为“精修”

训练结果（high only）：

- `train_loss = 1.1884`
- `train_runtime = 0:04:38`

自动规则评测（SFT vs DPO）：

- `schema_valid`
  - SFT: `47 / 48`
  - DPO: `48 / 48`
- `category_matches_reference`
  - SFT: `70.21%`
  - DPO: `68.75%`
- `severity_matches_reference`
  - SFT: `63.83%`
  - DPO: `60.42%`

pairwise judge（SFT vs DPO）：

- `DPO wins = 13`
- `SFT wins = 7`
- `tie = 28`
- 去掉 tie 后：
  - `DPO win rate = 65%`
- `overall score delta = +0.1915`

关键行为：

- 自动规则评测显示：
  - DPO 主要把结构稳定性从 `47/48` 补到了 `48/48`
- judge 显示：
  - DPO 在内容质量上仍有正收益
  - 但大量 `tie` 说明它更像在强基线上做边界样本精修

一句话：

- **8B DPO 有效，但更像“精修”而不是“拉升”。**

## 8. 4B 对齐模型 vs 8B base

阶段定位：

- 用来证明任务对齐的收益是否足以跨越模型规模差距

pairwise judge：

### `4B SFT` vs `8B base`

- `4B wins = 37`
- `8B base wins = 10`
- `tie = 1`
- 去掉 tie 后：
  - `4B win rate = 78.72%`

### `4B DPO` vs `8B base`

- `4B DPO wins = 35`
- `8B base wins = 6`
- `tie = 7`
- 去掉 tie 后：
  - `4B DPO win rate = 85.37%`

关键行为：

- 4B 对齐模型在 winner 上明显压过 8B base
- 但平均分差距并不夸张
- 这说明它们赢得更多是“稳定小胜”，而不是“少数样本大胜”

一句话：

- **在当前任务上，任务对齐的收益足以跨越一定的模型规模差距。**

## 9. 当前最该记住的一句话

- `0.5B`：流程验证
- `3B`：首次明显 scale-up 收益
- `4B strict`：稳定 baseline
- `8B qlora`：当前主实验位
- `14B qlora`：训练甜点位上沿
- `4B / 8B DPO`：可行，但收益有限，且更像风格与工程偏好的进一步塑形
