# 2026-05-02 Qwen3-14B QLoRA Strict SFT 实验记录

这份文档记录的是当前项目在 `RTX 4090 24GB` 单卡环境上完成的一轮 `Qwen3-14B + QLoRA + strict_json_prompt` 训练。

这轮实验的核心目标是回答：

1. `14B` 是否仍然可以在 `4090 24GB` 单卡环境上稳定承载 `QLoRA`
2. 相比已经完成的 `8B QLoRA` 主线，`14B` 是否继续给出更强的训练信号
3. 在当前资源约束下，`14B` 是否已经接近“继续 scale up 的甜点位”

相关文档：

- [2026-05-01-qwen3-8b-qlora-sft-log.md](/hy-tmp/llm-lab/docs/4090/2026-05-01-qwen3-8b-qlora-sft-log.md)
- [2026-05-01-qwen3-8b-qlora-throughput-tuning.md](/hy-tmp/llm-lab/docs/4090/2026-05-01-qwen3-8b-qlora-throughput-tuning.md)
- [2026-05-01-qwen3-4b-strict-repro-on-4090.md](/hy-tmp/llm-lab/docs/4090/2026-05-01-qwen3-4b-strict-repro-on-4090.md)

## 1. 实验标识

- 日期：`2026-05-02`
- 机器：`RTX 4090 24GB`
- 模型：`Qwen/Qwen3-14B`
- 微调方式：`QLoRA`
- 协议：`strict_json_prompt`
- 模板：`qwen3_nothink`

训练配置：

- [4090_qwen3_14b_smoke_qlora_sft_strict_json_prompt.yaml](/hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_14b_smoke_qlora_sft_strict_json_prompt.yaml)
- [4090_qwen3_14b_full_qlora_sft_strict_json_prompt.yaml](/hy-tmp/llm-lab/configs/llamafactory/4090_qwen3_14b_full_qlora_sft_strict_json_prompt.yaml)

推理配置：

- [qwen3_14b_base_hf_infer_strict_json_prompt.yaml](/hy-tmp/llm-lab/configs/llamafactory/qwen3_14b_base_hf_infer_strict_json_prompt.yaml)
- [qwen3_14b_full_qlora_hf_infer_strict_json_prompt.yaml](/hy-tmp/llm-lab/configs/llamafactory/qwen3_14b_full_qlora_hf_infer_strict_json_prompt.yaml)

输出目录：

- `/hy-tmp/outputs/llamafactory/qwen3-14b-smoke-qlora-sft-strict-json-prompt-4090`
- `/hy-tmp/outputs/llamafactory/qwen3-14b-full-qlora-sft-strict-json-prompt-4090`

W&B run：

- smoke: `qtq0jqwk`
- full: `myvw4juu`

## 2. 配置摘要

这轮实验延续了 `8B` 主线的基本训练配方，只把模型规模继续提升到 `14B`。

量化相关配置保持：

- `quantization_bit: 4`
- `quantization_type: nf4`
- `double_quantization: true`

LoRA 相关配置保持：

- `lora_rank: 8`
- `lora_alpha: 16`
- `lora_dropout: 0.05`
- `lora_target: all`

这轮设计原则仍然是：

- 优先控制变量
- 先回答 scale up 是否继续有收益
- 暂不把 `rank`、数据配方、学习率等同时改掉

## 3. Smoke 结果

`14B QLoRA smoke` 最终指标：

- `epoch = 20.0`
- `train_loss = 1.1824`
- `eval_loss = 1.4863`
- `train_runtime = 0:06:33.42`

这说明：

- `14B` 在当前 `4090 24GB` 环境上是稳定可训的
- `QLoRA`、数据、模板、checkpoint、评估链路都没有结构性阻塞
- 当前单卡环境已经不仅能承载 `8B`，也能承载 `14B`

## 4. Full 结果

`14B QLoRA full` 最终指标：

- `epoch = 3.0`
- `train_loss = 1.5571`
- `eval_loss = 1.2974`
- `train_runtime = 0:11:28.53`
- `eval_samples = 48`

这说明：

- `14B` 不只是 smoke 可以跑通，而是完整 `SFT` 也能稳定跑满
- 训练时间相比 `8B` 有增加，但增长幅度仍然在可接受范围内

## 5. 与 8B 主线的对照

当前最重要的对照对象已经不是 `4B`，而是上一阶段主力候选 `8B QLoRA`。

### 5.1 Smoke 对照

`8B smoke`：

- `train_loss = 1.4574`
- `eval_loss = 1.4259`
- `train_runtime = 0:05:14.72`

`14B smoke`：

- `train_loss = 1.1824`
- `eval_loss = 1.4863`
- `train_runtime = 0:06:33.42`

这里要谨慎解读：

- `14B smoke train_loss` 很低
- 但 `14B smoke eval_loss` 并没有优于 `8B smoke`

所以 smoke 阶段更适合用来判断：

- 是否可训
- 是否稳定

而不宜过度下结论说 `14B smoke` 已经全面强于 `8B smoke`

### 5.2 Full 对照

`8B full`：

- `train_loss = 1.7031`
- `eval_loss = 1.3887`
- `train_runtime = 0:09:15.69`

`14B full`：

- `train_loss = 1.5571`
- `eval_loss = 1.2974`
- `train_runtime = 0:11:28.53`

这里的结论就清楚得多：

- `14B full` 的训练信号明显优于 `8B full`
- `eval_loss` 提升幅度达到 `-0.0913`
- 相比之下，训练时间只增加了大约 `2m13s`

从当前训练指标看，这不是“勉强提升”，而是一次比较有存在感的正向增益。

## 6. 显存与吞吐观察

训练过程中观察到的大致 GPU 状态：

- 典型显存占用约 `15.2GB / 24.6GB`
- GPU 利用率接近 `100%`
- 功耗约 `390W / 450W`

这说明：

- `14B QLoRA` 在当前卡上已经开始更充分地吃满 GPU
- 但还没有因为显存逼近极限而进入明显挣扎状态
- 当前环境仍然可以比较从容地承接这条 `14B` 训练主线

## 7. 如何评价这轮 14B 实验

### 7.1 训练层面是成功的

理由：

- smoke 跑通
- full 跑通
- 没有出现量化或显存相关的结构性失败
- 相比 `8B full`，训练信号明显增强

### 7.2 `14B` 的边际收益目前看是存在的

到 `8B` 时，项目已经出现一个问题：

- `4B -> 8B` 的内容质量提升存在，但幅度开始收缩

而这轮 `14B` 至少在训练信号上表明：

- `8B -> 14B` 仍然不是纯挤牙膏
- 在当前条件下，继续 scale up 依然有值得认真验证的收益

### 7.3 但这仍不是最终能力结论

和 `8B` 阶段一样，这轮 `14B` 结果当前主要回答的是：

- 可训性
- 收敛趋势
- 时间与资源成本是否可接受

它还没有正式回答：

- `14B strict` 的结构化输出是否稳定
- `14B` 的内容质量是否在 judge 视角下明确优于 `8B`

这些问题仍然需要：

1. HF 自动规则评测
2. `14B strict qlora` vs `8B strict qlora` 的 pairwise judge

## 8. 对后续路线的意义

这轮实验把当前路线进一步推到一个新的判断点：

1. `14B` 在单卡 `4090 + QLoRA` 上可行
2. 它在训练信号上明显优于 `8B`
3. 这使得 `14B` 很像当前资源约束下的一个“甜点位候选”
4. 下一步最重要的是确认：
   - 这种提升是否能在结构和内容评测里继续成立
   - 如果成立，是否意味着 scale up 仍然值得
   - 如果不成立，就该把主线转向 `DPO` / 数据质量 / 格式稳态优化

## 9. HF 推理评测受限：当前单卡路径的边界

在继续做 `14B` 推理评测时，当前项目尝试了两条 HF 推理路径：

### 9.1 `auto device_map`

在 `adapter_name_or_path` 路径下，`14B lora` 推理会在：

- `PeftModel.from_pretrained(...)`
- `peft_model.load_adapter(...)`
- `accelerate.get_balanced_memory(...)`

这条链路中报错，表现为：

- `TypeError: unhashable type: 'set'`

这说明：

- 当前 `PEFT + accelerate + auto device map` 组合在 `14B lora` 上存在基础设施级兼容性问题
- 问题发生在 adapter 挂载阶段，而不是数据或 prompt 阶段

### 9.2 强制单卡 `cuda:0`

为绕过上面的 `auto device_map` 路径，又尝试了强制单卡方式。

结果显示：

- `14B base` 在加载阶段就已经接近填满 `4090 24GB`
- 还未进入正式生成阶段，就已经触发：
  - `torch.OutOfMemoryError`

这意味着：

- 问题并不只是 `KV cache` 或 decode 阶段
- 而是当前这条 `HF + 单卡强塞 + 14B` 路径本身已经逼近硬件边界

换句话说，当前 `14B` 在这台机器上的情况是：

- 训练：可行
- HF 自动评测：基础设施上不够稳

补充一点更直观的观察：

- `14B base` 在少量样本探针中能够正常生成并通过 strict JSON 解析
- 但单条样本的 HF 推理耗时大约已经达到 `140s ~ 160s`

这说明：

- `14B base` 不是“完全不能推”
- 但在当前 `HF + 单样本串行` 评测链路下，它已经变得非常昂贵
- 因此后续即使继续保留 `HF` 作为严格基准，`14B base` 也更适合作为小样本探针，而不是每轮都跑满 `48` 条

## 10. HF LoRA 推理的两次尝试

针对 `14B lora`，当前项目实际尝试了两种 HF 推理方式。

### 10.1 方式一：默认 `auto device_map`

在这条路径下：

- `base` 能加载
- `adapter_name_or_path` 挂载阶段报错

错误链路集中在：

- `PeftModel.from_pretrained(...)`
- `peft_model.load_adapter(...)`
- `accelerate.get_balanced_memory(...)`

典型报错为：

- `TypeError: unhashable type: 'set'`

这说明：

- `14B lora` 在当前 `PEFT + accelerate + auto device_map` 组合下，存在明显的基础设施级兼容性问题
- 问题发生在 adapter 挂载与自动显存平衡阶段，而不是训练产物本身损坏

### 10.2 方式二：绕过 `auto`，强制单卡 `cuda:0`

为绕开上述 `auto device_map` 路径，又尝试了强制单卡加载。

结果显示：

- 报错阶段提前到 `base model` 加载过程
- 还未真正开始 adapter 推理，就已经在模型物化到 GPU 时触发：
  - `torch.OutOfMemoryError`

这说明：

- 如果彻底放弃 `auto`，单卡 `4090 24GB` 对 `14B` 的 HF 推理装载安全余量已经非常小
- 即使强行绕过 `auto` 相关 bug，也会立刻遇到更本质的显存边界

## 11. vLLM 尝试：CUDA 兼容与模型配置兼容的错位

为了验证 `14B` 是否适合转向高性能推理 backend，当前项目也尝试了 `vLLM` 路线。

实际遇到的情况分两步：

### 11.1 新版 `vLLM` 与当前 CUDA 环境不兼容

在当前机器上直接安装较新的 `vLLM` 后，出现：

- `ImportError: libcudart.so.13: cannot open shared object file`

这说明：

- 新版 wheel 偏向 CUDA 13
- 而当前机器环境仍是 CUDA 12.x / cu121 路线

### 11.2 退回旧版 `vLLM` 后，又与 `Qwen3-14B` 配置结构不兼容

为了匹配 CUDA 12.x，又尝试了更早版本的 `vLLM`。

这时服务启动阶段报错：

- `_get_and_verify_max_len`
- `assert "factor" in rope_scaling`

而模型 `config.json` 中实际情况是：

- `rope_scaling = None`
- `max_position_embeddings = 40960`

这说明：

- 旧版 `vLLM` 虽然更适合当前 CUDA 环境
- 但它又不完整支持当前这版 `Qwen3-14B` 的配置结构

因此当前 `vLLM` 路线卡在一个双重错位上：

1. 新版 `vLLM` 更可能理解 `Qwen3-14B`，但 wheel 偏向 CUDA 13
2. 旧版 `vLLM` 更匹配 CUDA 12.x，但又太老，不理解新版 `Qwen3-14B` config schema

## 12. 这组推理尝试真正说明了什么

这组推理尝试的价值不在于“证明 14B 彻底不能推”，而在于把问题定位得非常具体：

1. `14B` 训练层面是明确可行的
2. `14B base` 在 HF 下可做小样本行为探针，但全量评测成本很高
3. `14B lora` 在当前 `HF + PEFT + 单卡` 推理链上同时碰到了：
   - `auto device_map` 装载 bug
   - 强制单卡后的显存边界
4. `vLLM` 路线则同时碰到了：
   - CUDA wheel 兼容问题
   - 旧版本对新版 Qwen3 配置结构的理解问题

因此，当前最准确的结论不是：

- `14B` 不值得继续考虑

而是：

- `14B` 已经非常像当前资源约束下的训练甜点位上沿
- 它的能力收益仍值得重视
- 但它在现有软件栈上的推理与评测承载能力已经开始明显落后于训练承载能力

## 13. 这对 14B 的定位意味着什么

结合训练成功和推理受限两个事实，当前 `14B` 的定位可以更明确地收束成：

1. `14B` 是当前资源约束下一个很有吸引力的训练甜点位候选
2. 但它还不是当前这条 `HF + PEFT + 单卡` 推理评测链上的稳定甜点位
3. 这说明在当前项目里：
   - 能力上限已经继续上去了
   - 工程承载边界也开始明显出现

因此，当前最合理的结论不是：

- `14B` 不值得继续看

而是：

- `14B` 值得保留为高能力候选
- 但它的推理评测与部署验证需要更强的基础设施支持

## 14. 一句话结论

这轮 `Qwen3-14B + QLoRA + strict_json_prompt` 实验说明：

**在 4090 单卡上，`14B` 不仅稳定可训，而且在完整 `SFT` 的训练信号上明显优于 `8B`，而时间成本只温和增加；但与此同时，它也开始明确暴露出当前 `HF + PEFT + 单卡` 推理评测链的基础设施边界，因此它更像“训练甜点位候选”，而不是当前基础设施上可无缝接管主线的稳定推理位。**
