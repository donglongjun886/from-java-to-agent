# Week 1 复盘（2026.06.05 - 2026.06.11）

## 1. 这周学到了什么？

| 天 | 知识块 | 核心收获 |
|----|--------|---------|
| Day 1 | Python 速通 | asyncio、list comprehension、类型系统，用 Java 类比快速上手 |
| Day 2 | Pydantic + LLM 概念 | BaseModel/Field ≈ Lombok+Jackson；Token/Temperature/Context Window 三件套 |
| Day 3 | Chat API + Agent 架构 | Chat Completions 协议层、SSE 流式机制、Agent = Model + Harness + Feedback Loop |
| Day 4 | LLM-as-a-Judge 评估 | 四维度打分框架、Feedback Loop 集成、A/B Baselining |
| Day 5 | Tool Calling + 整合 | 模型自主调用决策、6 个模块整合成完整 Agent |

**6 个 Python 文件**：chat_api_basics.py / agent_skeleton.py / evaluator.py / agent_with_feedback.py / tool_calling_demo.py / hello_agent_complete.py

## 2. 和 Java 生态比，AI Agent 开发的核心差异是什么？

| 维度 | Java 后端 | AI Agent |
|------|----------|----------|
| 系统边界 | 调确定的 API / DB | 调**不确定的** LLM，输出不保证正确 |
| 测试方式 | assert 预期值 | 用 LLM 评估 LLM（Judge 模式） |
| 重试逻辑 | 同请求重试，等网络恢复 | **带反馈重试**，告诉模型上次哪里不好 |
| 工具集成 | 代码直接调方法 | 模型**自主决定**调哪个工具、传什么参数 |
| 状态管理 | DB + Redis | messages 数组 + 短期/长期记忆分治 |
| 核心瓶颈 | QPS / P99 延迟 / 数据一致性 | Token 成本 / Context Window / 幻觉 |

**最大认知升级**：Agent 开发不是"调 API + 写 Prompt"，而是**为不确定的模型建一套确定性的工程框架**——这就是 Harness 的意义。

## 3. 下周需要调整什么？

| 调整 | 状态 |
|------|------|
| 加 Tool Calling 到 Day 5 | ✅ 已完成 |
| 计划 v5→v6（LlamaIndex/FastAPI/Agent 安全） | ✅ 已更新 |
| `notes/harness-fundamentals.md` 还没写 | 下周补上 |
| 晚段 Spring AI 只做了一次 | 下周保持节奏 |

### 下周重点

Week 2 进入 **LangGraph 编排 + MCP 协议 + FastAPI 服务化 + Agent 安全**，从"单 Agent 对话"进化到"带图编排的多工具 Agent 网关"。

## 代码产出

- [x] `chat_api_basics.py` — Chat API 三实验
- [x] `agent_skeleton.py` — System Prompt 三态 + Agent 骨架
- [x] `evaluator.py` — LLM-as-a-Judge 四维度评估
- [x] `agent_with_feedback.py` — Feedback Loop + A/B Baselining
- [x] `tool_calling_demo.py` — Tool Calling 概念初体验
- [x] `hello_agent_complete.py` — Week 1 整合产出
- [ ] `notes/harness-fundamentals.md`

*记录日期：2026-06-11*
