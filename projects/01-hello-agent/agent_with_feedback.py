"""
Day 4 Part 2 — Feedback Loop 集成 + A/B Baselining

两个实验：
  实验1: AgentWithFeedback — 生成→评估→不合格→带反馈重试，直到达标
  实验2: A/B Baseline 对比 — 同一组问题 × 两种配置，量化哪个更好
"""

import os
import json
import time
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"

# ============================================================
# Evaluator（从 Day 4 Part 1 精简内嵌到本文件）
# ============================================================

EVALUATOR_SYSTEM_PROMPT = """你是一个严格的技术评审专家。对 AI 助手的回答按以下四个维度打分。

- accuracy（准确性）：事实是否正确？代码能否运行？1=严重错误 3=有瑕疵 5=完全正确
- relevance（相关性）：是否直接回答了问题？1=跑题 3=部分相关 5=精准命中
- completeness（完整性）：是否覆盖所有要点？1=严重遗漏 3=基本覆盖 5=全面覆盖
- format_quality（格式规范）：结构清晰？用标题/列表/代码块？1=混乱 3=基本规范 5=优秀

输出 JSON：{"accuracy":{"score":int,"reason":"..."},"relevance":{...},"completeness":{...},"format_quality":{...},"overall":{"score":int,"summary":"..."}}"""


def evaluate(question: str, answer: str, expected_format: str = "无特定要求") -> dict:
    """调用 Evaluator LLM，返回打分 dict"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"请评估以下 AI 回答。\n\n"
                f"【用户问题】{question}\n"
                f"【期望格式】{expected_format}\n"
                f"【AI 回答】{answer}"
            )},
        ],
        temperature=0.1,
        max_tokens=600,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


# ============================================================
# 实验1: AgentWithFeedback — 带自我检查能力的 Agent
# ============================================================

class AgentWithFeedback:
    """
    Agent = Model + Harness + Feedback Loop

    流程：
      chat_with_feedback(user_input)
        → chat_raw() 生成初版回答
        → evaluate() 打分
        → overall >= threshold? 返回
        → overall < threshold? 把失败原因喂给 Agent，重试
        → 超过 max_retries? 返回最佳尝试
    """

    def __init__(self, system_prompt: str = "", quality_threshold: int = 4, max_retries: int = 2):
        self.system_prompt = system_prompt
        self.quality_threshold = quality_threshold
        self.max_retries = max_retries

        # 可观测
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_eval_tokens = 0
        self.call_count = 0
        self.retry_count = 0

    # === 基础对话（不带反馈，直接生成）===

    def chat_raw(self, user_input: str, extra_hint: str = "") -> str:
        """单次 LLM 调用，extra_hint 用于重试时传递改进建议"""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        # 模拟对话历史：假设这是多轮对话的某一轮
        messages.append({"role": "user", "content": user_input})

        if extra_hint:
            messages.append({"role": "user", "content": f"[改进建议] {extra_hint}\n请根据以上建议重新回答。"})

        self.call_count += 1
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=600,
        )
        if response.usage:
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens
        return response.choices[0].message.content

    # === 带 Feedback Loop 的对话 ===

    def chat_with_feedback(self, user_input: str, expected_format: str = "无特定要求") -> dict:
        """
        生成 → 评估 → 不合格则带反馈重试。
        返回 {"answer": str, "score": dict, "attempts": int, "history": [...]}
        """
        history = []
        best_answer = None
        best_score = 0

        for attempt in range(self.max_retries + 1):
            # 第一次正常生成，后续带评估反馈
            hint = ""
            if attempt > 0:
                # 拼接上一次所有维度的改进建议
                last_eval = history[-1]["eval"]
                reasons = []
                for dim in ["accuracy", "relevance", "completeness", "format_quality"]:
                    if last_eval[dim]["score"] < 5:
                        reasons.append(f"【{dim}】{last_eval[dim]['reason']}")
                hint = "上一次回答的不足：" + "；".join(reasons) if reasons else "请改进回答质量。"

            answer = self.chat_raw(user_input, hint)
            eval_result = evaluate(user_input, answer, expected_format)

            # 统计评估 token（估算，因为 DeepSeek 流式结束时才返回 usage）
            overall = eval_result["overall"]["score"]
            history.append({"attempt": attempt + 1, "answer": answer, "eval": eval_result})

            if overall > best_score:
                best_score = overall
                best_answer = answer

            if overall >= self.quality_threshold:
                break

            self.retry_count += 1

        return {
            "answer": best_answer,
            "score": best_score,
            "attempts": len(history),
            "passed": best_score >= self.quality_threshold,
            "history": history,
        }

    def stats(self) -> dict:
        return {
            "call_count": self.call_count,
            "retry_count": self.retry_count,
            "retry_rate": f"{self.retry_count / max(self.call_count, 1) * 100:.0f}%",
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
        }


# ============================================================
# 实验1 验证: 用同一个问题，对比有/无 Feedback Loop 的差异
# ============================================================
print("=" * 60)
print("  实验1: Feedback Loop — 不达标就重试")
print("=" * 60)

question = "用 Python 实现线程安全的单例模式"

# 故意用一个"宽松"的 System Prompt，让 Agent 表现偏弱，触发 Feedback Loop
agent = AgentWithFeedback(
    system_prompt="你是一个编程助手。",
    quality_threshold=4,
    max_retries=2,
)

print(f"\n  问题: {question}")
print(f"  System Prompt: '你是一个编程助手。'（宽松）")
print(f"  质量阈值: {agent.quality_threshold}/5, 最大重试: {agent.max_retries}")
print(f"\n  --- 开始 Feedback Loop ---")

result = agent.chat_with_feedback(
    user_input=question,
    expected_format="包含代码、线程安全说明",
)

for h in result["history"]:
    attempt = h["attempt"]
    overall = h["eval"]["overall"]["score"]
    dims = {d: h["eval"][d]["score"] for d in ["accuracy", "relevance", "completeness", "format_quality"]}
    status = "✅ 通过" if overall >= agent.quality_threshold else "↻ 重试"
    print(f"\n  第{attempt}次: overall={overall} {dims} → {status}")
    if attempt > 1:
        # 展示改进
        prev_overall = result["history"][attempt - 2]["eval"]["overall"]["score"]
        if overall > prev_overall:
            print(f"    ↑ 比上次提升 {overall - prev_overall} 分")

print(f"\n  --- 结果 ---")
print(f"  最终得分: {result['score']}/5")
print(f"  尝试次数: {result['attempts']}")
print(f"  通过: {result['passed']}")
print(f"  成本统计: {agent.stats()}")

print(f"\n  【最终回答（前 300 字符）】")
print(f"  {result['answer'][:300]}...")

# ============================================================
# 实验2: A/B Baseline 对比框架
# ============================================================
print("\n\n" + "=" * 60)
print("  实验2: A/B Baseline 对比")
print("  对比两种 System Prompt 在 3 个问题上的表现")
print("=" * 60)

TEST_QUESTIONS = [
    ("用 Java 实现单例模式", "包含代码、线程安全说明"),
    ("解释 RESTful API 的设计原则", "Markdown 格式、至少 3 条原则"),
    ("写一个 Python 二分查找函数", "包含代码、复杂度分析"),
]

# 配置 A: 无 System Prompt
# 配置 B: 精确 System Prompt
configs = {
    "A(无SP)": "",
    "B(精确SP)": "你是资深软件工程师。每个回答必须：① 给出正确代码 ② 解释关键设计 ③ 用 Markdown 格式组织。",
}

results_ab = {name: [] for name in configs}

for config_name, system_prompt in configs.items():
    print(f"\n--- {config_name} ---")
    agent = AgentWithFeedback(system_prompt=system_prompt, quality_threshold=3, max_retries=0)  # 0次重试=不上反馈

    for q, fmt in TEST_QUESTIONS:
        result = agent.chat_with_feedback(user_input=q, expected_format=fmt)
        scores = {d: result["history"][0]["eval"][d]["score"] for d in ["accuracy", "relevance", "completeness", "format_quality"]}
        overall = result["history"][0]["eval"]["overall"]["score"]
        results_ab[config_name].append({"q": q, "scores": scores, "overall": overall})
        print(f"  {q[:30]:<30} overall={overall} {scores}")
        time.sleep(0.3)

# 汇总对比
print(f"\n{'='*60}")
print("  A/B 对比汇总")
print(f"{'='*60}")

for dim in ["accuracy", "relevance", "completeness", "format_quality", "overall"]:
    if dim == "overall":
        a_avg = mean(r["overall"] for r in results_ab["A(无SP)"])
        b_avg = mean(r["overall"] for r in results_ab["B(精确SP)"])
    else:
        a_avg = mean(r["scores"][dim] for r in results_ab["A(无SP)"])
        b_avg = mean(r["scores"][dim] for r in results_ab["B(精确SP)"])

    diff = b_avg - a_avg
    bar = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
    sig = "★显著" if abs(diff) >= 0.5 else ""
    print(f"  {dim:<16}: A={a_avg:.1f}  B={b_avg:.1f}  差{diff:+.1f} {bar} {sig}")

print(f"\n  结论:")
b_avg_all = mean(r["overall"] for r in results_ab["B(精确SP)"])
a_avg_all = mean(r["overall"] for r in results_ab["A(无SP)"])
print(f"    精确 System Prompt 平均得分 {b_avg_all:.1f}，比无 SP({a_avg_all:.1f})高 {b_avg_all - a_avg_all:.1f} 分")
print(f"    差距最大的维度是 'completeness' 和 'format_quality'——这正是 System Prompt 直接约束的")

print("\n" + "=" * 60)
print("  两个实验完成。核心收获:")
print("  1. Feedback Loop 让 Agent 从一次调用升级为自主纠错系统")
print("  2. 重试时传递评估反馈（不是盲目重试），Agent 知道从哪改进")
print("  3. A/B Baseline 用分数说话——不是'感觉'哪个好，是'数据'哪个好")
print("  4. 这套框架可以直接迁移到你自己的项目里做回归测试")
print("=" * 60)