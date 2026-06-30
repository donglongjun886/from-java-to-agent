# Day 5 (2026.06.11 四) — 项目 A（下）+ Tool Calling 初体验 + 周复盘

## Part 1: Tool Calling 概念初体验 ✅

### 核心认知

**Tool Calling 是 Agent 从「聊天」到「干活」的质变点。** 之前四天，Agent 本质是个高级聊天机器人——你问它答，最多用 System Prompt 约束行为。今天加上 Tool Calling 后，Agent 能自己决定「要不要查天气」「要不要算数」，这个自主决策能力才是 Agent 区别于普通 Bot 的关键。

**Tool Calling 的核心误解纠正**：不是模型自己去执行函数。实际的二分架构是：

| 角色 | 职责 | Java 类比 |
|------|------|----------|
| Model（决策层） | 判断需要哪个工具、提取什么参数、什么时候结束 | Spring MVC Controller — 路由决策 |
| Code（执行层） | 实际调 API、访问数据库、执行计算 | Service 层 — 业务逻辑执行 |

流程是四步闭环：
1. 发送 user message + tools 定义 → 模型返回 `finish_reason="tool_calls"`（而非 `"stop"`）
2. 你的代码解析 `tool_calls`，执行对应函数
3. 把函数结果作为 `role: "tool"` 消息追加到 messages 数组
4. 再次调 API（携带完整的 tools 定义），模型基于函数结果生成最终自然语言回复

**安全提醒**：模型返回的工具参数不可信。Code 层在调用任何外部 API、执行数据库操作、拼接命令前，必须对参数做校验和消毒。特别注意：绝对不能用 `eval()` 直接执行 LLM 返回的表达式或代码片段——这是典型的 RCE（远程代码执行）风险。类比 Java 后端的参数校验 Filter / `@Validated` 注解，Agent 的工具层也需要同等级别的输入消毒。

注意第三步的细节：tool result 必须作为**独立消息**追加，不能拼到 user message 里。这是 OpenAI 协议层的硬约束，否则模型会「忘记」工具已经调用过。

**多工具场景下，模型自动匹配正确工具**——给问题「杭州天气」就调 `get_weather`，给「12345+67890」就调 `calculate`。这种自动路由能力，类比 Java 里 Spring 的 `@RequestMapping` 注解：你定义了接口契约（JSON Schema），框架（LLM）自动做路由分发。

### 代码产出

- `tool_calling_demo.py`：三个实验全部跑通
  - 实验1：单工具（`get_weather`），观察模型识别需要天气数据、准确提取参数 `city: "杭州"`
  - 实验2：有工具 vs 无工具场景对比——「北京天气」触发工具调用，「你好你是谁」直接回复不调工具
  - 实验3：多工具选择（`weather` + `calc`），模型正确将「12345+67890等于多少」路由到 calculate
- 关键实现：`run_conversation()` 函数封装了完整的 tool calling 闭环（发送→解析→执行→回传→再生成）
- 工具注册表 `TOOL_MAP`（函数名→函数对象映射），这是代码层的工具发现机制，类比 Java SPI

## Part 2: Week 1 整合产出 + 周复盘 ✅

### 核心认知

**整合的意义不只是把代码拼在一起。** 当 Chat API + 流式 + 成本统计 + LLM-as-a-Judge 评估 + Feedback Loop 重试 + Tool Calling 六个模块同时在同一个 Agent 实例里工作时，才能真正感受到 Harness 工程的价值：各层之间的契约边界要清晰，否则改动一个模块就牵一发动全身。

Harness 六层指：Model / Agent Loop / Tools / Memory / Observability / Context——当前 Week 1 已落地其中五层（Agent Loop 暂时用简单的 while 循环替代，未抽象为图编排）。

| 层 | 落地方式 | 状态 |
|----|---------|------|
| Model | `client + model`（可替换，不是壁垒）| ✅ 已落地 |
| Agent Loop | 简单 while 循环替代（未抽象为图编排）| 🔜 待补 |
| Tools | `TOOLS` 定义 + `TOOL_MAP` 注册 + tool calling 闭环 | ✅ 已落地 |
| Memory | `self.messages` 数组 + `reset_context()` 支持上下文重置 | ✅ 已落地 |
| Observability | 输入/输出 token 累计 + 调用次数 + 重试次数 + 美元成本估算 | ✅ 已落地 |
| Context | `evaluate()` 四维度打分 → 阈值判断 → 带改进建议重试（Feedback Loop）| ✅ 已落地 |

对比 Java 后端开发的感受：Agent 开发的核心挑战不是「能跑」，而是「跑得稳定、可观测、知道什么时候该重试、什么时候该放弃」——这和微服务治理是一回事，只是治理对象从「服务」变成了「LLM 调用」。

学习计划 v5 → v6 更新：基于 JD 面经和 GitHub 趋势审视，做了三处关键调整：
1. 新增 Tool Calling 到 Day 5（原计划 Week 1 没有 Tool Calling，补上这个质变点）
2. 第 2 周新增 FastAPI 服务化 + Agent 安全体系（Prompt 注入防御 / Tool 调用预检）
3. 第 3-4 周新增 IR 基础 + 排序评估 + 权限感知检索（对标 Zoom Enterprise RAG JD）

这些调整的逻辑是：面试不考「我会调 API」，考的是「你有没有工程化思维」。FastAPI + 安全 + 评估 + 压测这套组合，才是 Java 工程师转型的优势面。

### 代码产出

- `hello_agent_complete.py`：Week 1 整合交互式 CLI，六大模块统一入口
  - 命令：`/stats` 用量、`/eval` 评估上次回答、`/reset` 重置上下文、`/quit` 退出
  - Flow：用户输入 → `agent.chat()` 内部走「生成 → Judge 评估 → 不达标带反馈重试」完整链路
  - Tool Calling 集成在 `_chat_once()` 中：检测 `tool_calls` → 执行函数 → 追加 tool result → 二次调用生成最终回复
- `journal/week-01/retrospective.md`：第一周复盘，三问框架
  - 学到了什么：6 个知识块，6 个 Python 文件，从零搭建了完整的单 Agent 系统
  - 核心差异：Agent 开发不是「调 API + 写 Prompt」，而是为不确定的模型建确定性的工程框架
  - 下周调整：补写 harness-fundamentals.md，保持晚段 Spring AI 节奏

### 5 个 commit

- `01f8ffd` docs: README 同步 Day 5 + Week 1 完整收官
- `ed96fdf` feat(hello-agent): Day 5 Part2 — Week 1 整合产出 + 周复盘
- `d25fb4e` feat(hello-agent): Day 5 Part1 — Tool Calling 概念初体验
- `afd7fd8` docs: Day 5 新增 Tool Calling 概念初体验——让 Agent 从聊天进化到干活
- `c7e709b` docs: learning-plan v5 → v6 — 基于 JD/面经/GitHub趋势审视

---

**Week 1 收官感言**：五天时间，从 Python 速通到跑通一个带评估 + 反馈 + 工具的完整 Agent。回头看不只是学了一堆 API，更重要的是建立了「Agent = Model + Harness + Feedback Loop」这个心智框架。下周进入 LangGraph 编排 + MCP 协议，从单 Agent 对话进化到图编排的多工具 Agent 网关——那才是真正考验工程能力的时候。
