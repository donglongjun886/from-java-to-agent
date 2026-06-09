"""
Day 3 Part 2 — System Prompt 对比 + Agent 架构骨架

两个核心实验：
  实验A: 同一问题 × 三种 System Prompt → 观察角色/约束/格式的影响
  实验B: Agent 类骨架 → 体现「Model + Harness + Feedback Loop」三层架构
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# ============================================================
# 实验A: System Prompt 三态对比
# ============================================================

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"
QUESTION = "用 Java 实现单例模式"


def ask(system_prompt: str | None, label: str):
    """发一次请求，打印结果摘要"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": QUESTION})

    t0 = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=400,
    )
    elapsed = time.time() - t0
    content = response.choices[0].message.content
    tokens = response.usage.completion_tokens if response.usage else 0

    print(f"\n{'─'*60}")
    print(f"  [{label}]")
    print(f"  System Prompt: {system_prompt or '(无)'}")
    print(f"  耗时: {elapsed:.1f}s | 输出 token: {tokens} | 输出长度: {len(content)} 字符")
    print(f"{'─'*60}")
    print(content[:500])  # 前 500 字符
    if len(content) > 500:
        print("  ...(截断)")


print("=" * 60)
print("  实验A: System Prompt 三态对比")
print("  问题: " + QUESTION)
print("=" * 60)

# 状态1: 无 System Prompt — 模型自由发挥
ask(None, "状态1: 无 System Prompt")

# 状态2: 简单角色 — 只定义了身份，没约束格式
ask("你是一个编程助手。", "状态2: 简单角色")

# 状态3: 角色 + 约束 + 格式 — 完整的 Agent 指令
ask(
    "你是资深 Java 架构师。回复必须包含以下三部分，用 Markdown 格式：\n"
    "① 代码实现（线程安全）\n"
    "② 线程安全性说明\n"
    "③ 适用场景分析",
    "状态3: 角色 + 约束 + 格式",
)

print("\n" + "=" * 60)
print("  实验A 小结:")
print("  状态1 → 输出不可控（可能给 Python、可能啰嗦、可能简短）")
print("  状态2 → 方向对了，但格式/深度不可预期")
print("  状态3 → 输出结构化、深度可控、可直接做下游解析")
print("=" * 60)


# ============================================================
# 实验B: Agent 类骨架 — Model + Harness + Feedback Loop
# ============================================================
print("\n\n")
print("=" * 60)
print("  实验B: Agent 架构骨架")
print("  Agent = Model（大脑）+ Harness（框架）+ Feedback Loop（反馈环）")
print("=" * 60)


class AgentSkeleton:
    """
    Agent 三层架构骨架。

    Model 层:  client + model — 负责推理/生成，可替换（DeepSeek/Claude/...）
    Harness 层: messages/tools/sandbox/observability — 模型之外的一切
    Feedback 层: validate/retry/fallback — 外部验证 + 自我纠错
    """

    def __init__(self, api_key: str, base_url: str, model: str = "deepseek-chat"):
        # ── Model 层 ──
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

        # ── Harness 层: 状态管理 ──
        self._system_prompt: str | None = None
        self.messages: list[dict] = []

        # ── Harness 层: 可观测 ──
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
        self.error_count = 0

        # ── Harness 层: 工具（Day4 正式引入，今天先占位）──
        self.tools: list[dict] = []

    # === Model 接口 ===

    def set_system_prompt(self, prompt: str):
        """
        设置 Agent 的「宪法」。
        System Prompt 应该瘦：只写不可变规则，可变知识放到工具/文件系统里。
        """
        self._system_prompt = prompt

    def _build_messages(self, user_input: str) -> list[dict]:
        """Harness 层负责组装 messages，Model 层只负责推理"""
        msgs = []
        if self._system_prompt:
            msgs.append({"role": "system", "content": self._system_prompt})
        msgs.extend(self.messages)
        msgs.append({"role": "user", "content": user_input})
        return msgs

    def chat(self, user_input: str, max_retries: int = 2) -> str:
        """
        同步对话 + Feedback Loop（重试机制）。

        Feedback Loop 的三层：
          1. 正常返回 → 直接使用
          2. API 报错 → 重试（exponential backoff 简化版）
          3. 超过重试次数 → 抛出异常（Human-in-the-Loop 介入点）
        """
        for attempt in range(max_retries + 1):
            try:
                self.call_count += 1
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self._build_messages(user_input),
                    max_tokens=2048,
                )

                # Harness: 记录用量
                if response.usage:
                    self.total_input_tokens += response.usage.prompt_tokens
                    self.total_output_tokens += response.usage.completion_tokens

                reply = response.choices[0].message.content

                # Harness: 维护对话历史
                self.messages.append({"role": "user", "content": user_input})
                self.messages.append({"role": "assistant", "content": reply})

                return reply

            except Exception as e:
                self.error_count += 1
                if attempt < max_retries:
                    wait = 0.5 * (2**attempt)  # 0.5s → 1s
                    print(f"  [Harness] 调用失败 ({e}), {wait:.1f}s 后重试 (第{attempt+1}次)")
                    time.sleep(wait)
                else:
                    raise

    def chat_stream(self, user_input: str):
        """流式对话（Feedback Loop 省略重试，保持简洁）"""
        self.call_count += 1
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(user_input),
            max_tokens=2048,
            stream=True,
        )

        full_reply = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                full_reply += delta.content
            if hasattr(chunk, "usage") and chunk.usage:
                self.total_input_tokens += chunk.usage.prompt_tokens
                self.total_output_tokens += chunk.usage.completion_tokens

        print()
        self.messages.append({"role": "user", "content": user_input})
        self.messages.append({"role": "assistant", "content": full_reply})

    # === Harness: 可观测接口 ===

    def stats(self) -> dict:
        """Token 用量 + 调用统计"""
        input_cost = self.total_input_tokens / 1_000_000 * 0.27  # DeepSeek 输入 ¥2/1M
        output_cost = self.total_output_tokens / 1_000_000 * 1.10  # DeepSeek 输出 ¥8/1M

        return {
            "model": self.model,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "est_cost_usd": round(input_cost + output_cost, 6),
            "history_turns": len(self.messages) // 2,  # 每轮 = user + assistant
        }

    # === Harness: 上下文管理 ===

    def reset_context(self):
        """重置对话历史（Day4+ 会演化为「上下文重置策略」）"""
        self.messages = []

    def context_size(self) -> int:
        """估算当前上下文 token 数（粗略：1 token ≈ 2 中文字符 ≈ 4 英文字符）"""
        total_chars = sum(len(m.get("content", "")) for m in self.messages)
        if self._system_prompt:
            total_chars += len(self._system_prompt)
        return total_chars // 2  # 中文为主的粗略估算


# === 跑验证 ===

print("\nAgentSkeleton 实例化 + System Prompt 对比验证:\n")

agent = AgentSkeleton(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 用状态3的 System Prompt 初始化
agent.set_system_prompt(
    "你是资深 Java 架构师。回复必须包含以下三部分，用 Markdown 格式：\n"
    "① 代码实现（线程安全）\n"
    "② 线程安全性说明\n"
    "③ 适用场景分析"
)

try:
    reply = agent.chat(QUESTION)
    print(reply[:300])
    print("  ...(完整内容见上方实验A状态3)")
except Exception as e:
    print(f"  [Feedback Loop] 最终失败: {e}")

print(f"\n  [Harness 可观测] {agent.stats()}")

print("\n" + "=" * 60)
print("  实验B 小结:")
print("  Model:     client.chat.completions.create() — 可替换，不是核心壁垒")
print("  Harness:   messages/tools/stats/reset_context — 工程能力分水岭")
print("  Feedback:  retry loop — 让 Agent 从「一次调用」升级为「可靠系统」")
print("=" * 60)