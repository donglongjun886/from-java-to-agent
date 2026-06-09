# Day 3 (2026.06.09) — LLM API + Agent 概念

## 第一部分：Chat Completions API 核心 ✅

### 资源阅读
- **DeepSeek API 文档**：Chat Completions 端点
- **OpenAI Chat API 文档**：Create chat completion → Request body 参数表 + Streaming 小节

### 核心认知

**Chat Completions API 本质**：无状态 HTTP POST，每次请求都要把完整对话历史带上。模型本身不记任何上下文——这就是为什么 messages 数组越来越长、Context Window 是稀缺资源。

**流式 vs 非流式**：
| | 非流式 (stream=false) | 流式 (stream=true) |
|---|---|---|
| object 类型 | `chat.completion` | `chat.completion.chunk` |
| 内容字段 | `message.content`（全量） | `delta.content`（增量） |
| 首个 chunk | — | 只有 role，无 content |

**关键参数速查**：
- `temperature`: 0=确定（代码/分类），0.7=平衡（对话），1.5=发散（创意）
- `max_tokens`: 不设会被长回复吃光预算
- `finish_reason`: `stop`=正常 / `length`=被截断 / `content_filter`=内容过滤

### 代码产出
- `projects/01-hello-agent/chat_api_basics.py`：三个实验全部跑通
  - 实验1：拆解完整 response JSON 结构（id/choices/finish_reason/usage/费用）
  - 实验2：观察 67 个 SSE chunk 的形态（delta vs message、首个 chunk 只宣告 role）
  - 实验3：temperature=0 vs 1.5 同 prompt 对比

### 发现
- `deepseek-chat` 实际路由到 `deepseek-v4-flash`，服务端可能做了映射

---

## 第二部分：System Prompt + Agent 架构 ✅

### 资源阅读
- **OpenAI Prompt Engineering 指南**：Six strategies for getting better results
- **Anthropic Context Engineering**：System prompts + Context windows 两节

### 核心认知

**System Prompt 三重作用**：
1. 角色设定：「你是资深 Java 架构师」
2. 行为约束：「只回答技术问题」
3. 输出格式：「用 Markdown 格式，分三部分」

**System Prompt 应该瘦**（Harness 工程核心认知）：
- 传统做法：把所有指令塞进 system prompt → 越来越长，模型对中间部分「耳旁风」
- Harness 做法：核心规则放 system prompt（~200 字），约束下沉到 Tool/代码层，知识放文件系统

**Agent = Model + Harness + Feedback Loop**：
| 层 | 职责 | Java 类比 |
|---|---|---|
| Model | 推理/生成 | 数据库引擎 |
| Harness | 工具/记忆/沙箱/上下文/可观测 | Spring Framework |
| Feedback Loop | 重试/外部验证/人工审核 | CI/CD Pipeline |

**关键洞察**：Model 是同质化的，真正拉开差距的是 Harness 层的工程质量——和 Java 生态里「框架选型比语言更重要」同一逻辑。

### 代码产出
- `projects/01-hello-agent/agent_skeleton.py`：两个实验全部跑通
  - 实验A：同一问题 × 三种 System Prompt 对比，验证输出可控性
  - 实验B：AgentSkeleton 类体现三层架构，retry loop / stats / context reset 就绪

### 三态对比结论
| | 无 System Prompt | 简单角色 | 角色+约束+格式 |
|---|---|---|---|
| 结构 | 自发展开多种实现 | 同左 | 聚焦一种实现深度展开 |
| 线程安全 | 顺带提 | 顺带提 | 独立一节专门分析 |
| 防御性 | 无 | 无 | 加了反射攻击防御 |

---

## 第三部分：Tokenizer 工具实测 ✅

### 实测数据（cl100k_base 编码）

| 文本类型 | 字符数 | Token 数 | 比率 |
|----------|--------|----------|------|
| 中文 50字 | 64 | 85 | 1 token ≈ 0.75 中文字符 |
| 中文 200字 | 175 | 231 | 1 token ≈ 0.76 中文字符 |
| 中文 500字 | 400 | 525 | 1 token ≈ 0.76 中文字符 |
| 英文 | 43 | 12 | 1 token ≈ 3.6 英文字符 |

**单条消息有 4 个固定 overhead token**（role + 格式标记）。

### 生产速算公式

```
中文 token 估算: 字符数 × 0.75
英文 token 估算: 字符数 × 0.28
典型对话: content tokens + 消息数 × 4 (overhead)
精确计算: API response.usage.prompt_tokens 或 tiktoken 本地算
```

### 3 个 commit
```
a5f6ddb feat(hello-agent): Day 3 Part2 — System Prompt 三态对比 + Agent 架构骨架
864d266 feat(hello-agent): Day 3 Part1 — Chat Completions API 三实验
```