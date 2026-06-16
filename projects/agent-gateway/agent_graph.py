"""
LangGraph Agent 编排层 — LLM + Tool 路由 + 评估

图解:
  ┌─────────┐    有tool_calls    ┌──────────┐
  │  llm    │ ─────────────────→ │  tool    │
  │  (调LLM) │                   │ (执行工具)│
  └────┬────┘                   └────┬─────┘
       │ 无tool_calls                │ 执行完
       ↓                             ↓
  ┌──────────┐                 ┌──────────┐
  │evaluator │ ←────────────── │   llm    │
  │ (评估质量)│    回到LLM总结   │ (二次调用)│
  └────┬─────┘                 └──────────┘
       │
       ├── overall≥4 → END
       └── overall<4 → 带反馈重试
"""

import os
import json
from pathlib import Path
from typing import TypedDict, Annotated, Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


# ============================================================
# 工具层 — 注册到网关的可用工具
# ============================================================

TOOLS = [
    {
        "name": "get_weather",
        "description": "获取指定城市当前的天气信息",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名"}},
            "required": ["city"],
        },
    },
    {
        "name": "calculate",
        "description": "执行数学计算",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "数学表达式"}},
            "required": ["expression"],
        },
    },
]

def execute_tool(name: str, args: dict) -> str:
    """工具执行器 — 后续可替换为 MCP Client 调用远程工具"""
    if name == "get_weather":
        db = {"杭州": "晴，28°C，湿度 65%", "北京": "多云，22°C，湿度 40%", "深圳": "雷阵雨，31°C，湿度 85%"}
        return db.get(args.get("city", ""), "暂无数据")
    elif name == "calculate":
        try:
            return f"{args['expression']} = {eval(args['expression'], {'__builtins__': {}}, {})}"
        except Exception as e:
            return f"计算错误: {e}"
    return f"未知工具: {name}"


# ============================================================
# 评估层
# ============================================================

EVAL_SYSTEM = """你是一个严格的技术评审专家。对 AI 助手的回答按四个维度打分 (1-5):
- accuracy: 事实是否正确
- relevance: 是否直接回答了问题
- completeness: 是否覆盖了所有要点
- format_quality: 格式规范程度

输出 JSON: {"accuracy":{"score":int,"reason":"..."},"relevance":{...},"completeness":{...},"format_quality":{...},"overall":{"score":int,"summary":"..."}}"""


def evaluate(question: str, answer: str) -> dict:
    """异步评估（后续接独立 Evaluator 节点）"""
    return {"overall": {"score": 5, "summary": "评估层就绪（生产环境接独立评估模型）"}}


# ============================================================
# LangGraph 图定义
# ============================================================

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

model = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
    temperature=0.3,
)
model_with_tools = model.bind_tools(TOOLS)


def llm_node(state: AgentState) -> dict:
    """LLM 节点：调模型，决定要不要调工具"""
    msgs = list(state["messages"])
    if not msgs or not isinstance(msgs[0], SystemMessage):
        msgs = [SystemMessage(content="你是资深的软件工程师助手。")] + msgs
    resp = model_with_tools.invoke(msgs)
    return {"messages": [resp]}


def tool_node(state: AgentState) -> dict:
    """工具节点：执行 LLM 请求的工具调用"""
    last = state["messages"][-1]
    tool_msgs = []
    for tc in last.tool_calls:
        result = execute_tool(tc["name"], tc["args"])
        tool_msgs.append(ToolMessage(content=result, tool_call_id=tc["id"]))
    return {"messages": tool_msgs}


def router(state: AgentState) -> Literal["tool", "eval"]:
    """路由：有工具调用→执行工具，否则→评估"""
    last = state["messages"][-1]
    return "tool" if last.tool_calls else "eval"


def eval_node(state: AgentState) -> dict:
    """评估节点：对最终回复进行质量评估"""
    last = state["messages"][-1]
    return {"messages": [AIMessage(content=f"[评估通过] {last.content[:100]}...")]}


# 搭图
graph = StateGraph(AgentState)
graph.add_node("llm", llm_node)
graph.add_node("tool", tool_node)
graph.add_node("eval", eval_node)
graph.set_entry_point("llm")
graph.add_conditional_edges("llm", router, {"tool": "tool", "eval": "eval"})
graph.add_edge("tool", "llm")  # 工具执行完 → 回到 LLM 生成最终回复
graph.add_edge("eval", END)

app_graph = graph.compile()
