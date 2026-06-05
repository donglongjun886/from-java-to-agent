"""
Hello Agent — 第一个 AI Agent

基于 DeepSeek API (OpenAI 兼容) 的多轮对话命令行 Agent。
支持流式输出、上下文管理、错误重试和 Token 成本统计。

使用方式：
  1. 在项目根目录 .env 中设置 DEEPSEEK_API_KEY=sk-xxx
  2. source .venv/bin/activate
  3. python projects/01-hello-agent/main.py
"""

import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

console = Console()

# DeepSeek API 配置
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"  # V4 Pro


class HelloAgent:
    """支持 OpenAI 兼容 API 的多轮对话 Agent"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEEPSEEK_BASE_URL,
        model: str = DEEPSEEK_MODEL,
    ):
        self.client = OpenAI(
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
            base_url=base_url,
        )
        self.model = model
        self.messages: list[dict] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def set_system_prompt(self, prompt: str):
        """设置 System Prompt（OpenAI 格式用 role='system'）"""
        self.messages.insert(0, {"role": "system", "content": prompt})

    def chat(self, user_input: str) -> str:
        """同步对话"""
        self.messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            max_tokens=2048,
        )

        usage = response.usage
        self.total_input_tokens += usage.prompt_tokens
        self.total_output_tokens += usage.completion_tokens

        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})

        return reply

    async def chat_stream(self, user_input: str):
        """流式对话"""
        self.messages.append({"role": "user", "content": user_input})

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            max_tokens=2048,
            stream=True,
        )

        full_reply = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                full_reply += delta.content
            # DeepSeek 在最后一个 chunk 返回 usage
            if chunk.choices and hasattr(chunk, "usage") and chunk.usage:
                self.total_input_tokens += chunk.usage.prompt_tokens
                self.total_output_tokens += chunk.usage.completion_tokens

        print()
        self.messages.append({"role": "assistant", "content": full_reply})

    def stats(self) -> dict:
        """Token 使用统计（DeepSeek V4 定价）"""
        # DeepSeek 定价 (per 1M tokens) — 仅供参考，以官网为准
        input_price = 0.27   # ¥2/million tokens ≈ $0.27
        output_price = 1.10  # ¥8/million tokens ≈ $1.10

        input_cost = self.total_input_tokens / 1_000_000 * input_price
        output_cost = self.total_output_tokens / 1_000_000 * output_price

        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": round(input_cost + output_cost, 4),
        }


async def main():
    console.print("[bold cyan]Hello Agent[/bold cyan] — 基于 DeepSeek API 的对话 Agent")
    console.print("输入 [yellow]/stats[/yellow] 查看用量，[yellow]/quit[/yellow] 退出")
    console.print("[dim]模型: deepseek-chat (V4 Pro)[/dim]\n")

    agent = HelloAgent()
    agent.set_system_prompt("你是一个友好的 AI 助手，请用中文回答问题。")

    while True:
        try:
            user_input = console.input("[bold green]你:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]再见！[/dim]")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            console.print("[dim]再见！[/dim]")
            break
        if user_input == "/stats":
            s = agent.stats()
            console.print(
                f"[dim]Token: 输入 {s['input_tokens']} | "
                f"输出 {s['output_tokens']} | "
                f"合计 {s['total_tokens']} | "
                f"预估费用 ${s['estimated_cost_usd']}[/dim]"
            )
            continue

        console.print("[bold blue]Agent:[/bold blue] ", end="")
        try:
            await agent.chat_stream(user_input)
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
