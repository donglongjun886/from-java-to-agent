# Day 9 (2026.06.17) — 审计 + 晚段补课启动

## 主题
进度审计 Day 1-8 + 启动晚段债务偿还（LangChain4j + 面经）

## 审计发现

### 缺口清单
| 缺口 | 状态 |
|------|------|
| `journal/week-01/day-05.md` | ❌ 缺失 |
| `projects/agent-gateway/` 核心实现 | ❌ 空壳 |
| Week 2 晚段 LangChain4j（Day 6-8） | 🔄 今天起补 |
| `notes/面试题-Agent基础.md` | 🔄 2/15 完成 |
| 行业视野（Week 1+2，各1次） | ❌ 未做 |

### 已完成项（Day 1-8 白段）
Python速通 → LLM概念 → Chat API → 评估入门 → Tool Calling → LangGraph → MCP → A2A概览 + 记忆层
核心知识面全覆盖，笔记 6 篇，代码 14 个 Python 文件。

### 本周剩余压力
Day 9-10 需完成 agent-gateway 核心实现（MCP Client + 沙箱 + 流式 + 安全 + 压测），时间紧张。

## 晚段补课：Day 6 晚段内容

### LangChain4j 核心概念
- **@Tool**：Java 方法签名自动提取 JSON Schema，编译期类型安全，参数校验零代码
- **AiServices**：面向接口的动态代理，定义 interface 即可获得完整 Tool-Calling Agent
- **LangChain4j 定位**：一个依赖树覆盖 Python 生态 openai SDK + LangGraph + FastMCP + LlamaIndex
- **面试定位**：框架熟悉度排第三（系统设计 > 工程经验 > 框架），LangChain4j 是案例素材不是核心考点

### 面试模拟
- 口头回答 Function Calling 原理（四阶段：注册→决策→执行→反馈）
- 三层考点拆解（原理→坑→防御）
- Java 视角反杀：@Tool 静态类型 = Schema 自动生成，省一半胶水代码

### 面经产出
- `notes/面试题-Agent基础.md`：题1 Agent定义 + 题2 Function Calling原理
- 每题含参考答案 + 考点分层 + Java 视角加分

## 关键认知

1. **LangChain4j ≈ Spring Framework 对 AI 做的事** — 统一编程模型，屏蔽底层差异
2. **面试问 LangChain4j 不考细节**，考的是"为什么选它"的技术判断力
3. **Function Calling 不是魔法** — 模型输出决策信号，客户端执行，AI 版 SPI
4. **工具描述质量 > 代码实现质量** — LLM 只能看到 description，看不到方法体

## 产出
- `notes/面试题-Agent基础.md`（新建，2/15 道）