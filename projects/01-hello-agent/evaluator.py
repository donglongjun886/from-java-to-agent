"""
Day 4 Part 1 — LLM-as-a-Judge 评估器

核心思路：
  用一个独立的 LLM 调用，扮演"技术评委"，对 Agent 的回答进行多维度打分。
  Evaluator 的 System Prompt 是评估标准（宪法），User Message 是待评估内容。

三个实验：
  实验1: 单条评估 — 对一条 QA 按四维度打分 + 输出结构化 JSON
  实验2: 三态对比 — 把 Day 3 的 System Prompt 三态输出拉通打分，验证"角色+约束+格式"是否胜出
  实验3: 评估器校准 — 同一个输出评两次，看 Evaluator 自身的一致性
"""

import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"

# ============================================================
# 评估 Prompt 模板
# ============================================================

EVALUATOR_SYSTEM_PROMPT = """你是一个严格的技术评审专家。你的任务是对「AI 助手」的回答进行多维度打分。

评分规则：
1. 对每个维度给出 1-5 的整数分数
2. 每个分数必须有具体理由，引用回答中的原文作为证据
3. 输出必须是严格的 JSON 格式，不要包含任何其他文字

四个评估维度：

- accuracy（准确性）：回答中的事实/技术细节是否正确？代码是否能编译运行？
  1=严重事实错误  3=部分正确但有瑕疵  5=完全准确

- relevance（相关性）：是否直接回答了用户的问题，有没有跑题？
  1=完全跑题  3=部分相关但有冗余  5=精准命中

- completeness（完整性）：是否覆盖了问题要求的所有要点？
  1=严重遗漏  3=覆盖主要要点但有缺失  5=全面覆盖

- format_quality（格式规范性）：输出结构是否清晰、格式是否符合要求
  （如要求 Markdown 则看是否用了标题/列表/代码块）？
  1=格式混乱  3=有基本结构但不规范  5=格式优秀

输出 JSON 格式：
{
  "accuracy": {"score": 整数, "reason": "理由（引用原文）"},
  "relevance": {"score": 整数, "reason": "理由（引用原文）"},
  "completeness": {"score": 整数, "reason": "理由（引用原文）"},
  "format_quality": {"score": 整数, "reason": "理由（引用原文）"},
  "overall": {"score": 整数, "summary": "一句话总评"}
}
"""


def build_eval_user_prompt(question: str, answer: str, expected_format: str = "无特定要求") -> str:
    """构造评估输入：用户问题 + Agent 回答 + 期望格式"""
    return f"""请对以下 AI 助手的回答进行评估。

【用户问题】
{question}

【期望输出格式】
{expected_format}

【AI 助手的回答】
{answer}"""


def evaluate(question: str, answer: str, expected_format: str = "无特定要求", verbose: bool = False) -> dict:
    """调用 Evaluator LLM，返回打分结果。verbose=True 时打印原始 JSON。"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": build_eval_user_prompt(question, answer, expected_format)},
        ],
        temperature=0.1,  # 评估用低温度，保证一致性
        max_tokens=800,
        response_format={"type": "json_object"},  # 强制 JSON 输出
    )
    raw = response.choices[0].message.content
    if verbose:
        print(f"\n  [Evaluator 原始 JSON]\n  {json.dumps(json.loads(raw), indent=2, ensure_ascii=False).replace(chr(10), chr(10)+'  ')}")
    return json.loads(raw)


def print_scores(result: dict, label: str = ""):
    """格式化打印评分结果"""
    header = f"  [{label}]" if label else ""
    dims = ["accuracy", "relevance", "completeness", "format_quality"]
    scores = [f"{d}={result[d]['score']}" for d in dims]
    print(f"{header} {' | '.join(scores)} | overall={result['overall']['score']}")


# ============================================================
# 实验1: 单条评估
# ============================================================
print("=" * 60)
print("  实验1: 单条 QA 的四维度评估")
print("=" * 60)

# 模拟一个 Agent 的回答（故意混合正确和问题）
question = "用 Java 实现线程安全的单例模式"
good_answer = """### ① 代码实现（线程安全）

```java
public class Singleton {
    private static volatile Singleton instance;

    private Singleton() {
        if (instance != null) {
            throw new RuntimeException("Use getInstance() to get the singleton.");
        }
    }

    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

### ② 线程安全性说明
1. **volatile** 关键字保证多线程间的可见性，并禁止指令重排序
2. **synchronized** 块保证同一时刻只有一个线程进入临界区
3. **双重检查**（DCL）：第一次 null 检查避免每次调用都加锁，提升性能
4. 构造方法中的反射攻击检测提供额外防御

### ③ 适用场景分析
适用于需要全局唯一实例的场景，如配置管理器、连接池、日志工厂等。
DCL 方案在 JDK 5+ 环境下是安全且高性能的选择。"""

bad_answer = """单例模式就是只创建一个实例，用 static 就行。

```java
public class Singleton {
    public static Singleton instance = new Singleton();
}
```

这样就线程安全了。"""

print("\n【好回答评估结果】")
result1 = evaluate(question, good_answer, "Markdown 格式，包含代码/线程安全说明/适用场景三部分")
print_scores(result1, "好回答")
print(f"  总评: {result1['overall']['summary']}")

print("\n【差回答评估结果】")
result2 = evaluate(question, bad_answer, "Markdown 格式，包含代码/线程安全说明/适用场景三部分")
print_scores(result2, "差回答")
print(f"  总评: {result2['overall']['summary']}")

print("\n  💡 观察：差回答在 accuracy（饿汉式也是对的但没说清楚）和 completeness（缺两部分）上明显更低")

# ============================================================
# 实验2: 三态对比 —— 量化 Day 3 的结论
# ============================================================
print("\n" + "=" * 60)
print("  实验2: System Prompt 三态对比 — 用打分验证直觉")
print("  问题: " + question)
print("=" * 60)

# Day 3 的三个输出（从 agent_skeleton.py 的实际运行结果截取关键部分）
sys_prompt_outputs = {
    "无 System Prompt": (
        "无特定要求",
        """单例模式的实现有多种方式，比如饿汉式、懒汉式、枚举等。饿汉式在类加载时就创建实例，
        懒汉式在第一次调用时创建。双重检查锁定（DCL）是常用的线程安全懒汉实现。
        使用 volatile 和 synchronized 关键字保证线程安全。"""
    ),
    "简单角色": (
        "无特定要求",
        """单例模式确保一个类只有一个实例。Java 中最常用的是双重检查锁定（Double-Checked Locking），
        通过 volatile + synchronized 实现线程安全。还有饿汉式和枚举方式，各有优缺点。"""
    ),
    "角色+约束+格式": (
        "Markdown 格式，包含代码/线程安全说明/适用场景三部分",
        good_answer,  # 用上面的好回答模拟
    ),
}

print()
baseline_scores = {}
for label, (fmt, output) in sys_prompt_outputs.items():
    result = evaluate(question, output, fmt)
    baseline_scores[label] = result
    print_scores(result, label)
    time.sleep(0.3)  # 避免 API 限流

print("\n  📊 对比结论:")
print(f"    无 SP:     overall={baseline_scores['无 System Prompt']['overall']['score']}")
print(f"    简单角色:   overall={baseline_scores['简单角色']['overall']['score']}")
print(f"    角色+约束:   overall={baseline_scores['角色+约束+格式']['overall']['score']}")
print("  🎯 预期：角色+约束+格式组 在 completeness 和 format_quality 上显著更高")
print("     这就是 System Prompt '瘦但准'的量化证据")

# ============================================================
# 实验3: 评估器校准 — 同一个输出评两次
# ============================================================
print("\n" + "=" * 60)
print("  实验3: 评估器一致性 — 同一输出评两次")
print("=" * 60)

print("\n  第一次评估:")
r1 = evaluate(question, good_answer, "Markdown 格式")
print_scores(r1, "第1次")

time.sleep(0.3)

print("\n  第二次评估:")
r2 = evaluate(question, good_answer, "Markdown 格式")
print_scores(r2, "第2次")

# 比较两次的一致性
print("\n  一致性分析:")
for dim in ["accuracy", "relevance", "completeness", "format_quality", "overall"]:
    s1, s2 = r1[dim]["score"], r2[dim]["score"]
    diff = abs(s1 - s2)
    bar = "✅" if diff == 0 else ("⚠️" if diff == 1 else "❌")
    print(f"    {bar} {dim}: {s1} vs {s2} (差 {diff})")

print("\n  💡 温度=0.1 下两次评估应高度一致。如果出现 ≥2 分的偏差，")
print("     说明评估 prompt 需要更精确（维度定义不够清晰）。")

print("\n" + "=" * 60)
print("  三个实验完成。核心收获:")
print("  1. LLM-as-a-Judge = System Prompt(评分标准) + User(QA对) → JSON打分")
print("  2. 四个维度覆盖正确性/相关性/完整性/格式 — 能捕获人直觉中的'好坏'")
print("  3. Baseline 对比让优化有方向 — 不是'感觉更好'而是'分数更高'")
print("  4. 低温度+明确维度定义 = 评估一致性高（可做自动化回归）")
print("=" * 60)
