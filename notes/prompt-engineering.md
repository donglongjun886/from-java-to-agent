# Prompt 工程

> Day 3-4 学习笔记（2026-06-09/10）。核心认知：**Prompt 是给 LLM 的编程语言 — 用自然语言写指令，但工程属性完全相同。输入格式决定输出质量。**

---

## 1. Prompt 的本质

### 1.1 三段式结构

```
┌──────────────────────────────┐
│ System Prompt  角色+规则+格式  │  ← 一次定义，全程生效
├──────────────────────────────┤
│ User Message   具体问题/任务   │  ← 每次不同
├──────────────────────────────┤
│ Assistant      模型回复       │  ← 历史记录（多轮对话）
└──────────────────────────────┘
```

| Java 类比 | Prompt 概念 |
|-----------|------------|
| Spring `@Bean` 配置 | System Prompt（定义 Bean 的行为模式） |
| HTTP Request Body | User Message（具体请求参数） |
| Session History | Assistant 历史消息（上下文保持） |

### 1.2 为什么重要

同样的模型，Prompt 好坏能差 2-3 分（5分制）。`evaluator.py` 实验2 的量化结论：

| System Prompt 状态 | overall 得分 |
|-------------------|-------------|
| 无 SP | 4 |
| 简单角色 | 4 |
| **角色+约束+格式** | **5** |

差距不在模型，在 Prompt 设计。

---

## 2. System Prompt 设计

### 2.1 三要素

```
① 角色设定    → "你是资深的软件工程师"
② 行为约束    → "用中文回答，代码用 Markdown 代码块"
③ 输出格式    → "包含代码、复杂度分析、适用场景三部分"
```

三要素**缺一不可**。缺失任一项，对应维度（completeness / format_quality）的评分都会下降。

### 2.2 瘦原则

> System Prompt 不是文档，是约束条件。

```python
# ❌ 太胖：1000 字角色描述 + 50 条规则 → 模型「迷失」，抓不住重点
# ✅ 瘦但准：3-5 句核心约束 → 模型清楚边界，灵活性高
```

经验值：System Prompt 控制在 100-300 字，超过 500 字需要反思是否必要。

### 2.3 量化验证（evaluator.py 实验2）

学习者在 Day 3-4 写了完整的对比实验：同一个问题，三种 System Prompt，用 LLM-as-a-Judge 四维度打分。结论：

- 无 SP → completeness 和 format_quality 拖后腿
- 简单角色 → 有改进但不够
- 角色+约束+格式 → 四个维度均衡高分

**这是 Prompt 工程的核心方法论：不靠感觉，靠打分数据做决策。**

---

## 3. Prompt 工程核心技巧

### 3.1 JSON Mode（结构化输出）

```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[...],
    temperature=0.1,                        # 低温度保证一致性
    response_format={"type": "json_object"}, # 强制 JSON 输出
)
```

适用场景：评估、数据提取、结构化查询。结合低温度（0.1）使用，一致性极高。

### 3.2 Few-shot Prompting（少样本提示）

给模型 2-3 个例子，它就能理解输出格式：

```
请将以下句子翻译成 JSON 格式。

示例1: "张三 25岁 工程师" → {"name": "张三", "age": 25, "job": "工程师"}
示例2: "李四 30岁 设计师" → {"name": "李四", "age": 30, "job": "设计师"}

现在请翻译: "王五 28岁 产品经理"
```

类比：Few-shot ≈ 单元测试的 fixture 数据——用具体例子定义契约。

### 3.3 Chain-of-Thought（CoT，思维链）

让模型「一步步想」而不是直接给答案：

```
❌ "这道题答案是多少？"              → 容易出错
✅ "这道题答案是多少？请一步步推理。"  → 准确率显著提升
```

本质上是用 token 换准确率。复杂推理任务（数学/逻辑/代码）必须开 CoT。

### 3.4 Tool Calling 场景的 Prompt 设计

`tool_calling_demo.py` 的核心经验：

```python
# 工具描述 = Prompt 的一部分
TOOLS = [
    {
        "name": "get_weather",
        "description": "获取指定城市当前的天气信息",  # ← 这就是 Prompt！
        "parameters": {...}
    }
]
```

**Tool 的 `description` 字段是 Prompt 工程的重要部分**：写得好，模型选对工具的概率高；写得模糊，模型会选错。

---

## 4. 评估 Prompt（LLM-as-a-Judge）

### 4.1 四维度框架

`evaluator.py` 中定义的评估体系：

| 维度 | 考察点 | 1分 | 5分 |
|------|--------|-----|-----|
| accuracy | 事实正确性 / 代码能否运行 | 严重错误 | 完全正确 |
| relevance | 是否直接回答问题 | 完全跑题 | 精准命中 |
| completeness | 是否覆盖所有要点 | 严重遗漏 | 全面覆盖 |
| format_quality | 结构 / 格式规范 | 混乱 | 优秀 |

### 4.2 评估 Prompt 的设计要点

```python
EVALUATOR_SYSTEM_PROMPT = """你是一个严格的技术评审专家。

评分规则：
1. 对每个维度给出 1-5 的整数分数
2. 每个分数必须有具体理由，引用回答中的原文作为证据  ← 防止「瞎打分」
3. 输出必须是严格的 JSON 格式                        ← 结构化保证可解析

输出 JSON 格式：{"accuracy": {...}, "relevance": {...}, ...}
"""
```

关键设计：
- **温度=0.1** → 保证评分一致性（实验3 验证：两次评估偏差为 0）
- **要求引用原文** → 防止 LLM 随便给分
- **`response_format={"type": "json_object"}`** → 保证输出可解析

### 4.3 评估一致性验证

学习者在 `evaluator.py` 实验3 中验证了：温度 0.1 下，同一个回答评两次，四个维度分数偏差为 0。这说明：
- 评估 Prompt 的设计是有效的
- 低温度 + 明确维度定义 = 可复现的自动化评估

类比：评估 Prompt ≈ 单元测试的 assert——定义什么是「对」，且每次运行结果一致。

---

## 5. 常见反模式

| 反模式 | 后果 | 正确做法 |
|--------|------|---------|
| Prompt 太长（>1000字） | 模型抓不住重点，忽略关键约束 | 精简到核心 3-5 条约束 |
| 指令冲突 | System 说用中文，User 说用英文→模型困惑 | 分层清晰：System 管格式，User 管内容 |
| 过度约束 | 模型死板，失去灵活处理能力 | 约束精确但不泛滥 |
| 把 Prompt 当数据库 | 把大量业务规则塞进 System Prompt | 规则放 Tool/MCP，Prompt 只管调用 |
| 温度=0 用于创意任务 | 输出千篇一律 | 创意类用 0.7-0.9，事实类/评估类用 0-0.3 |

---

## 6. 核心 Takeaway

1. **Prompt 是 LLM 的编程语言** — System Prompt = 类定义，User Message = 方法参数
2. **角色+约束+格式三要素** — 缺一不可，量化实验已验证
3. **用数据驱动 Prompt 优化** — 不是「感觉更好」，是「分数更高」
4. **低温度 + JSON Mode = 评估一致性** — 可做自动化回归测试
5. **Tool description 也是 Prompt 工程** — 决定了模型能不能选对工具

---

## 7. 自测

1. 一个客服 Agent 的 System Prompt 应该包含哪些要素？
2. 为什么评估 Prompt 的温度要设为 0.1 而不是 0.7？
3. 如何验证 Prompt 改进是否有效？（答：A/B Baseline 四维度量化对比）
4. Tool Calling 中，Tool 的 `description` 字段为什么属于 Prompt 工程的一部分？