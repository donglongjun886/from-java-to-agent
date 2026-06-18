# Week 2 复盘（06/12 - 06/18）

## 一、这周学到了什么？（知识增量）

### 技术栈

| 领域 | 学到的东西 | 实战产出 |
|------|-----------|---------|
| **LangGraph** | StateGraph/Node/Edge/条件路由/Checkpointer，图编排替代手写 if-else | agent_graph.py（llm→tool→eval 三层图） |
| **MCP 协议** | Server/Client 架构、三原语(Tools/Resources/Prompts)、stdio/HTTP+SSE 传输、动态工具发现 | Python MCP Server + Java LangChain4j MCP Client |
| **FastAPI 服务化** | 同步/SSE流式双接口、lifespan关机钩子、EventSourceResponse缓冲脱敏 | server.py（/chat + /chat/stream + /stats） |
| **Agent 安全** | 三层防线：guard_input(注入+Unicode NFKC) / guard_tool(危险操作拦截) / guard_output(脱敏替换) | agent_graph.py 内建安全护栏 |
| **容错与可观测** | asyncio.wait_for 超时 + 指数退避重试 + 30s 冷却；Stats 追踪 calls/tokens/time/eval | circuit_breaker.py + Stats 收集器 |
| **代码沙箱** | E2B 概念、SandboxExecutor 封装、本地工具注册表 SSOT | sandbox.py |
| **压测** | Locust 框架使用、框架基线 vs Agent 链路对比、Token 成本估算 | load_test.py + BENCHMARK.md |
| **架构可视化** | Mermaid 系统架构图/时序图/状态流转图 | ARCHITECTURE.md（6 张图） |
| **Java 对照** | LangChain4j @Tool/AiServices/MCP Client/StdioMcpTransport | agent-gateway-java/（12个Java文件） |

---

## 二、和 Java 生态比，核心差异是什么？（认知升级）

### 1. Agent 开发的「不可靠性」是设计前提

传统 Java 后端假设下游服务有 SLA——超时是异常、失败是 bug。Agent 开发中 LLM 的不可靠性是常态：
- 幻觉（编造工具名、编造参数）
- 响应时间不可预测（2s ~ 30s）
- 同一个 prompt 两次输出不一样

所以 Agent 架构天然需要**护栏**（guard_input/guard_tool/guard_output）和**反馈环**（eval_node → 重试），和传统 API Gateway 的熔断限流是同一种思路，但粒度不同——传统网关防的是下游挂了，Agent 网关防的是 LLM 疯了。

### 2. 编排方式的升维

```
传统后端: Controller → Service → DAO（固定链路，编译期确定）
Agent:    LangGraph 图 → LLM 动态决策 → 条件路由（运行时决定走哪个工具）
```

这个差异类似硬编码 HTTP 调用 vs 工作流引擎——后者在图定义里加一个节点不影响已有节点，前者要改整个 if-else。

### 3. 评估体系从「可用性」变为「质量」

传统后端监控：QPS、P99、错误率——数字好看就行。
Agent 监控：回答质量（准确性/完整性/相关性/安全性）——数字好看不代表回答好用。

这周把 LLM-as-a-Judge 独立成一个 eval_node，就是让「另一个 LLM」当裁判，避免 Agent 自评。这和传统后端里「外部监控大盘」vs「自我心跳检测」是类似的关系——自己说自己好不算。

### 4. Python 的工程短板和 Java 的天然优势

| | Python | Java |
|------|--------|------|
| 工具注册 | `@tool` 装饰器，运行时反射 | `@Tool` 注解，编译期类型检查 |
| JSON Schema | 靠 Pydantic 自动生成 | 方法签名本身就是强类型约束 |
| 并发模型 | async/await，GIL 限制 | 虚拟线程(Virtual Threads)，天然高并发 |
| 生态成熟度 | Agent 框架最全最活跃 | 晚半年到一年，但企业集成力强 |

这一周最大的认知是：**Python 赢在 Agent 生态，Java 赢在生产可靠性。** 最好的岗位是「用 Java 搭系统，用 Python 做 Agent 算子」，而不是二选一。

### 5. 工具发现方式的质变

```
Day 1-5:  工具硬编码在 Agent 代码里（TOOLS = [...]）
Day 6-7:  工具通过 MCP Server 独立进程暴露（动态发现）
Day 10:  同一个 Python MCP Server，Java 端通过 stdio 连上去
```

工具从「Agent 的一部分」变成了「Agent 可以动态接入的外部能力」。这和 Java 里从「new Service()」到「@Autowired Service」再到「Nacos 服务发现」是同一个进化方向。

---

## 三、下周需要调整什么？（行动优化）

### 1. 技术深度专题必须化固为习惯

**问题**：技术专题欠债，知识梳理跟不上编码节奏。这两项是学习计划的一部分，不能因为「忙着写代码」就推后。

**调整**：技术专题每天 2 个 + 系统设计每天 45min，作为开机第一件事，不推到晚段。

### 2. Week 3 RAG 入门需要前置准备

**问题**：LlamaIndex + ChromaDB + Embedding 是全新的领域，和 Week 1-2 的 LLM API + Agent 编排不在一个知识树上。

**调整**：周末提前读一遍 LlamaIndex 文档目录，建立概念地图（Data Ingestion → Indexing → Querying 三阶段），周一直接进入编码。

### 3. 项目产出的对外展示

**问题**：代码量够了（Python 14 文件 + Java 12 文件），但别人不会跑你的代码。

**调整**：Agent 网关的 README 里放架构图缩略链接 + 一行启动命令，让人扫一眼就知道做了什么。

### 4. 晚段 Java 对照不要掉落

Week 2 的 MCP Client 和 LangChain4j 对照做得不错，Week 3 进入 RAG 后对应的 Java 对照是 PGVector + Embedding，需要提前确认 LangChain4j 对 PGVector 的支持情况。

---

## 周评分

| 维度 | 自评 | 说明 |
|------|------|------|
| 技术学习 | 9/10 | Python+Java 双线推进，MCP 跨语言集成超出计划预期 |
| 习惯养成 | 7/10 | 每日编码习惯稳固，但技术专题未固化进日常节奏 |

**周关键词**：从 Demo 到工程 —— 这周 Agent 网关从框架变成有安全护栏、可观测、压测数据、架构图的完整系统。下周的关键词应该是**从工程到表达**——把写出来的东西讲得出来。
