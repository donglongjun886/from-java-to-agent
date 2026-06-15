"""
Day 7 Part 3 — FastAPI 服务化：把 Agent 从 CLI 变成 HTTP 服务

将 hello_agent_complete.py 的 Agent 能力暴露为 RESTful API。
支持流式（SSE）和非流式两种模式，带 Token 统计端点。

启动: python agent_api.py
访问: http://localhost:8000/docs（FastAPI 自动生成的 Swagger 文档）
"""

import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import uvicorn

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"

app = FastAPI(title="Hello Agent API", version="1.0")

# ============================================================
# 工具层（和之前完全一样）
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

TOOL_MAP = {
    "get_weather": lambda city: (
        {"杭州": "晴，28°C，湿度 65%", "北京": "多云，22°C，湿度 40%", "深圳": "雷阵雨，31°C，湿度 85%"}
    ).get(city, f"{city}：暂无数据"),
    "calculate": lambda expression: f"{expression} = {eval(expression, {'__builtins__': {}}, {})}",
}

SYSTEM_PROMPT = "你是资深的软件工程师助手。用中文回答，代码用 Markdown 格式。"

# ============================================================
# 路由
# ============================================================

@app.get("/")
def root():
    return {"service": "Hello Agent API", "endpoints": ["/chat", "/chat/stream", "/stats"]}


@app.get("/chat")
def chat_sync(msg: str = Query(..., description="用户消息")):
    """非流式对话：发送消息 → 返回完整回复 + 统计"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": msg}]
    t0 = time.time()

    # 第一次调用
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, tools=TOOLS, temperature=0.3, max_tokens=800,
    )
    choice = resp.choices[0]

    # Tool Calling 处理
    tool_calls = []
    if choice.message.tool_calls:
        # 追加 assistant 的 tool_calls
        messages.append({
            "role": "assistant",
            "content": choice.message.content,
            "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in choice.message.tool_calls],
        })
        # 执行工具
        for tc in choice.message.tool_calls:
            func = TOOL_MAP.get(tc.function.name)
            if func:
                result = func(**json.loads(tc.function.arguments))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                tool_calls.append({"tool": tc.function.name, "args": tc.function.arguments, "result": result})
        # 第二次调用
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.3, max_tokens=800,
        )
        choice = resp.choices[0]

    usage = resp.usage
    return {
        "reply": choice.message.content,
        "tool_calls": tool_calls if tool_calls else None,
        "stats": {
            "latency_ms": round((time.time() - t0) * 1000),
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        },
    }


@app.get("/chat/stream")
async def chat_stream(msg: str = Query(..., description="用户消息")):
    """流式对话：SSE 逐 token 推送"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": msg}]

    async def generate():
        stream = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, max_tokens=800, stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield f"data: {delta.content}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/stats")
def stats():
    """占位：全局统计端点（生产环境接 Langfuse）"""
    return {"model": MODEL, "note": "生产环境接入 Langfuse 后可返回全量调用统计"}


if __name__ == "__main__":
    print(f"Hello Agent API → http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
