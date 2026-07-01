# Day 10 (2026.06.18 四) — 项目A：压测 + 架构图 + Week 2 复盘

## Part 1: 压测 ✅

### 核心认知：用传统高并发标准度量 Agent

Java 后端做压测是本能——JMeter/Locust/Gatling 随手就来，QPS/P99/错误率三件套。Agent 网关的压测不一样的地方在于：**瓶颈不在代码，在 LLM API 调用**。这个发现本身就是本周最重要的工程结论。

### 压测分两轮

#### 第一轮：框架基线（/health），50 并发 30s

- QPS: **156 req/s**
- P99: 17ms
- 失败: 0

和 Spring Boot Actuator `/health` 一个量级——FastAPI + Uvicorn 单 worker 框架开销几乎为零。这说明网关本身的吞吐能力不是问题。

#### 第二轮：Agent 完整链路（POST /chat），3 并发 30s

- Avg 延迟: **2,622ms**
- P99: 3,006ms
- 有效 QPS: 0.37 req/s（实测值，LLM API 限流导致低于理论值 1.14）
- 成功率: 100%

两轮的对比非常戏剧性——框架层 P99 17ms，Agent 层 P99 3,000ms，差了 **176 倍**。这个差距全部来自 DeepSeek API 的推理耗时。

### 瓶颈分析

传统后端的性能优化思路是「哪里慢优化哪里」——加索引、加缓存、调连接池。Agent 网关的瓶颈分析结果却是：

| 层次 | 瓶颈 | 占延迟比 |
|------|------|---------|
| FastAPI 框架 | 无 | <1% |
| 安全护栏（正则+NFKC） | 无 | <1% |
| MCP 通信（stdio） | 无影响（本次未触发工具调用） | 0% |
| **LLM API 调用** | **主要瓶颈** | **>98%** |
| Python GIL | 轻微（单 worker 可忽略） | <1% |

这很像 Java 微服务里「数据库 IO 吃掉了 95% 的响应时间」——优化代码没意义，应该优化的是连接管理（LLM API 并发控制）、缓存（System Prompt prefix caching）、以及流式输出（降低用户体感延迟）。

### Token 成本估算

单次简单对话约 490 token，费用约 ¥0.0007（不到 1 厘钱）。工具调用场景额外 +1 次 LLM 往返，成本翻倍至约 ¥0.0014。按 10 万次调用/月估算，月成本约 ¥70-140。这个数字对比 Java 后端里一个 Redis 实例的月费还低，说明 **LLM API 的成本现阶段不是瓶颈，瓶颈在工程可靠性和输出质量**。

### Java 类比

传统 API 网关的 P99 在 50ms 以内，Agent 网关的 P99 在 3,000ms。但这不是 Agent 网关做得差——而是 LLM 推理的物理时间绕不过去。类比就是：**传统网关是路由器转发，Agent 网关是让一个专家当场思考后再回答**。延迟高是合理的，工程重点应该从「快」转向「可靠」——熔断、重试、降级、超时，这些微服务治理手段在 Agent 场景完全复用。

### 原生 Tool Calling vs MCP 对比

Week 1 的 Tool Calling 和 Week 2 的 MCP 看似都让 Agent 调工具，但本质差别很大：

| 维度 | 原生 Tool Calling | MCP 协议 |
|------|------------------|---------|
| 工具发现 | 硬编码 `TOOLS = [...]` 在代码里 | Client 动态调用 `list_tools()` 发现 |
| 进程隔离 | 工具函数和 Agent 在同一进程 | MCP Server 独立进程，崩溃不影响 Agent |
| 跨语言复用 | 只限 Python 调用 | 任何语言实现 MCP Server，Agent 通过 stdio/HTTP 连接 |
| Java 类比 | `new Service()` 硬编码 | Nacos 服务发现 + SPI 动态加载 |

这个对比的意义在于：工具从「Agent 的一部分」变成了「Agent 可以动态接入的外部能力」。Week 1 加一个工具要改代码重启，Week 2 只需要启一个 MCP Server。

---

## Part 2: 架构图 + 设计决策 ✅

### 产出：6 张 Mermaid 图 + 1 张决策表

`ARCHITECTURE.md` 包含了从系统全景到安全细节的完整可视化：

1. **系统架构图**（graph TB）—— Agent Gateway 全景，从客户端到 DeepSeek API 再到 MCP Server 的完整数据流
2. **同步调用时序图**（sequenceDiagram）—— POST /chat 一次工具调用场景的完整链路（客户端 → 护栏 → LLM → MCP → 评估 → 返回）
3. **SSE 流式时序图**（sequenceDiagram）—— 流式输出 token-by-token + 缓冲脱敏的时机
4. **LangGraph 状态流转图**（stateDiagram）—— llm_node → tool_node → eval_node 的状态机，和 BPMN 的状态流转一模一样
5. **安全三层防线图**（flowchart LR）—— guard_input → guard_tool → guard_output 的执行顺序和拦截点
6. **关键设计决策表**—— 5 个核心决策 + 理由 + 面试可讲的类比

### 评估层独立为 evaluator.py

Day 9 时 eval_node 嵌在 agent_graph.py 里，Day 10 把它拆成独立的 `evaluator.py`。这是个关注点分离的典型重构：

- **独立的 OpenAI client 实例**——不和 Agent 共享模型实例，避免「自己写的代码通过自己写的测试」
- **独立的 System Prompt**——评估器的 prompt 和 Agent 的 prompt 互不干扰
- **独立的错误处理**——评估失败不污染 Agent 的正常回复（默认 3 分降级）

这类似 Java 里的「将 Service 拆分为独立 Bean，各自维护自己的连接池」——单例是方便，但隔离性不够。

### 关键设计决策的 Java 视角

| 决策 | Python 实现 | Java 类比 |
|------|-----------|-----------|
| LangGraph 编排 | `StateGraph.add_node().add_conditional_edges()` | Flowable BPMN 的 ProcessDefinitionBuilder |
| MCP 协议工具发现 | `ClientSession.list_tools()` 动态加载 | Java SPI `ServiceLoader.load()` |
| LLM-as-a-Judge 质检 | 独立 evaluator.py + 四维 JSON 评分 | 微服务里的独立审计服务 |
| SSE 缓冲后脱敏 | `asyncio.Queue` 累积再正则替换 | API Gateway 的 Response Filter |
| 单 worker 部署 | Uvicorn 默认 1 worker | 单实例部署——瓶颈在 IO 不在 CPU |

---

## Part 3: Week 2 复盘

### 这周学到了什么？

从「能调用 LLM API」到「能交付一个工程化的 Agent 网关系统」。具体增量：

| 领域 | 从 | 到 |
|------|-----|-----|
| 编排方式 | 手写 if-else 控制流 | LangGraph StateGraph 图编排（加节点不改已有节点） |
| 工具管理 | 硬编码 `TOOLS = [...]` | MCP Server 独立进程 + 动态工具发现 |
| 服务化 | 命令行脚本 | FastAPI HTTP + SSE 流式双接口 |
| 安全 | 无防护 | 三层防线（输入 → 工具 → 输出） |
| 质量评估 | 人肉判断 | LLM-as-a-Judge 四维自动评分 |
| 可观测 | print() 调试 | Stats 收集器（calls/tokens/time/eval） |
| 压测 | 不关注 | Locust 框架基线 vs Agent 链路对比 |
| 容错 | 异常即崩溃 | 超时重试 + 指数退避 + 30s 冷却 |

### 核心差异认知

和 Java 生态比，Agent 开发最大的差异不是语言和框架，而是 **「不可靠性」成了设计前提**：

1. **延迟不可预测**——同一个 prompt 两次调用，可能 2s 也可能 10s。传统后端假设 SLA 稳定，Agent 必须假设 LLM 随时可能慢、可能错、可能幻觉。
2. **输出不可验证**——数据库查询能用单元测试验证，LLM 的输出没有「正确答案」，只能靠另一个 LLM 做裁判（eval_node）。
3. **编排要支持回退**——传统工作流的节点编排是确定的（A → B → C），Agent 的编排需要 eval 节点能触发重试（C → 回到 A），这要求状态设计支持回滚。

### 下周调整

1. **RAG 领域前置准备**——Week 3 进入 Enterprise RAG，和 LLM API 不在一个知识树上，周末需提前建立概念地图
2. **技术专题要日常化**——不能推到「晚段」再说，Day 11 起作为开机第一件事
3. **Python 代码开始注意工程规范**——Week 1-2 以快速实验为主，Week 3-4 的项目需要能讲架构设计的代码

### 周评分

| 维度 | 自评 | 说明 |
|------|------|------|
| 技术学习 | 9/10 | Python+Java 双线推进，MCP 跨语言集成超出计划预期 |
| 工程实践 | 8/10 | 压测+架构图+安全三层+评估独立，工程意识到位 |
| 习惯养成 | 7/10 | 每日编码稳固，但技术专题和行业视野需固化进日常 |

---

## 产出

| 文件 | 说明 |
|------|------|
| `projects/agent-gateway/load_test.py` | Locust 压测脚本（框架基线 + Agent 链路两种 scenario） |
| `projects/agent-gateway/BENCHMARK.md` | 压测报告（两轮数据 + Token 成本 + 瓶颈分析） |
| `projects/agent-gateway/ARCHITECTURE.md` | 6 张 Mermaid 图 + 5 条设计决策 + Java 对照 |
| `projects/agent-gateway/evaluator.py` | 评估层独立（从 agent_graph.py 拆出，独立 client + 独立 prompt） |
| `journal/week-02/retrospective.md` | Week 2 完整复盘（知识增量 + 认知升级 + 行动优化） |

### 3 个 commit
```
feat(agent-gateway): Day 10 压测 — Locust脚本 + 压测报告
docs(agent-gateway): Day 10 架构图 — 6张Mermaid图 + 设计决策表
refactor(agent-gateway): 评估层独立为 evaluator.py
```
