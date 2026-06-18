# Agent Gateway 架构设计

> 项目A：基于 LangGraph + MCP + FastAPI 的多工具 Agent 网关

## 一、系统架构

```mermaid
graph TB
    subgraph "客户端"
        CLI[CLI / curl / 浏览器]
    end

    subgraph "Agent Gateway (FastAPI :9090)"
        API["FastAPI 路由层<br/>POST /chat · /chat/stream · /stats"]
        G1["guard_input()<br/>注入检测 + Unicode NFKC"]
        G2["guard_tool()<br/>危险操作拦截"]
        G3["guard_output()<br/>脱敏替换"]
        CB["CircuitBreaker<br/>超时重试 + 指数退避 + 冷却"]
    end

    subgraph "LangGraph 编排引擎"
        direction TB
        LLM["llm_node<br/>调用 DeepSeek API"]
        TOOL["tool_node<br/>工具执行调度"]
        EVAL["eval_node<br/>LLM-as-a-Judge 四维评分"]
        ROUTER{"条件路由<br/>需工具? → tool<br/>不需要? → eval"}
    end

    subgraph "工具层"
        MCP_C["MCP Client<br/>stdio 子进程"]
        LOCAL["本地工具<br/>sandbox.execute_code_tool"]
    end

    subgraph "外部"
        DS["DeepSeek API<br/>deepseek-chat"]
        MCPS["Python MCP Server<br/>get_weather / calculate"]
    end

    subgraph "可观测"
        STATS["Stats 收集器<br/>calls / tokens / time / eval"]
    end

    CLI -->|HTTP| API
    API --> G1
    G1 --> CB
    CB --> LLM
    LLM --> ROUTER
    ROUTER -->|tool_call| TOOL
    ROUTER -->|无工具| EVAL
    TOOL --> MCP_C
    TOOL --> LOCAL
    MCP_C -->|stdin/stdout| MCPS
    EVAL --> G3
    G3 --> API
    TOOL --> LLM
    CB -.- STATS
    EVAL -.- STATS
    TOOL -.- STATS
    G1 -.- G2 -.- G3
```

## 二、核心链路时序图

### POST /chat 同步调用

```mermaid
sequenceDiagram
    actor C as 客户端
    participant API as FastAPI
    participant G1 as guard_input
    participant CB as CircuitBreaker
    participant LLM as llm_node
    participant R as Router
    participant T as tool_node
    participant MCP as MCP Client
    participant P as Python MCP Server
    participant E as eval_node
    participant G3 as guard_output
    participant S as Stats

    C->>API: POST /chat {"msg":"杭州天气"}
    API->>G1: 输入安全检测
    G1->>CB: 通过
    CB->>LLM: messages [System + History + User]
    LLM->>DS: API 调用 (≈2.6s)
    DS-->>LLM: tool_call: get_weather("杭州")
    LLM->>R: 决策: 走 tool 分支
    R->>T: tool_node
    T->>MCP: call_tool("get_weather", {"city":"杭州"})
    MCP->>P: JSON-RPC via stdio
    P-->>MCP: "杭州：晴，28°C"
    MCP-->>T: 工具结果
    T->>LLM: 工具结果 + 继续生成
    LLM->>DS: API 再次调用 (≈2.6s)
    DS-->>LLM: "杭州今天晴，28°C..."
    LLM->>R: 决策: 结束
    R->>E: eval_node
    E->>DS: 评估 API 调用
    DS-->>E: {"overall":5, "accuracy":5, ...}
    E->>G3: 输出安全检测
    G3->>S: 记录 stats
    S-->>API: 脱敏后回复
    API-->>C: {"reply":"杭州今天晴，28°C...","time_ms":5200,...}

    Note over C,API: 总耗时: ~5.2s (2次LLM + 1次MCP)
```

### POST /chat/stream SSE 流式

```mermaid
sequenceDiagram
    actor C as 客户端
    participant API as FastAPI
    participant LLM as llm_node
    participant BUF as 缓冲器

    C->>API: POST /chat/stream {"msg":"你好"}
    API->>LLM: astream_events()
    loop 逐 token
        LLM-->>BUF: token chunk
        BUF-->>BUF: 缓冲累积
        BUF-->>API: EventSourceResponse 推送
        API-->>C: SSE data: "你"
        API-->>C: SSE data: "好"
        API-->>C: SSE data: "！"
    end
    Note over BUF: 缓冲后脱敏 → 避免漏掉敏感词片段
    API-->>C: SSE event:done data:[DONE]
```

## 三、LangGraph 状态流转

```mermaid
stateDiagram-v2
    [*] --> llm_node: 用户消息
    llm_node --> tool_node: LLM 返回 tool_call
    llm_node --> eval_node: LLM 直接回复
    tool_node --> llm_node: 工具结果注入
    eval_node --> [*]: 返回最终回复

    note right of tool_node: 工具执行调度<br/>MCP Client / 本地工具
    note right of eval_node: LLM-as-a-Judge<br/>四维评分 JSON
```

## 四、安全三层防线

```mermaid
flowchart LR
    REQ[用户请求] --> G1[① guard_input]
    G1 -->|通过| LLM[Agent 处理]
    G1 -->|拦截 'prompt_injection' + 400| REJ1[拒绝]

    LLM --> TOOL[工具调用]
    TOOL --> G2[② guard_tool]
    G2 -->|通过| EXEC[执行工具]
    G2 -->|拦截 'dangerous_tool' + 跳过| SKIP[跳过并记录]

    EXEC --> EVAL[评估输出]
    EVAL --> G3[③ guard_output]
    G3 -->|脱敏| RESP[返回客户端]
    G3 -->|含敏感数据| MASK[替换为 ***]
```

| 防线 | 位置 | 检测内容 | 失败策略 |
|------|------|---------|---------|
| guard_input | 请求入口 | 黑名单关键词(ignore/forget/system)、Unicode NFKC 归一化 | 返回 400 |
| guard_tool | 工具执行前 | 危险操作(os.system/subprocess/sql injection) | 跳过工具，记录日志 |
| guard_output | 响应出口 | 脱敏(PEM密钥/API Key/手机号/身份证) | 替换为 `***` |

## 五、关键设计决策

| 决策 | 理由 | 面试可讲 |
|------|------|---------|
| **LangGraph 而非手写 if-else** | State 自动合并、节点隔离、内建 Checkpoint | "类似 Flowable 工作流引擎" |
| **MCP 协议而非硬编码工具** | 跨语言、动态发现、工具与 Agent 解耦 | "类似 Java SPI 机制" |
| **LLM-as-a-Judge 而非规则评分** | 灵活理解语义，4 维度可解释 | "外部验证 > 自我评估" |
| **SSE 缓冲后脱敏** | 避免流式输出中敏感词片段漏过 | "安全在传输层和业务层都要做" |
| **单 worker 启动** | Agent 瓶颈在 LLM API 不在 CPU | "压测数据支撑：框架 P99 17ms vs LLM P99 3s" |

## 六、Java 对照实现

同一架构在 `agent-gateway-java/` 有 Spring Boot + LangChain4j 版本，相同的核心模式用 Java 表述：

| Python | Java | 模式 |
|--------|------|------|
| `@tool` 装饰器 | `@Tool` 注解 | 工具声明式注册 |
| `model.bind_tools()` | `AiServices.builder().tools()` | 工具绑定 |
| `StdioServerParameters` | `StdioMcpTransport.builder()` | MCP stdio 传输 |
| `ClientSession.list_tools()` | `McpClient` → `McpToolProvider` | MCP 动态发现 |
| `StateGraph` | — (Java 侧未接入 LangGraph4j) | 图编排 |
