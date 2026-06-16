# Agent 网关平台 (Project A)

## 架构

```
Client (HTTP/SSE)
  │
  ▼
┌─────────────────────────────────────────┐
│  FastAPI Gateway (server.py)             │  ← 统一入口
├─────────────────────────────────────────┤
│  LangGraph Agent (agent_graph.py)        │  ← 图编排：LLM ↔ Tool → Eval
├────────────┬──────────────┬─────────────┤
│  MCP Tools │  Evaluator   │  Feedback   │  ← 可插拔模块
│  (tools/)  │  (质量门禁)   │  (重试/降级)│
└────────────┴──────────────┴─────────────┘
```

## 五层架构

| 层 | 文件 | 职责 |
|----|------|------|
| Route | `server.py` | HTTP/SSE 入口，路由分发 |
| Agent Graph | `agent_graph.py` | LangGraph 编排 LLM + Tool + Eval 流转 |
| Tools | `tools/` | MCP Server，可独立部署的工具服务 |
| Evaluator | `evaluator.py` | LLM-as-a-Judge 四维度评估 |
| Feedback Loop | `agent_graph.py` 内 | 评估不达标 → 带反馈重试 |

## 后续演进

- [ ] 接入 MCP Client，动态发现工具（替换硬编码 TOOLS）
- [ ] 接入 Langfuse 全链路追踪
- [ ] 接入 E2B/Docker 代码沙箱
- [ ] 多 Agent 协同（Week 4）
