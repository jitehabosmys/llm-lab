# 2026-05-02 4B 对齐模型 vs 8B Base：任务对齐跨越量级差距

这份文档记录的是当前项目里一个很有代表性的对照：

- `Qwen3-4B strict SFT`
- `Qwen3-4B strict DPO`

分别和：

- `Qwen3-8B base`

做 pairwise judge 比较。

这个对照的价值在于，它能直接回答一个很重要的问题：

**在当前这种强结构化、工程诊断类任务上，任务对齐带来的收益，能否在一定程度上跨越模型规模差距。**

相关文档：

- [2026-05-01-qwen3-4b-strict-repro-on-4090.md](/hy-tmp/llm-lab/docs/4090/2026-05-01-qwen3-4b-strict-repro-on-4090.md)
- [2026-05-01-qwen3-8b-qlora-sft-log.md](/hy-tmp/llm-lab/docs/4090/2026-05-01-qwen3-8b-qlora-sft-log.md)
- [2026-05-02-4b-8b-dpo-training-log.md](/hy-tmp/llm-lab/docs/4090/2026-05-02-4b-8b-dpo-training-log.md)

## 1. 对比对象

本轮比较使用：

### A 组

- `qwen3_4b_strict_json_prompt_sft`
- `qwen3_4b_strict_json_prompt_dpo`

### B 组

- `qwen3_8b_strict_json_prompt_base`

这里的关键在于：

- `8B base` 已经是更大的模型
- 但它没有经过当前任务的 SFT / DPO 对齐

因此这轮比较非常适合用来观察：

- 模型规模
- 和任务对齐

谁在当前任务里更重要。

## 2. `4B SFT` vs `8B base`

结果如下：

- `4B SFT wins = 37`
- `8B base wins = 10`
- `tie = 1`

去掉 `tie` 之后：

- `4B SFT win rate = 78.72%`

维度 winner 分布：

- `evidence_groundedness`: `31 vs 6`
- `root_cause_quality`: `33 vs 9`
- `actionability`: `27 vs 4`
- `missing_info_quality`: `27 vs 10`
- `overall_engineering_quality`: `35 vs 8`

总体平均分：

- `4B SFT = 3.5000`
- `8B base = 3.4167`
- `delta = +0.0833`

## 3. `4B DPO` vs `8B base`

结果如下：

- `4B DPO wins = 35`
- `8B base wins = 6`
- `tie = 7`

去掉 `tie` 之后：

- `4B DPO win rate = 85.37%`

维度 winner 分布：

- `evidence_groundedness`: `33 vs 10`
- `root_cause_quality`: `34 vs 10`
- `actionability`: `31 vs 6`
- `missing_info_quality`: `31 vs 7`
- `overall_engineering_quality`: `33 vs 6`

总体平均分：

- `4B DPO = 3.5208`
- `8B base = 3.4792`
- `delta = +0.0417`

## 4. 如何理解“胜率明显领先，但分数优势不大”

这组结果最有意思的地方就在这里。

表面上看：

- `4B SFT` 和 `4B DPO` 在 winner 上都明显压过 `8B base`

但分数层面：

- 整体平均分差距并不大

这说明的不是矛盾，而是一种很典型的现象：

### 4.1 4B 对齐模型更“稳”

在很多样本上：

- `4B` 更贴当前任务格式
- 更保守
- 更 grounded
- 更像一个靠谱的工程诊断助手

所以 judge 在二选一时，更常把胜利判给 `4B`。

### 4.2 8B base 的底子并不差

虽然 `8B base` 输得多，但它的平均分并没有被甩开很多，说明：

- 它在很多样本上也具备不错的底层能力
- 只是风格不够稳
- 不够贴当前任务协议
- 工程保守性和结构化输出习惯不如已经对齐过的 4B

换句话说：

- `8B base` 不是“完全不会”
- 而更像是“会，但不够像我们想要的系统”

### 4.3 4B 的优势更像“稳定小胜”

因此，当前结果更像：

- `4B` 经常能赢
- 但很多时候是“略优但稳定优”
- 而不是少数样本上大幅碾压

这也是为什么：

- winner 胜率差距很大
- 平均分差距却不算夸张

## 5. DPO 在这组比较里的作用

从结果看：

### `4B SFT` vs `8B base`

- `win rate = 78.72%`
- `overall delta = +0.0833`

### `4B DPO` vs `8B base`

- `win rate = 85.37%`
- `overall delta = +0.0417`

这说明：

- `DPO` 进一步提升了 `4B` 相对 `8B base` 的胜率
- 但并没有显著拉大“每次赢的时候的分差”

更像是：

- `DPO` 把 `4B` 往更稳、更少犯错、更常略优的方向推了
- 而不是把它改造成了完全不同等级的系统

## 6. 这组结果的项目价值

这轮对照给出的最重要结论是：

**在当前这种强结构化、工程诊断类任务中，任务对齐带来的收益，已经足以在相当多样本上跨越模型规模差距。**

更具体地说：

- 已经对齐过的 `4B` 模型
- 在当前任务上
- 可以明显压过未对齐的 `8B base`

这并不意味着：

- `4B` 在所有能力上都全面优于 `8B`

而是意味着：

- 对这个具体任务来说
- “是否对齐任务协议和工程偏好”
- 比“参数规模更大但未对齐”
- 更能决定最终表现

## 7. 一句话结论

这组 `4B 对齐模型 vs 8B base` 的对照结果说明：

**在当前工程诊断任务上，任务对齐的收益足以跨越一定的模型规模差距；4B 的 SFT / DPO 版本虽然在平均分上并没有大幅甩开 8B base，但在 pairwise winner 上已经形成了明显领先，这说明它们赢得更多是“稳定小胜”，而不是“少数样本大胜”。**
