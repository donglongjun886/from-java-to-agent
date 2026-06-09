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

## 第二部分：System Prompt + Agent 架构 🚧

（待完成）