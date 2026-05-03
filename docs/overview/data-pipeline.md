# 数据获取与合成 Pipeline

这份文档用于统一说明当前项目里两类核心训练数据是怎么来的：

1. `SFT` 数据
2. `DPO` 数据

目标不是保留所有实验细节，而是讲清楚：

- 数据从哪里来
- 中间做了哪些处理
- 为什么这样做
- 最终给训练框架吃的产物长什么样

相关文档：

- [docs/5060ti/data-construction-log.md](/hy-tmp/llm-lab/docs/5060ti/data-construction-log.md)
- [docs/4090/2026-05-02-final-dpo-dataset.md](/hy-tmp/llm-lab/docs/4090/2026-05-02-final-dpo-dataset.md)
- [docs/4090/2026-05-02-dpo-candidate-generation-smoke.md](/hy-tmp/llm-lab/docs/4090/2026-05-02-dpo-candidate-generation-smoke.md)

## 1. 总体思路

当前项目不是直接拿公开现成数据训练，而是围绕目标任务自己构造数据。

任务本身是：

- 中文训练 / 部署问题诊断
- 输入包含：
  - 用户问题
  - 环境
  - 命令
  - 报错日志
- 输出是一个严格结构化 JSON

因此，数据构造的总体原则是：

1. 数据分布要贴近真实工程问题
2. 输出格式要能支撑 strict JSON 协议
3. 训练数据和评测数据要职责分离
4. DPO 数据不能只看数量，更要看偏好信号质量

---

## 2. SFT 数据 Pipeline

SFT 数据构造可以分成五步：

### 第一步：确定任务 schema

在真正写数据前，先固定输出协议。当前任务输出字段包括：

- `category`
- `severity`
- `summary`
- `root_cause`
- `missing_info`
- `next_steps`

这一步非常关键，因为：

- 它决定了后续数据该写成什么样
- 也决定了评测和 judge 应该比较什么

### 第二步：构造高质量种子样本

最早的数据来源不是公开大规模语料，而是：

- 手工整理的训练 / 部署真实问题
- 覆盖典型报错与故障模式

这批种子样本的作用是：

1. 锚定任务分布
2. 定义目标输出风格
3. 给后续扩写提供高质量模板

### 第三步：用外部模型做扩写

在种子样本基础上，再用外部模型扩写，增加：

- 用户描述方式的变化
- 报错日志细节的变化
- 环境组合的变化
- 信息完整度的变化

扩写的目的不是简单增量，而是提高：

- 表达多样性
- 场景覆盖面
- 模型训练时对不同输入风格的鲁棒性

### 第四步：清洗与质量筛选

扩写后的数据不会直接进入训练，而要经过：

- 格式清洗
- 内容筛查
- 去掉明显不合理或质量差的样本

这一步的意义在于：

- 保证训练集不是“量大但噪声高”
- 尽量让模型学习到稳的工程风格，而不是不一致的口径

### 第五步：构建最终训练集与多种视图

清洗后的数据最终形成：

- 原始项目内训练集
- LLaMA-Factory 可直接吃的 Alpaca 视图
- strict prompt / default prompt 的不同切分视图
- train / eval / smoke 切分

最终关键产物包括：

- `data/sft_train_final.jsonl`
- `data/llamafactory/diagnosis_sft_strict_json_prompt_train_alpaca.json`
- `data/llamafactory/diagnosis_sft_strict_json_prompt_eval_alpaca.json`
- `data/llamafactory/diagnosis_sft_strict_json_prompt_smoke_alpaca.json`

---

## 3. 为什么 SFT 要分 strict / default 两条线

SFT 阶段并不是只有一份 prompt，而是有两条主要路线：

- `default_prompt`
- `strict_json_prompt`

这样做的原因是：

1. 可以观察 base model 的自然 JSON 倾向
2. 可以判断模型的收益究竟来自：
   - 更强的任务对齐
   - 还是更强的协议约束
3. 最终为正式主线收束提供证据

最终实验已经表明：

- `strict_json_prompt` 更适合作为正式协议主线

因此后续大部分训练、评测和 DPO 都优先围绕 strict 路线展开。

---

## 4. DPO 数据 Pipeline

DPO 数据的构造方式和 SFT 很不一样。  
它不是“写一个标准答案”，而是要构造：

- 同一个 prompt
- 两个候选答案
- 再确定谁更好

当前 DPO 数据构造可以分成六步：

### 第一步：选 prompt 池

当前 DPO prompt 主要来自：

- `train` 分布样本

而不是 `eval`。

原因是：

- `eval` 需要保持纯净，供后续评测使用
- `DPO` 本质上还是训练数据
- 当前任务分布在 train 中已经比较清楚

### 第二步：对同一个 prompt 生成两个候选答案

当前做法是：

- 让两个不同能力/风格的模型
- 对同一个 train prompt 各生成一份答案

我们当前尝试过的健康组合是：

- `deepseek-v4-pro`
- `deepseek-v4-flash`

这里候选模型组合的目标不是：

- 一个极强，一个完全崩

而是：

- 强模型常常更好
- 弱模型也有机会在某些样本上更保守、更贴日志

这样才能产生对 DPO 更有价值的 pair。

### 第三步：用独立 judge 判 winner

候选答案生成后，再交给一个独立 judge 模型比较：

- `winner`
- `winner_confidence`
- 不同维度的优劣

judge 关注的核心维度包括：

- `evidence_groundedness`
- `root_cause_quality`
- `actionability`
- `missing_info_quality`
- `overall_engineering_quality`

### 第四步：过滤 tie 和低价值 pair

不是每个 prompt 都会进入最终 DPO 数据。

如果：

- `winner = tie`

就不进入最终 preference dataset。

此外，后续还会按：

- `high`
- `medium`
- `low`

对 confidence 分层。

### 第五步：多批次合并

因为 DPO 候选不是一次性生成完的，而是分多次批量生成，所以需要把：

- smoke
- 100 条
- 200 条
- 其他补跑批次

合并成一份总表。

合并时，采用：

- `sample_id` 作为主键
- `max_per_sample_id = 2`
- `prefer_latest = true`

这意味着：

- 同一条 prompt 最多保留两对
- 后面生成的质量更稳定批次优先

### 第六步：导出正式 DPO 训练集

从合并后的 `judge_results.jsonl` 再导出两版正式 preference 数据：

- `high_only`
- `high_plus_medium`

当前关键统计：

- `high_only_count = 148`
- `high_plus_medium_count = 275`

这两版数据就是当前第一版正式 DPO 训练集。

---

## 5. 为什么同一个 sample_id 最多允许 2 对

这是一条很重要的设计决策。

如果完全不允许重复：

- 很多有价值的不同偏好差异会被压掉

如果无限允许重复：

- 同一 prompt 权重会被放大
- 分布会不均衡

所以当前折中是：

- 每个 `sample_id` 最多保留 `2` 对

这两对的意义通常可能不同：

1. 一对更偏 groundedness / root_cause
2. 一对更偏 actionability / missing_info

这样做既保留了信息密度，也避免某个样本反复主导训练。

---

## 6. 当前 DPO 数据的局限

这批 DPO 数据虽然已经足以支撑第一轮实验，但也有明确局限：

### 1. 偏好目标是复合的

当前 winner 背后的原因可能来自：

- groundedness
- actionability
- missing_info
- 工程保守性

这说明它不是一个单轴偏好任务，而是复合目标。

### 2. medium 样本带来的信号更杂

实验已经表明：

- `high_only` 更稳
- `high + medium` 更容易让训练曲线抖动

这说明：

- medium 样本有增量
- 但噪声也明显更大

### 3. DPO 对数据质量比 SFT 更敏感

SFT 容忍一定风格不一致。  
DPO 则更吃：

- pair 差异是否清楚
- judge 是否稳定
- chosen / rejected 是否真的在比你想优化的偏好

所以 DPO 阶段的主要难点已经不再是“脚本能不能跑”，而是：

- 偏好定义
- 候选设计
- 清洗策略

---

## 7. 当前数据 Pipeline 的最重要结论

如果把整个数据 pipeline 压成一句话：

- `SFT` 数据是通过：  
  **种子样本 -> 扩写 -> 清洗 -> 严格协议视图 -> train/eval 切分**

- `DPO` 数据是通过：  
  **train prompt -> 双模型候选生成 -> judge 判优 -> 多批次合并 -> per-sample 控制 -> confidence 分层导出**

当前阶段，这条数据 pipeline 已经足够支撑：

1. 一轮完整的 SFT 实验闭环
2. 一轮完整的 DPO 可行性验证

但如果后面还要进一步提高 DPO 收益，主要工作量会继续转向：

- 更纯的偏好目标
- 更细的 pair 设计
- 更严格的数据清洗

---

## 8. 一句话总结

当前项目的数据 pipeline 已经从“能否构造出一批能训练的数据”推进到了：

**能否围绕同一个任务，分别构造出适合 SFT 的监督数据和适合 DPO 的偏好数据，并从中看清训练收益、模型规模效应与数据工程瓶颈。**
