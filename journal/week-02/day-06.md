# Day 6 (2026.06.12) — LangGraph 入门 + Tool Use

## Part 1: LangGraph 核心概念 ✅

### 资源
- LangGraph Quick Start + 核心概念文档（StateGraph / Node / Edge / Conditional Edge）
- Checkpointing 简介

### 核心认知

**LangGraph ≈ Flowable BPMN**：用图编排替代手写 if-else。

| 概念 | 作用 | Java 类比 |
|------|------|-----------|
| StateGraph | 定义 Agent 的状态结构和流转图 | ProcessDefinition |
| Node | 图中的执行单元（调 LLM、调工具） | BPMN Service Task |
| Edge | 固定连线（A 完了一定走 B） | Sequence Flow |
| Conditional Edge | 根据状态判断走哪个分支 | BPMN Gateway |
| State | 节点间共享数据 | Process Variables |
| Checkpointer | 自动保存状态，支持断点续传 | Saga 事务日志 |
| `operator.add` | 消息追加不覆盖 | 类似 List.addAll() |

**关键认知**：
- `Annotated[list, operator.add]` 是 LangGraph 的核心设计——消息不是替换，是追加
- 条件路由函数替代了手写 if-else：代码只负责判断"往哪走"，图引擎负责流转
- `Literal["tool_node", END]` 类型约束让 IDE 能自动补全和校验

### 待做
- Part 2: `langgraph_agent.py` — 用 LangGraph 重写 tool_calling 流程
