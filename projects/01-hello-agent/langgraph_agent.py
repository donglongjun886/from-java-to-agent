"""
Day 6 Part 2 — LangGraph 重写 Tool Calling

把 tool_calling_demo.py 的流控逻辑用 LangGraph 重写。
手写的 if-else 全部消失，变成：图定义 + 节点函数 + 条件路由。

两个实验：
  实验1: 对比 tool_calling_demo（手写流程）vs LangGraph（图编排）的实现差异
  实验2: 两条不同路径的对话——需要工具 vs 不需要工具，观察路由行为
"""

import os
import json
from pathlib import Path
from typing import TypedDict, Annotated, Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# ============================================================
# 工具定义 — 和 tool_calling_demo.py 完全一样
# ============================================================

@tool
def get_weather(city: str) -> str:
    """获取指定城市当前的天气信息"""
    db = {"杭州": "晴，28°C，湿度 65%", "北京": "多云，22°C，湿度 40%", "深圳": "雷阵雨，31°C，湿度 85%"}
    return db.get(city, f"{city}：暂无数据")


@tool
def calculate(expression: str) -> str:
    """执行数学计算，如加减乘除"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


TOOLS = [get_weather, calculate]

# ============================================================
# LangGraph 搭建
# ============================================================

# ① State — 图的共享内存
class AgentState(TypedDict):
    """
    messages 用 add_messages reducer：各节点返回的消息自动追加，不覆盖。
    等价于 tool_calling_demo.py 里手动拼接 messages 数组。
    """
    messages: Annotated[list[BaseMessage], add_messages]

# ② 模型（绑定 tools）
model = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
    temperature=0.3,
)
model_with_tools = model.bind_tools(TOOLS)

# ③ 节点：调 LLM
def call_llm(state: AgentState) -> dict:
    """
    调一次 LLM。
    state["messages"] 包含 system prompt + 全部历史，模型决定要不要调工具。
    """
    messages = state["messages"]

    # 确保第一条是 system prompt
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content="你是资深的软件工程师助手。用中文回答，代码用 Markdown 格式。")] + list(messages)

    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

# ④ 节点：执行工具
def call_tool(state: AgentState) -> dict:
    """
    取最后一条 AI 消息的 tool_calls，挨个执行。
    等价于 tool_calling_demo.py 里 tool_calls 的 for 循环。
    """
    last_message = state["messages"][-1]
    tool_messages = []

    for tc in last_message.tool_calls:
        func_name = tc["name"]
        func_args = tc["args"]
        func = {"get_weather": get_weather, "calculate": calculate}.get(func_name)

        result = func.invoke(func_args) if func else f"未知函数: {func_name}"
        print(f"    → {func_name}({json.dumps(func_args, ensure_ascii=False)}) → {result}")

        tool_messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))

    return {"messages": tool_messages}

# ⑤ 条件路由 — 替代手写 if-else
def router(state: AgentState) -> Literal["tool", "__end__"]:
    """
    这就是 tool_calling_demo.py 里 140 行左右的 if-else 的 LangGraph 等价物：

    # 手写逻辑：
    if not msg.tool_calls:
        return msg.content      # ← 等价于 return END
    # 有 tool_calls → 执行后继续    # ← 等价于 return "tool"

    图引擎读到 "tool" → 自动跳到 call_tool 节点 → 执行完回 call_llm
    图引擎读到 END → 结束
    """
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool"
    return END

# ⑥ 搭图
graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("tool", call_tool)
graph.set_entry_point("llm")
graph.add_conditional_edges("llm", router, {"tool": "tool", END: END})
graph.add_edge("tool", "llm")  # 工具执行完 → 回到 LLM
app = graph.compile()

# ============================================================
# 实验
# ============================================================

def run(query: str):
    """给图输入一条消息，运行并打印结果"""
    result = app.invoke({"messages": [HumanMessage(content=query)]})
    final = result["messages"][-1]
    return final.content


print("=" * 60)
print("  实验1: 需要调工具 — 杭州天气")
print("=" * 60)
answer = run("杭州天气怎么样")
print(f"\n  最终回复: {answer[:200]}...")

print("\n\n" + "=" * 60)
print("  实验2: 不需要调工具 — 纯聊天")
print("=" * 60)
answer = run("你好，请问你是谁")
print(f"\n  最终回复: {answer[:200]}...")

print("\n\n" + "=" * 60)
print("  实验3: 多工具选择 — 计算")
print("=" * 60)
answer = run("12345 + 67890 等于多少")
print(f"\n  最终回复: {answer[:200]}...")

print("\n\n" + "=" * 60)
print("  对比总结:")
print("  手写版 (tool_calling_demo.py): 你手动管理 messages 拼接 + if-else 分支")
print("  LangGraph 版 (本文件): 图定义流程 + State 自动合并 + router 路由")
print("=" * 60)
print("\n  图结构: llm → [router] → tool(需要) → llm → END")
print("                               → END(不需要)")
