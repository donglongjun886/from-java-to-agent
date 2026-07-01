# Day 18 (2026.07.01 三) — 日志缺口补齐 + 四Agent联调 + Context Reset

## Part 1: 历史日志缺口补齐

### 核心认知

日志是学习计划的骨骼。Week 3（Day11-15）代码和笔记产出量最大（19文件~3700行），但日志全空——只有一篇周复盘。今天一次性补齐了 Day10 到 Day17 的全部缺口。

补写过程中最大的感受：**靠周复盘回溯写日志，和当天实时记录，信息密度完全不同**。当天写日志能捕捉到「卡住的瞬间」和「为什么这样设计」的思考过程；事后补只能靠commit和代码反推——框架对了，血肉少了。这是一个重要的习惯教训。

### 补写产出

| 天数 | 内容 | 审查+修复 |
|------|------|----------|
| Day10 | 压测+架构图+Week2复盘 | ✅ |
| Day11 | IR基础+Embedding+首个RAG | ✅ |
| Day12 | 全理论日：三级管道+GraphRAG+上下文工程 | ✅ |
| Day13 | 权限感知检索+双维评估+Langfuse | ✅ |
| Day14 | 项目B（上）：Enterprise RAG框架 | ✅ |
| Day15 | 项目B（下）+Week3复盘 | ✅ |
| Day17 | 检索评估+安全+SDD+四Agent架构 | ✅ |

7篇日志 + HITL笔记补充，全部走审查→修复闭环。

## Part 2: 四Agent全链路联调

### 核心认知

四Agent Pipeline（Planner → Retriever → Generator → Evaluator）全部跑通，三个查询覆盖单源/跨源/对比三种场景，9次API调用零报错。

三个查询结果：
- 研发部Q3预算利用率：98.37%
- 研发部Q4建议：云成本优化降本18%、细化预算管理
- 各部门对比：销售部102.9%超预算，最需优化

Evaluator独立评分：Faithfulness 1.0 / Answer Relevancy 1.0（三个查询全部满分）。

### Java类比

四个Agent之间的数据流是纯结构化的——plan是 `list[dict]`，retrieved是 `dict[str, str]`，answer是 `str`，evaluation是 `dict`。没有任何地方传递共享的messages数组。这就像微服务之间通过DTO通信而非共享数据库——每个服务有自己的状态，通过明确的接口契约传递数据。

## Part 3: Context Reset策略

### 核心认知

检查代码后发现，**Context Reset已经天然存在**：`ask_llm()` 每次调用都创建全新的 `messages = [{"role": "system", "content": system_prompt}]`，不累积历史。四个Agent之间传递结构化数据而非消息数组，天然隔离。

这个设计和JVM的栈帧管理是同构的——每次方法调用分配新栈帧，方法结束自动释放。没有全局状态，就没有污染风险。但需要显式标注——在三个关键位置添加了 `【Context Reset】` 注释。

## 今日统计

**日志**：补写7篇（Day10-15, Day17）+ 1篇HITL笔记补充
**审查**：10篇日志+笔记全部审查（MCP code-review）× 修复闭环
**代码**：四Agent全链路联调通过 + Context Reset注释落地
**认知锚点**：
- 当天写日志和事后补的信息密度完全不同——习惯比产出更重要
- Agent间用结构化数据传递优于共享messages数组——微服务治理思想完全适用
- 好的架构天然具备Context Reset——不需要额外做"清理"，只需要不创造全局状态
