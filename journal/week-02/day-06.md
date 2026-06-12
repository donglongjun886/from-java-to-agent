# Day 6 (2026.06.12) — LangGraph 入门 + Tool Use

## Part 1: LangGraph 核心概念 ✅

### 资源
- LangGraph Quick Start + 核心概念文档（StateGraph / Node / Edge / Conditional Edge + Checkpointing）

### 核心认知

**LangGraph ≈ Flowable BPMN**：用图编排替代手写 if-else。

| 概念 | 作用 | Java 类比 |
|------|------|-----------|
| StateGraph | Agent 状态结构和流转图 | ProcessDefinition |
| Node | 图中执行单元 | BPMN Service Task |
| Edge | 固定连线 | Sequence Flow |
| Conditional Edge | 根据状态分支路由 | BPMN Gateway |
| State | 节点间共享数据 | Process Variables |
| Checkpointer | 自动保存状态、断点续传 | Saga 事务日志 |
| `operator.add` | 消息追加不覆盖 | List.addAll() |

## Part 2: LangGraph 代码实战 ✅

### 产出
- `langgraph_agent.py` — 用 LangGraph 重写 tool_calling_demo 的流控逻辑
- 三实验全部跑通

### 手写 vs 图编排对比

| | tool_calling_demo（手写） | langgraph_agent（图） |
|---|---|---|
| messages 拼接 | 手动 append | add_messages 自动追加 |
| 流程控制 | if-else 写死 | router() + 图引擎流转 |
| 工具循环 | for tc in msg.tool_calls | call_tool 节点自动执行 |
| 可扩展 | 加步骤 = 改代码 | 加步骤 = add_node + add_edge |

### 关键设计
- `@tool` 装饰器替代手写 JSON Schema（get_weather / calculate）
- `model.bind_tools(TOOLS)` 绑定工具集
- `ToolMessage` + `tool_call_id` 替代手拼 dict

### 1 个 commit
```
7af5e0a feat(hello-agent): Day 6 Part2 — LangGraph 重写 Tool Calling
```
