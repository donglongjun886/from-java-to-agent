# Day 9 (2026.06.17) — 审计 + 晚段技术专题启动

## 主题
进度审计 Day 1-8 + 启动晚段债务偿还（LangChain4j 技术专题）

## 审计发现

### 缺口清单
| 缺口 | 状态 |
|------|------|
| `journal/week-01/day-05.md` | ❌ 缺失 |
| `projects/agent-gateway/` 核心实现 | ❌ 空壳 |
| Week 2 晚段 LangChain4j（Day 6-8） | 🔄 今天起补 |
| `notes/agent-basics-deep-dive.md` | 🔄 技术专题待启动 |
| 行业视野（Week 1+2，各1次） | ❌ 未做 |

### 已完成项（Day 1-8 白段）
Python速通 → LLM概念 → Chat API → 评估入门 → Tool Calling → LangGraph → MCP → A2A概览 + 记忆层
核心知识面全覆盖，笔记 6 篇，代码 14 个 Python 文件。

### 本周剩余压力
Day 9-10 需完成 agent-gateway 核心实现（MCP Client + 沙箱 + 流式 + 安全 + 压测），时间紧张。

## 晚段专题：Day 6 LangChain4j 技术深度

### LangChain4j 核心概念
- **@Tool**：Java 方法签名自动提取 JSON Schema，编译期类型安全，参数校验零代码
- **AiServices**：面向接口的动态代理，定义 interface 即可获得完整 Tool-Calling Agent
- **LangChain4j 定位**：一个依赖树覆盖 Python 生态 openai SDK + LangGraph + FastMCP + LlamaIndex

### Function Calling 技术拆解
- Function Calling 原理（四阶段：注册→决策→执行→反馈）
- 三层分析（原理→坑→防御）
- Java 视角：@Tool 静态类型 = Schema 自动生成，省一半胶水代码

## 关键认知

1. **LangChain4j ≈ Spring Framework 对 AI 做的事** — 统一编程模型，屏蔽底层差异
2. **LangChain4j 的学习重点不在细节**，在于"为什么选它"的技术判断力
3. **Function Calling 不是魔法** — 模型输出决策信号，客户端执行，AI 版 SPI
4. **工具描述质量 > 代码实现质量** — LLM 只能看到 description，看不到方法体

## 产出
- LangChain4j 核心概念笔记 + Function Calling 技术拆解