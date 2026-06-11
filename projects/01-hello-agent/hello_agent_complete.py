"""
Hello Agent Complete — Week 1 完整产出

整合了本周所有模块：
  - AgentSkeleton: Chat API 封装 + 流式 + 成本统计
  - Evaluator: LLM-as-a-Judge 四维度评估
  - Feedback Loop: 不合格→带反馈重试
  - Tool Calling: 模型自主调用决策 (get_weather + calculate)

使用方式: source .venv/bin/activate && python projects/01-hello-agent/hello_agent_complete.py
"""

import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"
console = Console()

# ============================================================
# 工具层
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市当前的天气信息",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "数学表达式"}},
                "required": ["expression"],
            },
        },
    },
]

def get_weather(city: str) -> str:
    db = {"杭州": "晴，28°C，湿度 65%", "北京": "多云，22°C，湿度 40%", "深圳": "雷阵雨，31°C，湿度 85%"}
    return db.get(city, f"{city}：暂无数据")

def calculate(expression: str) -> str:
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

TOOL_MAP = {"get_weather": get_weather, "calculate": calculate}

# ============================================================
# 评估层
# ============================================================

EVALUATOR_SYSTEM_PROMPT = """你是一个严格的技术评审专家。对 AI 助手的回答按以下四个维度打分。

- accuracy（准确性）：事实是否正确？代码能否运行？1=严重错误 3=有瑕疵 5=完全正确
- relevance（相关性）：是否直接回答了问题？1=跑题 3=部分相关 5=精准命中
- completeness（完整性）：是否覆盖所有要点？1=严重遗漏 3=基本覆盖 5=全面覆盖
- format_quality（格式规范）：结构清晰？用标题/列表/代码块？1=混乱 3=基本规范 5=优秀

输出 JSON：{"accuracy":{"score":int,"reason":"..."},"relevance":{...},"completeness":{...},"format_quality":{...},"overall":{"score":int,"summary":"..."}}"""


def evaluate(question: str, answer: str, expected_format: str = "无特定要求") -> dict:
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
# Agent 核心
# ============================================================

class HelloAgent:
    """
    Agent 完整实现，覆盖 Harness 六层中已落地的四层：

    Model    → client + model（可替换，不是壁垒）
    Harness  → 工具系统 + 记忆管理 + 上下文工程 + 可观测
    Feedback → 评估打分 + 阈值判断 + 带反馈重试
    """

    def __init__(self, system_prompt: str = "", quality_threshold: int = 4, max_retries: int = 2):
        self.system_prompt = system_prompt
        self.quality_threshold = quality_threshold
        self.max_retries = max_retries
        self.messages: list[dict] = []

        # 可观测
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
        self.retry_count = 0

    # === 基础对话 ===

    def _chat_once(self, user_input: str, extra_hint: str = "", enable_tools: bool = True) -> str:
        """单次 LLM 调用，支持 tools 和重试提示"""
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.extend(self.messages)
        msgs.append({"role": "user", "content": user_input})
        if extra_hint:
            msgs.append({"role": "user", "content": f"[改进建议] {extra_hint}\n请根据以上建议重新回答。"})

        self.call_count += 1
        kwargs = {"model": MODEL, "messages": msgs, "temperature": 0.3, "max_tokens": 800}
        if enable_tools:
            kwargs["tools"] = TOOLS

        response = client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

        if response.usage:
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens

        # Tool Calling 处理
        if msg.tool_calls:
            msgs.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls],
            })
            for tc in msg.tool_calls:
                func = TOOL_MAP.get(tc.function.name)
                if func:
                    result = func(**json.loads(tc.function.arguments))
                    msgs.append({"role": "tool", "tool_call_id": tc.id, "content": result})

            # 第二次调用：基于工具结果生成回复
            self.call_count += 1
            response2 = client.chat.completions.create(
                model=MODEL, messages=msgs, temperature=0.3, max_tokens=800,
            )
            if response2.usage:
                self.total_input_tokens += response2.usage.prompt_tokens
                self.total_output_tokens += response2.usage.completion_tokens
            return response2.choices[0].message.content

        return msg.content

    # === 带 Feedback Loop 的对话 ===

    def chat(self, user_input: str, expected_format: str = "无特定要求") -> str:
        """生成 → 评估 → 不合格带反馈重试"""
        best_answer = None
        best_score = 0

        for attempt in range(self.max_retries + 1):
            hint = ""
            if attempt > 0:
                reasons = []
                for dim in ["accuracy", "relevance", "completeness", "format_quality"]:
                    if last_eval[dim]["score"] < 5:
                        reasons.append(f"【{dim}】{last_eval[dim]['reason']}")
                hint = "上一次回答的不足：" + "；".join(reasons) if reasons else "请改进回答质量。"

            answer = self._chat_once(user_input, hint)
            eval_result = evaluate(user_input, answer, expected_format)
            last_eval = eval_result
            overall = eval_result["overall"]["score"]

            if overall > best_score:
                best_score = overall
                best_answer = answer

            if overall >= self.quality_threshold:
                break
            self.retry_count += 1

        # 维护对话历史
        self.messages.append({"role": "user", "content": user_input})
        self.messages.append({"role": "assistant", "content": best_answer})
        return best_answer

    def chat_stream(self, user_input: str):
        """流式对话（不带 Feedback Loop，保持流畅）"""
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.extend(self.messages)
        msgs.append({"role": "user", "content": user_input})

        self.call_count += 1
        stream = client.chat.completions.create(
            model=MODEL, messages=msgs, max_tokens=800, stream=True, tools=TOOLS,
        )

        full_reply = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                full_reply += delta.content
        print()

        self.messages.append({"role": "user", "content": user_input})
        self.messages.append({"role": "assistant", "content": full_reply})

    # === 可观测 ===

    def stats(self) -> dict:
        input_cost = self.total_input_tokens / 1_000_000 * 0.27
        output_cost = self.total_output_tokens / 1_000_000 * 1.10
        return {
            "model": MODEL,
            "call_count": self.call_count,
            "retry_count": self.retry_count,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "est_cost_usd": round(input_cost + output_cost, 6),
            "history_turns": len(self.messages) // 2,
        }

    def reset_context(self):
        self.messages = []


# ============================================================
# 交互入口
# ============================================================

async def main():
    console.print("[bold cyan]Hello Agent Complete[/bold cyan] — Week 1 完整产出")
    console.print("功能：多轮对话 | Tool Calling | 评估打分 | Feedback Loop")
    console.print("命令：[yellow]/stats[/yellow] 用量 [yellow]/eval[/yellow] 评估上次回答 [yellow]/reset[/yellow] 重置 [yellow]/quit[/yellow] 退出")
    console.print(f"[dim]模型: {MODEL}[/dim]\n")

    agent = HelloAgent(
        system_prompt="你是资深的软件工程师助手。用中文回答问题，代码用 Markdown 格式，给出关键设计说明。",
        quality_threshold=4,
        max_retries=1,
    )

    last_reply = ""
    while True:
        try:
            user_input = console.input("[bold green]你:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]再见！[/dim]")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            break
        if user_input == "/stats":
            s = agent.stats()
            console.print(f"[dim]调用 {s['call_count']} 次 | 重试 {s['retry_count']} 次 | Token {s['total_tokens']} | 费用 ${s['est_cost_usd']}[/dim]")
            continue
        if user_input == "/eval":
            if last_reply:
                result = evaluate("（上一条对话）", last_reply)
                dims = ["accuracy", "relevance", "completeness", "format_quality"]
                scores = " | ".join(f"{d}={result[d]['score']}" for d in dims)
                console.print(f"[dim]评估: {scores} | overall={result['overall']['score']}[/dim]")
            else:
                console.print("[dim]暂无对话可评估[/dim]")
            continue
        if user_input == "/reset":
            agent.reset_context()
            console.print("[dim]对话已重置[/dim]")
            continue

        try:
            last_reply = agent.chat(user_input, "Markdown 格式，给出代码和设计说明")
            console.print(f"[bold blue]Agent:[/bold blue] {last_reply}")
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
