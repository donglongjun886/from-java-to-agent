# Tool Calling + MCP + A2A

> Day 5-8 学习笔记（2026-06-11/16）。核心认知：**Tool Calling 是 Agent 从「聊天」到「干活」的质变点；MCP 让工具从硬编码变成可插拔的服务。**

---

## 1. Tool Calling（Function Calling）

### 1.1 核心原理

**模型不执行工具，只输出「我要调哪个工具 + 什么参数」。** Client 负责真正执行。

```
User: "杭州天气怎么样？"
  → LLM 输出: tool_calls=[{name:"get_weather", args:{city:"杭州"}}]
    → Client 执行: 查数据库 → "晴，28°C"
      → 结果回传 LLM: "杭州今天晴，28°C，湿度65%"
        → LLM 总结: "杭州今天晴天，28°C，适合出门。"
```

| 传统编程 | Tool Calling |
|---------|-------------|
| 代码写死 `if (msg.contains("天气")) callWeather()` | 模型自主判断要不要调工具 |
| 参数从正则提取 | 模型从语义中提取并结构化 |
| 单工具，硬编码路由 | 多工具，模型自主选择 |

### 1.2 三个实验（tool_calling_demo.py）

| 实验 | 用户输入 | 模型行为 | 关键认知 |
|------|---------|---------|---------|
| 1-单工具 | "杭州天气" | 提取 city="杭州"，调 get_weather | 参数从自然语言自动提取 |
| 2-需vs不需 | "你好" vs "天气" | 前者不调，后者调 | 模型知道什么时候需要工具 |
| 3-多工具选择 | "天气"/"计算" | 模型选对工具 | 多工具场景下自主路由 |

### 1.3 工具注册

```python
# 方式1: 硬编码（tool_calling_demo.py）
TOOLS = [{
    "name": "get_weather",
    "description": "获取指定城市当前的天气信息",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "城市名"}},
        "required": ["city"],
    },
}]

# 方式2: @tool 装饰器（langgraph_agent.py）
@tool
def get_weather(city: str) -> str:
    """获取指定城市当前的天气信息"""
    ...

model_with_tools = model.bind_tools([get_weather, calculate])
```

| Java 类比 | Tool 概念 |
|-----------|----------|
| Interface 定义 | Tool Schema（name + parameters） |
| `@Service` 实现类 | Tool 实现函数 |
| `ApplicationContext.getBean(name)` | dispatch（按 name 查工具） |
| Feign Client | MCP Client（远程调用） |

### 1.4 LangGraph 中的 Tool 路由

`langgraph_agent.py` 用图编排替代手写 if-else：

```python
# 手写版（tool_calling_demo.py）:
if response.choices[0].message.tool_calls:
    for tc in tool_calls:
        result = execute(tc)
    messages.append(result)
    # 再调一次 LLM...

# LangGraph 版（langgraph_agent.py）:
graph.add_conditional_edges("llm", router, {"tool": "tool", END: END})
graph.add_edge("tool", "llm")  # 自动循环
```

`router()` 函数就是整个 Tool 调用的决策枢纽。

---

## 2. MCP 协议（Model Context Protocol）

### 2.1 定位

MCP 是连接 **LLM 与外部工具/数据** 的开放标准协议，由 Anthropic 提出，2026 年已成为 AI Agent 生态的事实标准。

```
┌──────────┐    MCP 协议     ┌──────────────┐
│ MCP Client │ ←───────────→ │  MCP Server   │
│ (Agent)    │   Tools       │  (工具提供方)  │
│            │   Resources   │               │
│            │   Prompts     │               │
└──────────┘                └──────────────┘
```

### 2.2 三原语

| 原语 | 作用 | 类比 |
|------|------|------|
| **Tools** | 可调用的工具（LLM 可以决定执行） | REST API endpoint |
| **Resources** | 数据资源（LLM 可以读取） | 数据库表 / 文件 |
| **Prompts** | 提示模板（预定义的 Prompt） | 配置文件 |

### 2.3 传输层

| 传输方式 | 适用场景 | 特点 |
|---------|---------|------|
| **stdio** | 本地进程通信 | 简单，Client 启动 Server 作为子进程 |
| **HTTP + SSE** | 远程服务通信 | 支持多 Client 连接，适合生产环境 |

### 2.4 实际代码（mcp_weather_server.py）

```python
# MCP Server 端
server = Server("weather-mcp-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="get_weather", description="...", inputSchema={...})]

@server.call_tool()
async def call_tool(name, arguments):
    if name == "get_weather":
        return [TextContent(type="text", text=f"晴，28°C")]

# 启动（stdio 传输）
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, ...)
```

**架构对比：**

| | Tool Calling（硬编码） | MCP Server |
|---|---|---|
| 工具定义 | 写在 Agent 代码里 | 独立进程/服务 |
| 部署 | 和 Agent 一起 | 独立部署 |
| 复用 | Agent 专属 | 多个 Agent 共享 |
| 升级 | 改 Agent 代码 | 改 Server 代码，Agent 无感知 |

**关键认知**：MCP 把工具从「硬编码在 Agent 代码里」升级为「独立部署的服务」。类比：硬编码 Tool ≈ `@Service` 内部类；MCP Server ≈ 独立微服务。

---

## 3. A2A 协议（Agent-to-Agent）

### 3.1 定位

A2A 是连接 **Agent 与 Agent** 的协议。MCP 让 Agent 能调工具，A2A 让 Agent 能调 Agent。

```
         MCP                          A2A
  Agent ←──→ Tool               Agent ←──→ Agent
  (1对1)                        (多对多)
```

### 3.2 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| **Agent Card** | Agent 的能力声明（我能做什么） | Swagger / OpenAPI Spec |
| **Task** | 任务对象（有状态、可追踪） | 异步任务 / Job |
| **Message** | Agent 间通信消息 | RPC Request/Response |

### 3.3 成熟度判断

| | MCP | A2A |
|---|---|---|
| 协议版本 | 稳定（2024.11 发布） | v0.3→v1.0（2026 演进中） |
| GitHub Stars | 83,500+ | 生态 ~200 Agent |
| 生产案例 | 大量（Claude Code/Cursor 等） | 较少 |
| 技术文章提及率 | ~10%（快速上升） | 极低 |
| **学习优先级** | ⭐⭐⭐ | ⭐（半天认知即可） |

**学习顺序正确**：先 MCP 后 A2A。MCP 是基座（Agent 要有工具能力），A2A 是进阶（Agent 之间需要协作时才需要）。

---

## 4. 三者对比总结

| | Tool Calling | MCP | A2A |
|---|---|---|---|
| **连接对象** | LLM ↔ 工具 | LLM ↔ 工具（标准化） | Agent ↔ Agent |
| **标准化** | 无（各家 API 不同） | 开放标准 | 开放标准 |
| **部署方式** | 硬编码 | 独立 Server 进程 | 独立 Agent 服务 |
| **类比** | 直接调本地方法 | REST API（HTTP 标准） | gRPC（服务间通信） |
| **成熟度** | 成熟 | 成熟（事实标准） | 早期（v1.0 刚稳定） |
| **学习时间** | 1 天 | 1-2 天 | 半天 |

### 架构演进路径

```
阶段1: 硬编码 Tool Calling  →  快速原型，工具少时够用
阶段2: MCP Server 化        →  工具独立部署，多 Agent 复用
阶段3: A2A Agent 协作       →  多 Agent 系统，Agent 间任务委派
```

---

## 5. 核心 Takeaway

1. **Tool Calling 是质变点** — 没有工具，Agent 只能聊天；有了工具，Agent 能干活
2. **MCP ≈ USB-C 协议** — 统一标准，插上就能用。工具提供方和消费方解耦
3. **MCP Server ≈ 微服务** — 独立部署、独立升级、多 Agent 共享
4. **A2A 优先级低于 MCP** — MCP 是基座，A2A 是进阶。先学会调工具，再学会调 Agent
5. **`@tool` 装饰器 + `bind_tools()` + `router()`** 是 LangGraph 下 Tool 系统的三个核心组件

---

## 自测

1. Tool Calling 中，模型做的是什么？Client 做的是什么？
2. MCP 的三个原语（Tools/Resources/Prompts）分别解决什么问题？
3. MCP 的 stdio 和 HTTP+SSE 两种传输方式分别适用什么场景？你的 `mcp_weather_server.py` 用的是哪种？
4. 什么情况下需要 A2A？为什么当前阶段「半天认知」就够？