# 训练与推理配置参数说明

这份文档用于解释当前项目中常见训练 / 推理配置参数的含义，以及为什么不同模型会使用不同设置。

它关注两个问题：

1. 这些参数分别控制什么
2. 我们为什么在不同阶段、不同模型上这样设

相关配置文件：

- `0.5B / 3B / 4B / 8B / 14B` 的 SFT 配置
- `4B / 8B` 的 DPO 配置
- `4B / 8B / 14B` 的 HF infer 配置

## 1. 先看配置的大结构

当前这套 YAML 大致都分成几段：

- `model`
- `method`
- `dataset`
- `output`
- `train`
- `eval`

可以粗略理解成：

- `model`：加载哪个模型、用什么量化、放在哪
- `method`：训练方式（LoRA / QLoRA / DPO）
- `dataset`：吃哪份数据、用什么模板
- `output`：输出到哪里、多久存一次
- `train`：batch、学习率、epoch 等优化超参
- `eval`：多久验证一次

---

## 2. 模型相关参数

### `model_name_or_path`

表示：

- 基座模型路径
- 可以是 Hugging Face / ModelScope 名称
- 也可以是本地目录

为什么不同阶段不同：

- 小模型阶段更常用远程名称
- 大模型阶段更常用本地路径

原因：

- 大模型下载成本高
- 本地路径更稳，也更适合反复加载评测

### `adapter_name_or_path`

表示：

- 在 base model 之上挂载的 LoRA / QLoRA adapter

什么时候需要：

- 训练时：如果是继续做 DPO，通常要在已有 SFT adapter 基础上接着训
- 推理时：用来加载 SFT / DPO 后的增量权重

### `trust_remote_code`

表示：

- 允许模型加载自定义代码实现

为什么常设为 `true`：

- `Qwen` 系列模型经常依赖自定义实现
- 否则容易出现 tokenizer / model config 不兼容

### `cache_dir`

表示：

- 模型和 tokenizer 缓存放在哪里

为什么都指向 `/hy-tmp/models`：

- 把大文件统一放到高速本地盘
- 避免挤爆系统盘

---

## 3. LoRA / QLoRA 相关参数

### `finetuning_type: lora`

表示：

- 当前走的是参数高效微调，而不是全参数训练

为什么一直用 LoRA：

- 单卡资源有限
- 能显著降低训练成本
- 对当前任务已经足够有效

### `lora_rank`

表示：

- LoRA 低秩矩阵的 rank

当前常设：

- `rank = 8`

为什么设 `8`：

- 是当前任务里一个很稳的经验值
- 足够让模型学到任务协议与风格
- 同时显存和训练成本都比较可控

为什么没有随着模型变大立即改：

- 为了控制变量
- 当前阶段更重要的是判断模型规模收益
- 而不是同时优化 LoRA rank

### `lora_alpha`

表示：

- LoRA 更新的缩放系数

当前常设：

- `16`

原因：

- 与 `rank=8` 搭配是比较常见、稳妥的经验组合

### `lora_dropout`

表示：

- LoRA 层的 dropout

当前常设：

- `0.05`

原因：

- 给一点轻微正则化
- 既不过分压制训练，也防止过快记忆

### `lora_target: all`

表示：

- 把 LoRA 注入到模型里的所有线性层

为什么设 `all`：

- 当前任务不是一个特别局部的适配问题
- 让模型更全面地学习结构和工程风格

### `quantization_bit: 4`

表示：

- 基座模型按 4-bit 量化加载

这是 `QLoRA` 的核心条件。

为什么只出现在 `8B / 14B`：

- 小模型（4B 及以下）单卡 LoRA 已经足够
- 大模型若不量化，很难在 4090 上稳定训练

### `quantization_type: nf4`

表示：

- 4-bit 量化采用 `NF4` 格式
- QLoRA 里的“量化/反量化”核心思想是：权重长期保存在 4-bit（通常是 NF4），计算时临时反量化到 16-bit（BF16/FP16），计算完立刻丢掉，只训练新增的 LoRA 参数。

为什么设 `nf4`：

- 是 QLoRA 常用且稳定的选择

### `double_quantization: true`

表示：

- 对量化常数再做一层压缩

为什么开：

- 进一步省显存
- 通常代价不大

---

## 4. 数据与模板参数

### `dataset`

表示：

- 训练集名字

例如：

- `diagnosis_sft_train`
- `diagnosis_sft_strict_json_prompt_train`
- `diagnosis_dpo_high_only`

为什么不同：

- SFT / DPO 使用的是不同数据格式
- strict / default 也是不同主线

### `eval_dataset`

表示：

- 验证集名字

在 SFT 中通常会单独给一份 eval。  
DPO 目前有些配置未显式开 eval，而是先做 train + 后续外部评测。

### `dataset_dir`

表示：

- 从哪个目录读取 `dataset_info.json`

为什么重要：

- 如果不显式写成项目自己的 `data/llamafactory`
- LLaMA-Factory 可能默认去读它自己的 `data/dataset_info.json`
- 然后就会出现：
  - 找不到我们新增的 DPO 数据集名

### `template`

表示：

- 当前数据/推理走哪套 prompt template

常见的：

- `qwen`
- `qwen3_nothink`
- `qwen3`

为什么不同模型不同：

- `Qwen2.5` 仍然走 `qwen`
- `Qwen3` 走 `qwen3_nothink`

### 关于 `qwen3_nothink`

要特别注意：

- 在训练阶段，`qwen3_nothink` 适合构造 no-think 风格数据
- 但在当前 HF 推理链里，它**不等于**真正硬关闭 thinking

真正能稳定关掉 thinking 的方式是：

- `template: qwen3`
- `enable_thinking: false`

这是当前项目中最重要的推理配置经验之一。

### `cutoff_len`

表示：

- 输入截断长度

当前常见值：

- `1024`（smoke）
- `1536`（full）
- `2048`（DPO）

为什么这样分：

- smoke 先保守，降低显存风险
- full 扩到更接近真实任务长度
- DPO 常再大一点，因为 chosen/rejected pair 本身更长

---

## 5. 输出与日志参数

### `output_dir`

表示：

- 训练输出目录

为什么总是单独命名：

- 方便保存不同模型、不同阶段、不同配置的产物
- 避免覆盖

### `logging_steps`

表示：

- 每多少个优化 step 打一次训练日志

为什么常设：

- `5`

这是一个平衡点：

- 不会太密
- 也足够观察 loss / rewards 曲线

### `save_steps`

表示：

- 每多少个优化 step 存一次 checkpoint

为什么常设：

- `25`

当前数据集比较小，训练步数也不算特别多，所以：

- `25` 足够频繁
- 又不会太浪费磁盘

### `save_total_limit`

表示：

- 最多保留多少个 checkpoint

为什么设 `2` 或 `3`：

- 控制磁盘占用
- 保留足够回溯空间

### `report_to`

表示：

- 日志同步到哪里

当前常用：

- `wandb`

原因：

- 方便看 loss、reward、margin、显存与吞吐变化

---

## 6. 训练超参数

### `per_device_train_batch_size`

表示：

- 单卡一次实际送进模型的物理 batch

为什么经常设成 `1`：

- 保守
- 显存压力最可控

为什么有时提到 `2`：

- 在 `8B` 上我们已经验证显存仍有余量
- `2` 可以显著提高吞吐

### `gradient_accumulation_steps`

表示：

- 梯度累积多少次后才做一次优化更新

它和 `batch_size` 是一组联动参数。

例如：

- `batch=1, grad_acc=32`
- `batch=2, grad_acc=16`

这两种设置的**有效 batch**差不多，但吞吐可能不同。

### 为什么不同模型的 `grad_acc` 不同

通常原因有两个：

1. 模型越大，物理 batch 越难放大
2. 我们希望不同规模下保持比较接近的有效 batch

### `learning_rate`

SFT 常用：

- `2e-4`

DPO 常用：

- `5e-6`

为什么差这么大：

- SFT 是在学整套任务协议与风格
- DPO 更像在已有 SFT 基础上做偏好微调
- DPO 若学习率太大，更容易把原有能力搞乱

### `num_train_epochs`

当前常设：

- `3.0`

原因：

- 当前数据集规模不大
- 3 epoch 足以观察趋势
- 再往上更容易带来过拟合和额外成本

### `lr_scheduler_type: cosine`

表示：

- 学习率按 cosine 衰减

原因：

- 常见、稳定
- 适合当前这种中小规模微调

### `warmup_steps` / `warmup_ratio`

作用：

- 前期让学习率缓慢升起来

SFT 多用：

- `warmup_steps`

DPO 多用：

- `warmup_ratio`

原因主要是：

- DPO 训练步数和数据规模更适合按比例设置

### `bf16`

表示：

- 训练使用 bfloat16

为什么常设：

- 在当前硬件上比较稳
- 通常比 fp16 更不容易数值不稳定

---

## 7. DPO 特有参数

### `stage: dpo`

表示：

- 训练进入偏好优化阶段，而不是普通 SFT

### `pref_beta`

表示：

- DPO 偏好强度的一个核心超参

当前常设：

- `0.1`

为什么选这个值：

- 是比较稳妥的经验起点
- 不会太激进
- 适合先做第一版 DPO 探索

### `pref_loss: sigmoid`

表示：

- 当前用的是标准 DPO 形式

原因：

- 最主流
- 最方便和社区经验对齐

---

## 8. 推理配置参数

### `infer_backend: huggingface`

表示：

- 当前走 HF 推理链

为什么仍以 HF 为正式主链：

- 行为更稳定
- 与前面所有正式评测结论一致
- backend 变量更少

### `do_sample: false`

表示：

- 用贪心 / 近似确定性生成

原因：

- 评测时希望减少采样随机性
- 让模型比较尽量聚焦在能力，而不是采样波动

### `max_new_tokens`

表示：

- 最多生成多少 token

当前常见：

- `512`

为什么设这么大：

- 给 base 和 lora 足够空间完成 JSON
- 同时也能观察：
  - base 是否容易拖尾
  - 是否经常撞长度上限

### `enable_thinking: false`

只在部分 Qwen3 infer 配置中出现。

它的意义是：

- 真正硬关闭 `Qwen3` 的 thinking 模式

为什么必须显式写：

- 否则 base 模型可能会输出 `<think>...</think>`
- 从而污染 strict JSON 评测

---

## 9. 为什么不同模型要有差异化配置

把差异压缩成几条就是：

### 1. 小模型和大模型的显存约束不同

- `4B` 可以直接 LoRA
- `8B / 14B` 更需要 QLoRA

### 2. `8B` 已证明还有吞吐优化空间

所以出现了：

- `bs=2 / grad_acc=16`

这一类更激进但工程上更优的版本

### 3. `14B` 已经碰到训练与推理的不同边界

- 训练还能跑
- 推理基础设施已明显变脆

所以 `14B` 配置更多是：

- 先证明可训
- 再判断是否值得继续在基础设施上投入

### 4. `4B / 8B` DPO 更像阶段性探索

这里配置重点不再是“怎么把模型训得更强”，而是：

- 数据是否够干净
- DPO 是否有收益
- 收益形态如何

---

## 10. 一句话总结

当前这套配置的核心思想不是“把每个参数都调到最优”，而是：

**先用尽量少的变量把模型规模、协议形式、数据质量和偏好优化的作用分别看清楚，再在已经证明有价值的方向上做更精细的优化。**
