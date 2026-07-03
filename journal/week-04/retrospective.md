# Week 4 复盘（2026.06.29 - 2026.07.03）

## 计划 vs 实际

| 天数 | 计划 | 实际 | 偏差 |
|------|------|------|------|
| Day16 | Agentic Retrieval + 多Agent协作 + Harness六层 | ✅ 四Agent协同系统 + 3篇笔记写审修 | 如期 |
| Day17 | 检索评估 + Agent安全 + SDD | ✅ 静态RAG vs Agentic对比（P@3/MRR/NDCG） | 如期 |
| Day18 | 四Agent实现 | ✅ 四Agent联调 + Context Reset收尾 | 如期 |
| Day19 | 压测 + 文档 | ✅ 负载压测 + 故障注入4/4 + 全量Review Fix | 如期 |
| Day20 | 全面复盘 | ✅ 周复盘 + 月度总结（今天） | 如期 |

> Week 4 全部按计划完成，零偏差。Day 19 的压测+Review+Fix是全月工程化程度最高的一天。

## 一、这周学到了什么？

### 知识增量

**Agentic Retrieval vs 静态RAG**：静态RAG是固定DAG（查询→检索→重排→生成），Agentic引入LLM做动态路由——Agent自主决策查什么数据源、以什么顺序、是否迭代。两者的边界清晰：单一检索用静态够用，多步推理/跨源查询才需要Agentic。Day 17的对比评估量化验证了这一点（4源规模下两者持平，20+源才会拉开差距）。

**四Agent协同架构**：Retrieval Planner（分解查询）→ Multi-Source Retriever（并行检索多源）→ Generator（生成报告）→ Evaluator（独立评估+反馈）。核心设计原则：Evaluator必须是独立Agent（外部验证>自我评估）、Planner输出需做输入校验（防御性编程）、Retriever四路并行（ThreadPoolExecutor）。

**多Agent协作模式**：Manager-Worker（中心化调度）、流水线（串行产出）、对等协作（去中心化）。选型取决于任务类型——单一复杂任务用Manager-Worker，固定链路用流水线，需要多方视角用对等协作。

**压测方法论**：用QPS/P99/成本三维度量Agent系统。Generator占62%耗时是最优瓶颈，引入Streaming可改善感知延迟。静态RAG零延迟零成本，高频简单查询兜底；Agentic Pipeline有LLM开销但灵活性高，复杂查询才进入。

**故障注入四场景**：Tool超时→降级返回而非崩溃、虚假检索数据→防线在Retrieval而非Generator、上下文截断→正常处理或fail-fast、Planner输出异常→下游防御性校验。核心认知：故障注入的目的不是「不出bug」，而是「出bug时有明确的责任边界」。

### 工程方法

- 子Agent并行执行MCP code review → fix → 全量回归的工作流
- unittest.mock.patch 注入故障替代伪测试
- `\b` 单词边界在中文语境中的陷阱（中文字符被视为`\w`）
- 正则贪婪匹配（`.*`）在JSON提取中的隐患及`find/rfind`边界定位替代方案
- `load_dotenv` 模块顶层执行对import的副作用

## 二、和Java生态比，核心认知升级

**1. Agent压测 ≠ 后端QPS压测**

传统后端：关注计算/IO/数据库瓶颈，压测优化链路短。
Agent：瓶颈在LLM调用（网络延迟+推理时间），压测价值不是「提高QPS」而是「找到哪个Agent最慢，优先优化该环节」。Streaming、缓存、静态兜底是优化三板斧。

**2. 故障注入在Agent系统里更难**

传统后端：下游挂了→熔断开路→降级返回兜底值，确定性链路。
Agent：LLM不可用的场景下，系统需要感知哪些组件依赖LLM、哪些不依赖。Day 19发现Retriever（本地数据查找）不依赖LLM，但Planner/Generator/Evaluator全是LLM依赖——故障注入的粒度要按组件拆，不是按系统拆。

**3. 评估体系分层**

传统后端：单元测试→集成测试→性能测试，层级明确。
Agent评估：检索端用NDCG/MRR（有ground truth）、生成端用RAGAS（LLM-as-a-Judge）、在线端用Langfuse（漂移检测）。三层的测量维度不同，不能互相替代。Day 17的静态vs Agentic对比就是用检索端指标（P@K/MRR/NDCG）而非生成端指标——因为这个对比测的是「检索质量」而非「生成质量」。

**4. Agent代码的防御性编程层次更深**

传统Java：参数校验→业务逻辑→异常处理，三层够用。
Agent代码：Planner输出可能非法JSON → Retriever需校验subtasks结构 → Generator需校验context完整性 → Evaluator需校验answer可用性。每个Agent的输出是下个Agent的输入，格式异常在整个链路上会级联放大，所以每个节点都要做输入防御。

## 三、后续方向

**已建立的能力**：
- 从零开始搭完整RAG系统的能力（摄入→索引→检索→生成→评估→追踪）
- Agentic Retrieval + 多Agent协同的架构设计能力
- 评估体系设计（双维交叉验证、评估粒度选择、数据集规模认知）
- 生产级意识（压测、故障注入、安全护栏、可观测）

**持续学习方向**：
- Agentic Design Patterns 系统化串知识
- Agent评测平台/工具链类实战项目
- MCP协议企业级实践（多Server治理、服务发现）
- Agent安全纵深防御体系
- Stream/SSE架构在生产Agent系统中的设计模式

---

## 产出统计

| 类别 | 数量 | 说明 |
|------|------|------|
| Python文件 | 6个 | four_agent_system / agentic_retrieval / multi_agent_collab / retrieval_compare / load_test / fault_injection |
| 笔记 | 3篇 | multi-agent-patterns / production-agent / harness-engineering-deep |
| 架构文档 | 1篇 | ARCHITECTURE.md（Mermaid图 + 压测数据 + 故障注入结果） |
| 日志 | 4篇 | Day 16-19 |
| Code Review | 1轮(4文件并行) | 子Agent+MCP review → fix → 全量回归 |
| 总代码量 | ~2000行 | 含文档 |
