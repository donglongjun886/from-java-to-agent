# Day 7 (2026.06.15) — MCP 协议深度 + FastAPI 服务化

## Part 1: MCP 核心概念 ✅

### 资源
- MCP 协议规范（Introduction + Core Architecture）
- FastMCP 文档 Quickstart
- MCP 官方 Python SDK README

### 核心认知
- MCP 三原语：Tools（执行动作）、Resources（读取数据）、Prompts（提示词模板）
- Transport：stdio（本地子进程）+ HTTP+SSE（远程服务）
- MCP ≈ 工具系统的 SPI 机制：加工具不需要改 Agent 代码

## Part 2: MCP 代码实战 ✅

### 产出
- `mcp_weather_server.py`：把 get_weather+calculate 抽成独立 MCP Server
- 支持 stdio 和 HTTP+SSE 两种 transport

### 关键设计
- `@app.list_tools()` 返回工具菜单
- `@app.call_tool()` 执行具体工具
- `run_stdio()` 供 IDE/CLI 本地调用
- `run_http()` 供 Agent HTTP 远程调用

## Part 3: FastAPI 服务化 ✅

### 产出
- `agent_api.py`：把 Agent 暴露为 HTTP 服务
- `/chat` — 非流式（JSON 返回）
- `/chat/stream` — SSE 流式
- `/stats` — 统计端点

### 关键设计
- Tool Calling 完整链路通过 HTTP 实现
- `/docs` 自动生成 Swagger 文档
- 为项目 A Agent 网关打底

### 2 个 commit
```
b2ca754 feat(hello-agent): Day 7 Part3 — FastAPI 服务化 Agent
9622f6f feat(hello-agent): Day 7 Part2 — MCP 协议实战
```
