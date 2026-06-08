# LLM 基础概念

> Day 2 学习笔记（2026-06-08）。从 Java 后端视角理解 LLM 三个核心概念：Token / Temperature / Context Window。

---

## 1. Token：LLM 的「计费单位」

### 1.1 是什么

LLM 不直接处理「字」或「词」，处理的是 **token**——通过 BPE（Byte Pair Encoding）算法把文本切成的一个个整数 ID。

```python
# 直观对比
"你好世界"      → [60802, 97268, 100603]    # 4 汉字 = 4 token（部分模型 6+）
"Hello world"   → [15339, 1917]              # 2 单词 = 2 token
"def foo():"    → [68, 1985, 383, 869, 26]   # 代码 = 拆得更碎
```

### 1.2 关键经验值

| 内容 | Token 数 | 备注 |
|------|---------|------|
| 1 个英文字母 | ≈ 0.25 | 拼成单词后分摊 |
| 1 个英文单词 | ≈ 1.3 | 高频词可能 1 token，低频词拆成 2-3 |
| **1 个汉字** | **≈ 1.5-2** | **反直觉：比英文「费」** |
| 1 个中文标点 | ≈ 1 | 句号、逗号各占 1 |
| 1 行 Python 代码 | ≈ 10-20 | 比自然语言碎 |

> **速记公式**：1 万字中文 ≈ 1.5-2 万 token

### 1.3 为什么中文「费」token

直觉是「汉字信息密度高，应该省 token」—— **错**。BPE 按字节对频率切，不管语义密度：

- 英文 "concatenate" → 拆成 `[concat]` + `[enate]`，**1 个长词共享 1 个 token**
- 中文「连接」 → 「连」+「接」**两字各占 1 个 token**，没有共享

类比 Java：`String.intern()` 把重复字符串池化，tokenizer **不会做这种事**。

### 1.4 成本计算

```python
def estimate_cost(input_chars: int, output_chars: int,
                  input_price: float, output_price: float,
                  is_chinese: bool = True) -> float:
    """估算 LLM 调用成本（元）"""
    # 关键参数：1 个汉字 = 1.5 token，1 个英文单词 = 1.3 token
    ratio = 1.7 if is_chinese else 0.3
    input_tokens = input_chars * ratio
    output_tokens = output_chars * ratio
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000
```

**DeepSeek V3 单价**（参考）：
- input: 2 元/百万 token
- output: 8 元/百万 token

```python
# 客服 Agent 单次成本
cost = estimate_cost(500, 300, 2, 8)  # 500字输入，300字输出
# ≈ 0.0058 元 ≈ 6 厘
```

### 1.5 实战工具

- **OpenAI Tokenizer**: https://platform.openai.com/tokenizer —— 浏览器里直接玩
- **tiktoken**（Python 库）：精确统计 OpenAI 系模型的 token 数
- **DeepSeek 自带 tokenizer**（API 返回的 `usage` 字段）

```python
response = client.chat.completions.create(...)
print(response.usage)
# CompletionUsage(prompt_tokens=850, completion_tokens=510, total_tokens=1360)
```

---

## 2. Temperature：控制「随机性」

### 2.1 是什么

LLM 每一步其实是在所有候选 token 上**算一个概率分布**，然后按这个分布**抽样**。Temperature 就是调节这个分布「平」或「尖」的超参数：

```
temperature = 0   →  几乎只选概率最高的 token（确定性）
temperature = 1   →  按原始分布抽样（平衡）
temperature = 2   →  分布被「拉平」，小概率 token 也有机会（发散）
```

### 2.2 参数对照

| 参数 | 范围 | 默认 | 作用 |
|------|------|------|------|
| `temperature` | 0 - 2 | 1 | 控制**随机性强度** |
| `top_p` | 0 - 1 | 1 | **核采样**：只从概率累计到 p 的 token 里选 |
| `max_tokens` | > 0 | 模型上限 | 单次输出最大 token 数 |
| `response_format` | — | — | 强制输出 JSON（结构化输出关键） |

> **temperature 和 top_p 二选一调**，不要同时拉满（会变得难以预测）。

### 2.3 经验法则

| 场景 | temperature | 原因 |
|------|------------|------|
| 代码生成 | 0 | 错一个字符就编译失败 |
| 工具调用 / JSON | 0 | 必须可解析 |
| SQL 生成 | 0 | 同上 |
| 翻译 / 摘要 | 0.2 - 0.3 | 准确为主 |
| 客服对话 | 0.5 - 0.7 | 平衡准确和自然 |
| 创意 / 营销文案 | 0.7 - 1.0 | 需要发散 |
| Brainstorm | 1.0 - 1.5 | 越意外越好 |

### 2.4 Java 类比

把 LLM 调用想象成**带随机种子的单元测试**：

```java
// temperature = 0 ≈ 用固定 seed，每次结果完全相同
Random rng = new Random(42);

// temperature = 1 ≈ 每次 seed 不同，结果可能不一样
Random rng = new Random();  // 用时间戳当 seed
```

> **关键洞察**：`temperature=0` 解决的是「可复现性」问题，**不是**「正确性」问题。模型不知道的事，再低的 temperature 也会胡编。

### 2.5 SQL Agent 完整防御链

```python
# temperature=0 只是第一步，完整防御链：
1. temperature=0           # 可复现
2. system prompt 贴 schema # 模型知道有哪些表/字段
3. response_format=json    # 输出可解析
4. Pydantic model_validate # 结构校验
5. EXPLAIN / dry-run       # 语法 + 权限校验
6. 失败重试 + 错误回传     # 自我修正
```

---

## 3. Context Window：模型的「工作记忆」

### 3.1 是什么

模型**单次调用**能处理的「输入 + 输出」总 token 数。**不是存储**，是**临时记忆**——调用结束就清空。

类比 Java：**栈帧大小**。超过就 `StackOverflowError`，没超过也得注意别用太多。

### 3.2 主流模型窗口

| 模型 | Context Window | 备注 |
|------|---------------|------|
| DeepSeek V3 | 64K | 性价比首选 |
| Claude Sonnet 4.6 | 200K | 主力工具调用 |
| Claude Opus 4.7 | 200K | 复杂任务 |
| GPT-5 (假设) | 400K+ | 参考 |

> **1K = 1000，1M = 100万**。200K 约等于 **15 万字中文**或 **30 万英文单词**。

### 3.3 成本是「双倍」的

Context Window 影响**两边**：

```
总成本 = (input_tokens + output_tokens) × 单价
              ↑                ↑
              占大头的输入       也在涨
```

把一个 50K token 的文档反复问 10 次 ≠ 50K token 成本，而是 **10 × 50K**。

### 3.4 「Lost in the Middle」现象

模型对**长 Context 开头和结尾**的内容注意力强，**中间部分**容易忽略。

```python
# 实验发现：把关键信息放在 prompt 中间，准确率显著下降
prompt = """
[无关背景... 5K tokens]
[关键问题在这里]        ← ← ← 模型可能忽略
[无关背景... 5K tokens]
"""
```

**工程对策**：
- 关键信息放**开头**或**结尾**
- 长 Context 用**摘要**而不是原文
- 多轮对话时**滚动压缩**前面的历史

### 3.5 Context Window vs 训练数据

| 概念 | 含义 | 比喻 |
|------|------|------|
| 训练数据截止 | 模型知道哪些「旧」信息 | 你的「学历」 |
| Context Window | 单次能处理多少信息 | 你的「工作记忆」 |
| 微调 / RAG | 给模型「补课」 | 给你发参考资料 |

模型**不知道**自己训练截止后发生的事，但你可以**把新信息塞进 Context Window** 让它临时知道。

---

## 4. 三个核心 takeaway

1. **汉字 ≈ 1.5-2 token**：成本估算别拍脑袋，中文比英文「费」token。
2. **temperature=0 不等于正确**：只是「可复现」，真要稳还得配合 schema + 格式 + 校验。
3. **Context Window = 钱 + 性能 + 准确性**：超过报错，接近上限准确率下降，关键信息别放中间。

---

## 5. Day2 验收题（自测）

### Q1：500 字中文 ≈ 多少 token？成本多少？

```
1 汉字 ≈ 1.7 token（中位数）
500 字 ≈ 850 token（输入）

输出 300 字 ≈ 510 token

单次成本：
  input  = 850 × 2/1,000,000  = 0.0017 元
  output = 510 × 8/1,000,000  = 0.0041 元
  合计 ≈ 0.0058 元（≈ 6 厘）

日活 1 万 × 5 轮/天：
  日成本 ≈ 290 元
  月成本 ≈ 8700 元
```

**关键洞察**：单次 6 厘看似便宜，乘以高频次后**轻松破万**。架构层必须做缓存和降级。

### Q2：SQL Agent 用哪个 temperature？

```
答：temperature = 0
原因：
  - 同样 prompt 永远输出同样 SQL（可复现）
  - 减少随机编造表名/字段名的概率
但 temperature=0 只是第一步：
  - 还要在 system prompt 里贴完整 schema
  - 用 response_format={"type": "json_object"} 强制 JSON
  - 用 Pydantic 校验输出结构
  - 用 EXPLAIN 验证 SQL 语法
```

### Q3：Pydantic V2 model_validate 失败原因？

```python
class Order(BaseModel):
    order_id: int
    amount: float
    currency: str = "CNY"

raw = '{"order_id": "12345", "amount": "99.5", "currency": 100}'
order = Order.model_validate(json.loads(raw))
```

**实际行为：不会报错**，Pydantic V2 默认 **lax 模式**会默默强转：

| 字段 | 输入 | 强转结果 |
|------|------|---------|
| `order_id` | `"12345"` (str) | → `12345` (int) ✓ |
| `amount` | `"99.5"` (str) | → `99.5` (float) ✓ |
| `currency` | `100` (int) | → `"100"` (str) ✓ |

**要触发严格校验**：

```python
class Order(BaseModel):
    model_config = ConfigDict(strict=True)   # ← 开启严格
    order_id: int
    amount: float
    currency: str = "CNY"
```

**关键洞察**：Pydantic V2 默认行为**不是** Java 强类型哲学，而是 JavaScript 的宽松哲学。需要严格校验时**显式开 strict**。

---

## 6. 待补充（Day3+ 涉及）

- [ ] System Prompt 工程细节
- [ ] 流式响应（SSE）原理
- [ ] Token 限流与速率控制（Rate Limiting）
- [ ] Prompt 缓存策略

---

*最后更新：2026-06-08（Day 2）*
*配套资料：[OpenAI Tokenizer](https://platform.openai.com/tokenizer) | [DeepSeek API 文档](https://platform.deepseek.com/api-docs/) | [Anthropic Context Engineering](https://docs.anthropic.com/en/docs/build-with-claude/context-engineering)*
