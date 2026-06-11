# Day 4 (2026.06.10) — 项目A（上）+ 评估入门

## Part 1: LLM-as-a-Judge 评估器 ✅

### 核心认知
- LLM-as-a-Judge = System Prompt(评分标准) + User(QA对) → JSON打分
- 四个维度：accuracy / relevance / completeness / format_quality
- 温度 0.1 + response_format json_object = 评估一致性高，可做自动化回归
- Evaluator 单次调用 ~$0.0004

### 代码产出
- `evaluator.py`：三个实验全部跑通
  - 实验1：好vs差回答区分（overall 5 vs 2）
  - 实验2：System Prompt 三态量化对比
  - 实验3：评估器一致性校验（两次0偏差）

## Part 2: Feedback Loop + A/B Baselining ✅

### 核心认知
- Feedback Loop ≠ 盲目重试，重试时传递评估反馈让 Agent 知道从哪改进
- A/B Baseline 用数据说话，不是感觉
- 小样本 A/B 不可靠（3 个问题噪声淹信号），真实场景需要 20-50 个问题

### 代码产出
- `agent_with_feedback.py`：两个实验
  - AgentWithFeedback: 生成→评估→不合格带反馈重试
  - A/B 对比框架: 同组问题×两种配置→四维度均值对比

### 2 个 commit
```
0b79134 feat(hello-agent): Day 4 Part2 — Feedback Loop 集成 + A/B Baselining
9e12e05 feat(hello-agent): Day 4 Part1 — LLM-as-a-Judge 四维度评估器
```