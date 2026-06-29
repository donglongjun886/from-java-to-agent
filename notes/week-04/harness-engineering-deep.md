# Agent Harness 工程：六层架构深度解析

> 核心认知：**Model 是大脑，Harness 是整个神经系统 + 骨骼系统。大脑决定「能不能想」，Harness 决定「想完之后能不能做事」。**

---

## 1. Harness 的定义

```
Agent 这个词的原始语义是「代理人」，不是「大脑」：
  Model（LLM）→ 决策器官，产生意图
  Harness     → 执行骨架，把意图变成行动
    文件系统 → 持久化状态    │  工具系统 → 手脚延伸
    记忆系统 → 时间连续性    │  沙箱     → 安全边界
    上下文   → 注意力预算    │  反馈环路 → 自纠闭环
```

| Java 直觉 | Harness 真实含义 |
|-----------|-----------------|
| Spring Framework | Agent = Spring Boot App，Harness = DI + AOP + 生命周期管理 |
| JVM | Model = CPU，Harness = 内核（进程调度 + 内存管理 + IO 子系统） |

---

## 2. 六层架构详解

### 2.1 整体架构图

```
用户请求 → ⑤上下文管理层(窗口分配/渐进式披露) → LLM(大脑)
                                                    │
                    ⑧ 生成Tool Call ──────────────   │  生成回复
                    │                                │
              ② 工具系统层                            │
              (注册·发现·调用·结果处理)                 │
              ┌───┴───┐                              │
             ④ 沙箱层  ① 文件系统层                    │
             (代码隔离) (持久化状态)                    │
              └───┬───┘                              │
                  ▼                                  ▼
           ③ 记忆层(短期/长期/情节/事实) → ⑥ 反馈环路(自评自纠)
```

### 2.2 第一层：文件系统层

**文件作为 Agent 的持久化状态（≈ 数据库），替代把所有信息塞进 context window。**

| 数据类型 | Token 阈值 | 存放策略 | Java 类比 |
|---------|-----------|---------|----------|
| 短工具返回 | < 500 | 直接放 prompt | 方法参数传递 |
| 中间计算结果 | 500-2000 | 摘要入 prompt，原文落盘 | 返回 DTO，不传整个 Entity |
| 批量检索 | > 2000 | 落盘 + 逐块读取工具 | 分页查询 + 游标 |
| 结构化数据 | 任意 | 落盘为 CSV/SQLite，用 SQL 操作 | DAO 层 |

```python
# ❌ 全塞：每条 1000 token × 10 条 = 10K，且每轮重传
all_results = [search(q) for q in queries]
next_prompt = build_prompt(all_results)  # O(n) 爆炸

# ✅ 分流：落盘后 prompt 只传引用
with open("/workspace/batch_1.json", "w") as f:
    json.dump(results, f)
next_prompt = """
结果存入 /workspace/batch_1.json (128条)。
请用 read_file 逐批分析，总结共性后回复。"""  # read_file 示例来自 Claude Code 等 AI 编程工具的文件读取能力，非通用 API
# prompt 仅 ~50 token，数据量可无限扩展
```

### 2.3 第二层：工具系统层

**Tool 注册/发现/调用/结果处理 —— SPI + RPC 框架的合体。**

```
生命周期：
  定义(JSON Schema + 描述) → 注册(挂载到Agent) → 发现(LLM路由匹配)
  → 调用(执行+超时) → 结果处理(截断/脱敏/注入上下文)

Java 映射：
  @Bean 声明       → Tool 静态注册
  SPI ServiceLoader → MCP 动态发现
  Feign/Dubbo 调用  → Tool Invocation
  Hystrix 熔断     → Tool Timeout/Fallback
```

**渐进式注册：** 意图分类→分析工具 / 执行→领域工具 / 输出→格式化工具。类比分层 ClassLoader，不一次性加载所有 jar。

### 2.4 第三层：记忆层

**四种记忆类型，必须分开设计、独立存储。**

| 记忆类型 | 存储介质 | 生命周期 | 检索方式 | Java 类比 |
|---------|---------|---------|---------|----------|
| **短期窗口** | Context Window | 单次会话 | 自然语言理解 | 线程栈/局部变量 |
| **长期语义** | 向量数据库 (如 ChromaDB/Pinecone) | 跨会话持久化 | 语义相似度 | Redis（语义化版） |
| **情节摘要** | SQL/NoSQL | 跨会话持久化 | 时间索引 | 归档日志 / 操作审计摘要 |
| **事实 KV** | Redis/DynamoDB | 跨会话 | 精确键匹配 | Redis Hash |

```
协作示例：
用户：「我上周让你分析的那份财报，再帮我对比阿里同期」

事实KV("user:pref") → 「中文、财务风格」
情节摘要(上周对话)  → 「对话#42：特斯拉Q3，营收$25.2B，毛利率18.2%」
短期窗口           → 「阿里在讨论中」
→ Agent 用同一分析框架对比阿里最新财报
```

**设计原则：** 分层不耦合 / 按需检索（不预加载） / 有过期机制 / 用户可审计。

### 2.5 第四层：沙箱层

**绝不信任 LLM 生成的代码。五层纵深防御：**

| 层级 | 机制 | 说明 | Java 类比 |
|------|------|------|---------|
| ① Prompt 约束 | System Prompt 禁止危险操作 | 不可靠，可被注入绕过 | 输入校验 |
| ② 静态分析 | AST 扫描，白名单 import | 拦截 `os/subprocess/socket` | 代码审查 |
| ③ 资源限制 | CPU 1核 / 内存 512MB / 超时 30s | cgroups | K8s Resource Limits |
| ④ 容器隔离 | Docker / Firecracker microVM | 内核级隔离 | SecurityManager |
| ⑤ 审计日志 | 记录每次执行的代码+结果 | 异常检测告警 | 审计系统 |

`exec()` 直接执行 = 🔴禁止（裸 `Runtime.exec(userInput)`） / Docker = 测试环境 / E2B/Firecracker = 生产环境（microVM 级隔离，~200ms 启动）

### 2.6 第五层：上下文管理层

**窗口分配 + 渐进式披露 + Reset vs Compaction。**

```
窗口分配公式（可用空间 = 模型上限 - 输出预留）：
┌──────────┬────────┬────────┬────────┬────────┐
│   场景    │ System │ 历史   │ 工具   │ 文档   │
├──────────┼────────┼────────┼────────┼────────┤
│ 单轮问答  │  10%   │   0%   │  10%   │  80%   │
│ 多轮对话  │  10%   │  50%   │  10%   │  30%   │
│ Agent编排 │  15%   │  15%   │  60%   │  10%   │
└──────────┴────────┴────────┴────────┴────────┘
```

**渐进式披露：** 第一层 System Prompt（始终在线） → 第二层工具定义（按阶段） → 第三层参考文档（检索命中才注入） → 第四层工具结果（本轮用完可丢弃）。

> 类比：不会一次性加载所有 Bean，懒加载按需实例化。

### 2.7 第六层：反馈环路

**让 Agent 从「一次性输出」变成「自我修正闭环」：**

```
① LLM-as-a-Judge：Agent 生成 → 另一 LLM 评估忠实度/相关性 → 不达标→重生成
   Java类比：CI 中跑 lint，不通过打回

② 外部验证：Agent 输出 SQL → 实际执行 → 语法错误 → 修正重试
   Java类比：集成测试，跑通才算通过

③ 环境反馈：Agent 操作 → 环境给 reward/penalty → 调整策略
   Java类比：A/B 实验，数据驱动迭代
```

```python
# 核心模式：最多重试 3 次，每次把错误反馈注入下一轮上下文
for attempt in range(3):
    output = agent.generate(context)
    if has_code(output):
        result = sandbox.run(output.code)
        if result.success: break
        context.add_error(result.error)   # ← Agent 看到错误自行修正
    else:
        score = judge.evaluate(output)
        if score.faithfulness > 0.85: break
        context.add_feedback(score.critique)
```

---

## 3. Context Reset vs Context Compaction（深度对比）

| 维度 | Context Reset | Context Compaction |
|------|--------------|-------------------|
| **操作** | 丢弃大部分历史，只留 System Prompt + 摘要 | LLM 将历史压缩为结构化摘要，替代原始消息 |
| **本质** | 「重新开始」— 断舍离，革命 | 「打包压缩」— 信息不丢，改良 |
| **信息损失** | 中等（细节不可恢复） | 低（结构化保留核心信息） |
| **Token 节省** | 极大（可降至 ~5K） | 中等（压缩比 3:1 ~ 10:1） |
| **计算成本** | 低（无需 LLM） | 中（每次压缩需 LLM 调用） |
| **适用场景** | 话题完全切换、用户显式重置 | Token 接近上限、话题延续 |

**Reset 流程：** 触发条件 → 保留 System Prompt + 偏好 → 可选 1-2 句摘要 → 丢弃原始消息 → 重建上下文。类比 JVM Full GC。

**Compaction 流程：** 取最旧 N 条消息 → LLM 生成结构化摘要（topics + decisions + key_facts + open_questions） → 用摘要替原始消息 → 新消息追加。类比 Kafka Log Compaction。

**选择决策：** Token 接近上限？→ 话题延续用 Compaction / 话题切换用 Reset。

---

## 4. 为什么文件系统比全塞 Prompt 更优

| 维度 | 全塞 Prompt | 文件系统分流 |
|------|-----------|------------|
| **Token 成本** | 每轮重传全部数据，O(n) 线性累积 | 按需读取，O(k) — k 为本轮实际读取量 |
| **注意力稀释** | Lost-in-the-Middle：中间信息被忽略概率 40-60% | 每次只读聚焦内容，注意力密度恒定 |
| **可复用性** | 无法跨会话/跨 Agent 共享 | 文件持久化，多 Agent 共享读写 |
| **可审计性** | 埋在长 prompt 中，难以提取 | 独立文件，可直接查看、git diff |

> 100 轮任务成本差距指数级。Token = Agent 的「现金」，浪费在 Java 叫 OOM，在这里叫账单。Lost-in-the-Middle 效应：Prompt > 20K token 时中间信息被忽略概率 40-60%，文件系统分流保持注意力密度恒定。

---

## 5. Java 类比总表：六层映射

| Harness 层 | Java 生态对应 | 映射逻辑 |
|-----------|-------------|---------|
| **文件系统层** | 数据库 + 对象存储 OSS | 状态持久化载体，CRUD 基本单元 |
| **工具系统层** | SPI + Feign/Dubbo + Hystrix | 接口定义 → 服务发现 → 调用 → 熔断 |
| **记忆层** | Redis + 向量数据库 (如 ChromaDB/Pinecone) + MySQL + Kafka | 四种记忆对应四种存储引擎 |
| **沙箱层** | SecurityManager + Docker + seccomp | JVM 沙箱是进程级，Agent 沙箱系统级 |
| **上下文管理层** | JVM 堆管理 (-Xmx, GC) | 有限空间 → 分配策略 → 回收机制 |
| **反馈环路** | CI/CD Pipeline | 自动化质量门禁 + 持续改进 |
| **Harness 整体** | Spring Framework | 框架提供全套基础设施 |

微服务分层映射：Controller→上下文管理 / Service→LLM / Repository→文件系统+记忆 / Integration→工具系统 / Security→沙箱 / Actuator→反馈环路

---

## 6. Agent Harness 2026 行业最佳实践

### 6.1 框架格局

| 框架 | Harness 覆盖度 | 适合 |
|------|--------------|------|
| **LangGraph** | 上下文 + 记忆 + 工具 + 反馈 | ⭐ 生产首选，状态图编排 |
| **CrewAI** | 工具 + 上下文 + 简易记忆 | 快速原型、Demo |
| **Claude SDK** | 全套（MCP 原生、Computer Use） | MCP 深度集成场景 |

### 6.2 2026 关键趋势

| 趋势 | 对 Harness 的影响 |
|------|-----------------|
| **MCP 成为标准**（OpenAI 跟进） | 工具系统从「自定义注册」→「MCP Server 发现」 |
| **窗口军备竞赛降温**（边际收益递减，注意力稀释成瓶颈） | 上下文管理重要性 > 窗口大小 |
| **Agent-to-Agent 协议**（Google A2A、Anthropic Agent Protocol） | Agent 间通信走 Google A2A 协议；Harness 需支持 Agent 间通信（服务网格） |
| **记忆即服务**（Mem0、LangMem 等中间件） | 记忆层抽象为独立服务，Redis-as-a-Service |
| **可观测性刚需**（Langfuse、Arize APM 成熟） | 反馈环路从「加分项」→「上线前置条件」 |

### 6.3 生产级检查清单

```
□ 工具调用有超时+熔断（不能让一个慢工具拖死整个 Agent）
□ 工具结果有截断（10MB API 响应不可原样塞 LLM）
□ 代码执行在沙箱（生产绝不裸 exec）
□ 上下文有 GC 策略（Compaction 或 Reset）
□ 记忆有 TTL（偏好过期、旧对话归档）
□ 所有 LLM 调用有 Trace（谁、何时、多少 Token、产出什么）
□ 反馈环路有阈值告警（Faithfulness < 0.8 → 通知 on-call）
□ 大结果落盘（>2000 token 不直接塞 prompt）
```

---

## 7. 面试要点

### 7.1 3 分钟讲完六层架构

画架构图，逐层一句话：①文件系统层=Agent的外存，大结果落盘只传引用；②工具系统层=SPI+RPC，渐进式注册；③记忆层=四种记忆独立存储，各司其职；④沙箱层=五层纵深防御，LLM代码不可信；⑤上下文管理层=窗口预算+渐进披露+GC策略；⑥反馈环路=LLM-as-a-Judge+外部验证，自纠闭环。

### 7.2 必问五题

**Q1：上下文太长怎么办？** 话题延续→Compaction（压缩保留）；切换→Reset（截断重建）。要有主动策略，不能等窗口满了让模型随机丢弃。类比 JVM GC。

**Q2：为什么需要文件系统层？** ① Token 成本线性累积不可持续；② Lost-in-the-Middle 中间信息忽略率 40%+；③ 无法跨会话/跨 Agent 复用。

**Q3：工具系统怎么做渐进式注册？** 按执行阶段分批：意图识别→分析工具 / 执行→领域工具 / 输出→格式化工具。类比分层 ClassLoader。

**Q4：沙箱为什么要五层防御？** LLM 代码不可信，单靠 Prompt 是安全幻觉。Swiss Cheese Model：每层有漏洞但五层叠加，攻击者需同时穿透。类比 Web 纵深防御。

**Q5：怎么评估 Harness 设计好坏？** 三个硬指标：Token 效率、安全边界（最坏破坏程度）、可恢复性（断点续传）。比设计模式「优雅」重要得多。

### 7.3 关键词速查

| 术语 | 一句话 |
|------|--------|
| Agent Harness | Model 是大脑，Harness 是神经系统+骨骼，管执行/约束/记忆/反馈 |
| Context Compaction | LLM 压缩历史为结构化摘要，3:1~10:1 压缩比，保留核心信息 |
| Context Reset | 丢弃大部分历史重建上下文，类比 JVM Full GC |
| Progressive Disclosure | 分层按需加载，不一次性全塞 prompt |
| Lost-in-the-Middle | 长 prompt 中间位置信息被模型系统性忽略 |
| Sandbox | 代码执行隔离，五层纵深防御 |
| LLM-as-a-Judge | 用 LLM 评估 LLM，组成自我修正闭环 |
| MCP | 工具/资源标准化发现协议，2026 已成行业标准 |
| Token Budget | 上下文窗口各模块的分配预算，按场景动态调整 |
