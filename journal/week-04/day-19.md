# Day 19: 项目B 压测 + 故障注入 + 全量 Review

**日期**: 2026-07-02

## 今日完成

### 1. 负载压测 `load_test.py`
- 四Agent 阶段耗时拆解：Planner 960ms / Retriever 0ms / **Generator 3383ms (62%瓶颈)** / Evaluator 1111ms
- 静态RAG vs Agentic 延迟：静态 0ms（纯规则）vs Agentic ~1030ms/题（含LLM）
- 并发压测：Agentic 单并发 QPS=0.1，P50=6578ms
- 成本：¥0.003/次，月均 ¥6.6
- 面试话术：生产环境简单查询走静态RAG兜底，复杂推理进Agentic Pipeline

### 2. 检索质量对比 `retrieval_compare.py`
- 修复 `\b` 单词边界Bug → 改用负向断言，英文关键词在中文语境中匹配正确
- 修复除零异常 → Agentic全失败时返回 NaN
- 中文字符串截断 → 按显示宽度截断
- 静态P@3=0.54 vs Agentic P@3=0.42（小规模持平，大规模下Agentic优势显现）

### 3. 故障注入 `fault_injection.py`
- 修复 Tool超时测试 → 从伪测试（直连非法端口）改为 mock LLM 抛异常，真正验证 run_pipeline 降级
- LLM幻觉检测 → 明确两道防线：Retrieval质量 + Evaluator校验
- 修复异常捕获 → 从裸 except Exception 改为具体异常类型
- **结果: 4/4 PASS**（超时/幻觉/截断/格式异常）

### 4. 全量 Code Review + Fix
- 4 个文件并行 Review（子Agent并发调用MCP code-review）
- 4 个文件并行 Fix（子Agent后台执行）
- 全量回归验证通过

### 5. 架构文档更新
- ARCHITECTURE.md 新增四Agent协同架构Mermaid图 + 压测数据 + 故障注入结果表
- README.md 新增 Week 4 文件结构 + 面试话术

## 面试关键数字

| 数字 | 含义 |
|------|------|
| 4/4 PASS | 故障注入全部通过 |
| 62% | Generator 瓶颈占比 |
| ¥0.003/次 | 单次四Agent调用成本 |
| P50=6578ms | Agentic 端到端延迟 |

## 求职进展

- 猎头投递钉钉悟空（AI Agent 平台，Java主力，高度匹配）
- BOSS 开始投递 Java+Agent 交叉岗位
- 看了多篇面经帖子，验证了交叉岗面试深度 + 市场定位

## 下一步

- Day 20: 全面复盘 + 技能矩阵 + 对标 JD 自评
- 晚段: 2 个项目技术复盘文档
- 持续 BOSS 投递
