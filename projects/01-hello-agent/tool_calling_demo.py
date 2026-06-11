"""
Day 5 Part 1 — Tool Calling 概念初体验

核心认知：
  Function Calling 不是 Agent 自己去执行函数——是 Agent 告诉你的代码"我要调哪个函数、传什么参数"，
  你的代码去执行，然后把结果还给 Agent。Agent 负责「决策」，代码负责「执行」。

两个实验：
  实验1: 单工具 — 定义一个 get_weather，观察模型自主决策要不要调
  实验2: 多工具 — 同时给 weather 和 calc，看模型怎么选
"""

import os
import json
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
# "真实"的函数实现 — 你的代码，不是模型的代码
# ============================================================

def get_weather(city: str) -> str:
    """模拟天气查询（生产环境这里调天气 API）"""
    weather_db = {
        "杭州": "晴，28°C，湿度 65%",
        "北京": "多云，22°C，湿度 40%",
        "深圳": "雷阵雨，31°C，湿度 85%",
    }
    return weather_db.get(city, f"{city}：暂无数据")


def calculate(expression: str) -> str:
    """安全的数学计算（生产环境这可能是数据库查询/API调用）"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


# ============================================================
# 工具定义 — 告诉模型"我有这些能力"（JSON Schema）
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市当前的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如 杭州、北京、深圳",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算，如加减乘除",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '3.14 * 2 + 100'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

# 函数名 → 实际函数映射（你的代码的"工具注册表"）
TOOL_MAP = {
    "get_weather": get_weather,
    "calculate": calculate,
}


def run_conversation(user_input: str, tools: list = TOOLS, verbose: bool = True):
    """
    Tool Calling 的完整一轮流程：

    ① 发 user message + tools 定义 → 模型返回 finish_reason="tool_calls" 或 "stop"
    ② 如果 tool_calls：你的代码执行函数，结果追加到 messages
    ③ 再次调 API（这次没有 tool_calls），模型基于函数结果生成自然语言回复
    """
    messages = [{"role": "user", "content": user_input}]

    # ① 第一次调用：模型决定要不要调工具
    if verbose:
        print(f"\n{'─'*50}")
        print(f"  用户: {user_input}")
        print(f"{'─'*50}")

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
    )
    msg = response.choices[0].message

    # ② 检查 finish_reason
    if not msg.tool_calls:
        # 模型认为不需要调工具，直接返回文本
        if verbose:
            print(f"  [无工具调用] 模型直接回复: {msg.content}")
        return msg.content

    # ③ 模型想调工具 → 你的代码执行
    if verbose:
        print(f"  模型决定调用 {len(msg.tool_calls)} 个工具:")

    # Step 1: 把 assistant 的 tool_calls 消息追加到历史
    messages.append({
        "role": "assistant",
        "content": msg.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ],
    })

    # Step 2: 执行每个工具，并追加 tool result 消息
    tool_results = []
    for tc in msg.tool_calls:
        func_name = tc.function.name
        func_args = json.loads(tc.function.arguments)
        func = TOOL_MAP.get(func_name)

        if func:
            result = func(**func_args)
        else:
            result = f"错误：未知函数 {func_name}"

        tool_results.append((func_name, func_args, result))

        if verbose:
            print(f"    → {func_name}({json.dumps(func_args, ensure_ascii=False)})")
            print(f"      返回结果: {result}")

        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result,
        })

    # ④ 第二次调用：模型基于工具结果生成最终回复
    response2 = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    final_answer = response2.choices[0].message.content

    if verbose:
        print(f"\n  模型最终回复: {final_answer}")

    return final_answer


# ============================================================
# 实验
# ============================================================
print("=" * 60)
print("  实验1: 单工具 — get_weather")
print("  观察：模型如何识别需要调用 weather，提取参数 '杭州'")
print("=" * 60)

run_conversation("杭州今天天气怎么样")

print("\n\n" + "=" * 60)
print("  实验2: 需要工具 vs 不需要工具")
print("  问题① 需要天气数据 | 问题② 纯闲聊不需要工具")
print("=" * 60)

run_conversation("北京天气如何")
run_conversation("你好，你是谁")

print("\n\n" + "=" * 60)
print("  实验3: 多工具选择")
print("  观察：模型能否在 weather 和 calc 中选择正确的工具")
print("=" * 60)

run_conversation("12345 + 67890 等于多少")

print("\n\n" + "=" * 60)
print("  三个实验完成。核心收获:")
print("  1. 模型只负责「决策」调哪个工具，你的代码负责「执行」")
print("  2. finish_reason 从 'tool_calls' 变成 'stop' = 工具调用结束")
print("  3. tool result 必须作为独立消息追加到 messages 数组")
print("  4. 多工具场景下模型自动选对应工具——这就是 Agent 的「自主性」")
print("=" * 60)
