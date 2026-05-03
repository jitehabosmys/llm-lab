# 基础设施与 Troubleshooting

这份文档集中记录当前项目里最值得保留的工程经验与问题排查结论。

重点不是完整复现每次报错，而是保留：

1. 问题是什么
2. 我们最后怎么定位
3. 结论是什么
4. 以后遇到类似问题应该先看什么

## 1. 下载与磁盘

### 1.1 `uv.toml` 不会跨项目自动生效

现象：

- 在 `llm-lab` 里配置的 `uv.toml` 镜像源
- 不会自动被兄弟目录下的 `LLaMA-Factory` 或 `vllm-venv` 继承

结论：

- `uv` 默认只会读当前项目或父目录中的配置
- 如果要让多个仓库都走镜像源：
  - 要么显式设置 `UV_INDEX_URL`
  - 要么写入 `~/.config/uv/uv.toml`

### 1.2 模型下载常见问题不在模型，而在下载链路

已经遇到过的情况包括：

- Hugging Face 官方站超时
- ModelScope 大文件分片失败
- 同一模型目录存在但其实不完整
- 中间缓存和临时文件导致磁盘打满

结论：

- 模型目录“存在”不等于模型“完整”
- 下载完成后必须检查：
  - 模型目录总大小
  - `model-0000x-of-xxxxx.safetensors`
  - `model.safetensors.index.json`
  - tokenizer 与 config 文件

### 1.3 盘被打满时，优先清缓存和失败残留

高占用来源曾包括：

- `/hy-tmp/.cache/uv`
- `/hy-tmp/models/._____temp`

结论：

- 扩容前先看清楚是不是缓存和临时目录在吃盘
- 但当模型规模上到 `14B` 后，扩容本身也开始变成合理的前置动作

## 2. 驱动与训练环境

### 2.1 `torch` wheel 和驱动版本必须配套

曾遇到：

- `torch 2.11.0+cu130`
- 但驱动只有 `535`

现象：

- `torch.cuda.is_available() == False`
- `LLaMA-Factory` CLI 能启动，但 GPU 不可用

结论：

- 这不是训练配置问题
- 是 `torch wheel` 与驱动 / CUDA ABI 不匹配
- 最稳的做法通常不是先动驱动，而是换一个和当前驱动兼容的 PyTorch/CUDA 版本

## 3. Qwen3 的 no-think 不是单靠模板名就能保证

### 3.1 `qwen3_nothink` 不等于真正硬关闭 thinking

在当前 `LLaMA-Factory + HF` 推理链里：

- `template: qwen3_nothink`

并不会真正阻止 `Qwen3` base 生成 `<think>...</think>`。

现象：

- `8B base` 在 strict 评测中 `48/48` 全部失败
- 原因不是 JSON 不会写，而是输出前面统一泄露了 `<think>`

### 3.2 真正有效的 no-think 方式

本地最小验证后确认：

- `template: qwen3`
- `enable_thinking: false`

才是当前链路里真正生效的 hard switch。

结论：

- 如果评测 Qwen3 base / lora 的 strict JSON 遵循能力
- 必须把 thinking 开关单独当实验变量控制住

## 4. 14B：训练甜点位上沿 vs 推理基础设施边界

### 4.1 14B QLoRA 训练是可行的

在单卡 `4090 24GB` 上：

- `14B smoke` 可训
- `14B full` 可训
- 训练信号明显优于 `8B`

这说明：

- 在训练层面，`14B` 仍然值得探索

### 4.2 HF 推理链在 14B 上开始明显变脆

#### 路径一：`auto device_map`

现象：

- `14B lora` 在 adapter 挂载阶段
- 进入 `PEFT + accelerate.get_balanced_memory()`
- 报出兼容性相关错误

结论：

- 当前版本组合下，`14B + adapter + auto device map`
- 已开始触碰基础设施边界

#### 路径二：强制单卡 `cuda:0`

现象：

- 为绕开 `auto` 路径，尝试强制单卡
- 结果连 base model 加载阶段就 OOM

结论：

- 问题已经不是“生成时 KV cache 太大”
- 而是 base model 装载本身就逼近单卡 4090 边界

### 4.3 14B 的更准确定位

因此 `14B` 当前最合理的定位是：

- 训练甜点位上沿候选
- 但不是当前 HF+PEFT 单卡推理评测链上的稳定推理位

## 5. vLLM：不是快不快的问题，而是版本兼容窗口

### 5.1 新版 vLLM

问题：

- 更可能支持新版 Qwen3 config
- 但默认 wheel 往往偏 CUDA 13
- 与当前 CUDA 12.x / cu121 环境不兼容

### 5.2 旧版 vLLM

问题：

- 更适合当前 CUDA 12.x
- 但又太老，不完整理解新版 Qwen3 config
- 在 `Qwen3-14B` 上报 RoPE / config 兼容错误

### 5.3 结论

当前阶段 `vLLM` 的问题已经不是：

- 它快不快

而是：

- 需要一个同时兼容
  - 当前 CUDA 12.x 环境
  - 以及新版 `Qwen3-14B` 配置结构

这进一步说明：

- `14B` 已经开始触碰的不只是显存边界
- 还有软件栈版本窗口边界

## 6. 自动评测与 pairwise judge 的分工

### 6.1 自动规则评测

适合回答：

- JSON 是否可解析
- schema 是否完整
- category / severity 是否命中参考答案

### 6.2 Pairwise judge

更适合回答：

- 哪个回答更 grounded
- 哪个更保守
- 哪个 next_steps 更可执行
- 哪个整体更像靠谱工程师

结论：

- 对当前任务，自动规则评测是必要但不充分的
- DPO 等偏好优化收益，往往更依赖 pairwise judge 才看得清楚

## 7. DPO 数据工程本身是主要难点

### 7.1 候选模型不能一边空答

曾出现：

- 一个候选模型返回空字符串
- Judge 只能在“空答 vs 正常答”之间做简单选择

结论：

- 这种数据适合做故障筛选，不适合作为正式 DPO 主数据

### 7.2 候选模型差距不能过大

理想状态不是：

- 强模型完全碾压

而是：

- 强模型常赢
- 弱模型偶尔能赢
- tie 也存在

这样才能得到更有信息密度的偏好对。

### 7.3 中途失败不能全丢

后来给 DPO 数据生成脚本加了：

- 每 N 条 flush 一次

结论：

- 大批量候选生成一定要做增量落盘
- 否则被 API 限流 / 502 打断后，代价会非常高

## 8. 当前阶段最值得记住的一句话

随着模型规模变大，问题的主导因素会逐步从：

- “训练能不能跑”

转向：

- “推理基础设施能不能承载”
- “偏好数据够不够纯”
- “收益是否还足够大到值得继续投入”

这也是当前项目最重要的工程学习之一。 
