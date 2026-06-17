"""
Agent 编排层 — LangGraph + MCP Client + 安全护栏 + LLM评估 + 可观测

架构:
  Client → FastAPI Gateway → AgentGraph (本文件)
                                ├── llm_node (调LLM)
                                ├── tool_node (MCP Client 调工具)
                                ├── eval_node (LLM-as-a-Judge)
                                ├── guard_input / guard_tool / guard_output (安全三层)
                                └── stats (可观测数据收集)
"""

import os
import re
import time
import json
import asyncio
import unicodedata
from pathlib import Path
from typing import TypedDict, Annotated, Literal, Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import (
    BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
)
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# ============================================================
# MCP Client — 替代硬编码 execute_tool
# ============================================================

MCP_SERVER_SCRIPT = str(Path(__file__).resolve().parent.parent / "01-hello-agent" / "mcp_weather_server.py")

_mcp_tools: list[dict] = []
_mcp_session = None
_mcp_context = None
_mcp_lock = asyncio.Lock()


def _tool_spec_to_openai_format(tool) -> dict:
    """MCP Tool → OpenAI tools 参数格式"""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


async def init_mcp_tools() -> list[dict]:
    """启动 MCP Server 子进程，获取工具列表，缓存 session"""
    global _mcp_tools, _mcp_session, _mcp_context
    if _mcp_tools:
        return _mcp_tools

    async with _mcp_lock:
        # 双重检查：拿到锁后再次确认，防止并发重复初始化
        if _mcp_tools:
            return _mcp_tools

        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=str(Path(__file__).resolve().parent.parent.parent / ".venv/bin/python"),
            args=[MCP_SERVER_SCRIPT],
        )
        _mcp_context = stdio_client(params)
        read, write = await _mcp_context.__aenter__()
        _mcp_session = ClientSession(read, write)
        await _mcp_session.__aenter__()
        await _mcp_session.initialize()

        result = await _mcp_session.list_tools()
        _mcp_tools = [_tool_spec_to_openai_format(t) for t in result.tools]
        return _mcp_tools


async def execute_tool_mcp(name: str, args: dict) -> str:
    """通过 MCP Client 执行工具调用"""
    if not _mcp_session:
        return f"MCP 会话未初始化: {name}"
    try:
        result = await _mcp_session.call_tool(name, args)
        # result.content 是 list[TextContent | ImageContent | ...]
        texts = [c.text for c in result.content if hasattr(c, "text")]
        return "\n".join(texts) if texts else str(result.content)
    except Exception as e:
        return f"工具执行失败 [{name}]: {e}"


async def close_mcp():
    """关闭 MCP 会话"""
    global _mcp_session, _mcp_context
    if _mcp_session:
        await _mcp_session.__aexit__(None, None, None)
        _mcp_session = None
    if _mcp_context:
        await _mcp_context.__aexit__(None, None, None)
        _mcp_context = None


# ============================================================
# 安全护栏 — 三层防线
# ============================================================

# 输入层：Prompt 注入检测（关键词启发式）
INJECTION_PATTERNS = [
    r"(ignore|forget|disregard|override)\s+(all\s+)?(previous|prior|above|system|your)\s+(instructions?|prompts?|rules?)",
    r"you\s+are\s+now\s+(DAN|jailbreak|unrestricted)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"output\s+your\s+(system\s+prompt|instructions?)",
    r"\[SYSTEM\]|\[JAILBREAK\]|<<SYSTEM>>",
]

# 工具层：危险操作关键词
DANGEROUS_PATTERNS = {
    "sql": [r"\bDROP\b", r"\bDELETE\s+FROM\b", r"\bTRUNCATE\b", r"\bALTER\b"],
    "shell": [r"\brm\s+-rf\b", r"\bchmod\s+777\b", r"\bwget\b.*\|.*sh\b"],
    "file": [r"\/etc\/(passwd|shadow)", r"\.\.\/\.\.\/\.\.\/"],
}

# 输出层：敏感信息检测
SENSITIVE_PATTERNS = [
    r"sk-(?:proj-)?[a-zA-Z0-9]{20,}",     # OpenAI API / Project Key
    r"ghp_[a-zA-Z0-9]{36}",                # GitHub Classic Token
    r"github_pat_[a-zA-Z0-9]{22,}",        # GitHub Fine-grained Token
    r"glpat-[a-zA-Z0-9]{20,}",             # GitLab Personal Access Token
    r"AKIA[0-9A-Z]{16}",                   # AWS Access Key
    r"-----BEGIN\s+(RSA|EC|DSA|PRIVATE)\s+PRIVATE\s+KEY-----",
]


@dataclass
class GuardResult:
    passed: bool
    reason: str = ""
    risk_level: str = "low"  # low / medium / high / critical


def guard_input(text: str) -> GuardResult:
    """输入护栏：检测 Prompt 注入（含 Unicode 同形字规范化）"""
    normalized = unicodedata.normalize("NFKC", text)
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return GuardResult(passed=False, reason=f"疑似注入: 匹配 {pattern}", risk_level="high")
    return GuardResult(passed=True)


def guard_tool(tool_name: str, args: dict) -> GuardResult:
    """工具护栏：检测危险调用"""
    arg_str = json.dumps(args, ensure_ascii=False)
    for category, patterns in DANGEROUS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, arg_str, re.IGNORECASE):
                return GuardResult(
                    passed=False,
                    reason=f"危险 {category} 操作: {pattern}",
                    risk_level="critical"
                )
    return GuardResult(passed=True)


def redact_sensitive(text: str) -> str:
    """脱敏：用 *** 替换敏感信息片段，而非拦截整个回答"""
    for pattern in SENSITIVE_PATTERNS:
        text = re.sub(pattern, lambda m: m.group()[:4] + "***[REDACTED]", text)
    return text


def guard_output(text: str) -> GuardResult:
    """输出护栏：检测敏感信息泄漏"""
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            return GuardResult(
                passed=False,
                reason="输出含疑似密钥/凭证，已脱敏处理",
                risk_level="high"
            )
    return GuardResult(passed=True)


# ============================================================
# 评估层 — 真实 LLM-as-a-Judge
# ============================================================

EVAL_SYSTEM = """你是一个严格的技术评审专家。对 AI 助手的回答按四维度打分 (1-5):

- accuracy: 事实是否正确
- relevance: 是否直接回答了用户问题
- completeness: 是否覆盖了关键要点
- format_quality: 格式是否清晰易读

严格输出 JSON（不要额外文字）:
{"accuracy":{"score":int,"reason":"..."},"relevance":{"score":int,"reason":"..."},"completeness":{"score":int,"reason":"..."},"format_quality":{"score":int,"reason":"..."},"overall":{"score":int,"summary":"..."}}"""

_eval_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)


def evaluate(question: str, answer: str) -> dict:
    """LLM-as-a-Judge 四维评估（用原始 OpenAI SDK，不走 LangChain 回调，避免污染流式输出）"""
    try:
        resp = _eval_client.chat.completions.create(
            model="deepseek-chat",
            temperature=0.1,
            messages=[
                {"role": "system", "content": EVAL_SYSTEM},
                {"role": "user", "content": f"用户问题: {question}\n\nAI 回答: {answer}"},
            ],
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```json")[-1].split("```")[0].strip()
        return json.loads(content)
    except Exception:
        return {"overall": {"score": 3, "summary": "评估失败，默认 3 分"}}


# ============================================================
# 可观测 — Stats 收集
# ============================================================

@dataclass
class Stats:
    total_calls: int = 0
    total_tokens: int = 0
    total_time_ms: float = 0.0
    tool_calls_count: int = 0
    eval_scores: list[int] = field(default_factory=list)
    guard_blocks: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def avg_time_ms(self) -> float:
        return self.total_time_ms / self.total_calls if self.total_calls else 0

    @property
    def avg_eval_score(self) -> float:
        return sum(self.eval_scores) / len(self.eval_scores) if self.eval_scores else 0

    async def snapshot(self) -> dict:
        async with self.lock:
            return {
                "total_calls": self.total_calls,
                "total_tokens": self.total_tokens,
                "avg_time_ms": round(self.avg_time_ms, 1),
                "tool_calls_count": self.tool_calls_count,
                "avg_eval_score": round(self.avg_eval_score, 2),
                "guard_blocks": self.guard_blocks,
            }


stats = Stats()


# ============================================================
# LangGraph 图定义
# ============================================================

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    original_question: Optional[str]
    temperature: Optional[float]


SYSTEM_PROMPT = "你是资深的软件工程师助手，用中文回答，简洁准确。"


async def llm_node(state: AgentState) -> dict:
    """LLM 节点：调用模型（含工具绑定）"""
    msgs = list(state["messages"])
    if not msgs or not isinstance(msgs[0], SystemMessage):
        msgs = [SystemMessage(content=SYSTEM_PROMPT)] + msgs

    temperature = state.get("temperature", 0.3)
    tools = await init_mcp_tools()
    node_model = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1",
        temperature=temperature,
    ).bind_tools(tools)

    resp = await node_model.ainvoke(msgs)
    stats.total_tokens += resp.usage_metadata.get("total_tokens", 0) if resp.usage_metadata else 0
    return {"messages": [resp]}


async def tool_node(state: AgentState) -> dict:
    """工具节点：通过 MCP Client 执行工具调用"""
    last = state["messages"][-1]
    tool_msgs = []
    for tc in last.tool_calls:
        # 工具调用护栏
        g = guard_tool(tc["name"], tc["args"])
        if not g.passed:
            stats.guard_blocks += 1
            tool_msgs.append(ToolMessage(
                content=f"[安全拦截] {g.reason}",
                tool_call_id=tc["id"]
            ))
            continue

        stats.tool_calls_count += 1
        result = await execute_tool_mcp(tc["name"], tc["args"])
        tool_msgs.append(ToolMessage(content=result, tool_call_id=tc["id"]))
    return {"messages": tool_msgs}


def router(state: AgentState) -> Literal["tool", "eval"]:
    last = state["messages"][-1]
    return "tool" if hasattr(last, "tool_calls") and last.tool_calls else "eval"


def eval_node(state: AgentState) -> dict:
    """评估节点：LLM-as-a-Judge 质量评分"""
    question = state.get("original_question", "")
    # 找最后一条有实质内容的 AI 消息
    answer = ""
    for m in reversed(state["messages"]):
        if isinstance(m, AIMessage) and m.content and not (
            hasattr(m, "tool_calls") and m.tool_calls
        ):
            answer = m.content
            break

    if answer:
        result = evaluate(question, answer)
        score = result.get("overall", {}).get("score", 3)
        stats.eval_scores.append(score)
        return {"messages": [AIMessage(content=f"[评估: {score}/5] {result.get('overall', {}).get('summary', '')}")]}
    return {"messages": []}


# 搭图
graph = StateGraph(AgentState)
graph.add_node("llm", llm_node)
graph.add_node("tool", tool_node)
graph.add_node("eval", eval_node)
graph.set_entry_point("llm")
graph.add_conditional_edges("llm", router, {"tool": "tool", "eval": "eval"})
graph.add_edge("tool", "llm")
graph.add_edge("eval", END)

agent_app = graph.compile()


# ============================================================
# 对外接口（供 server.py 调用）
# ============================================================

async def run_chat(user_message: str, temperature: float = 0.3) -> dict:
    """同步调用：输入文本 → Agent → 最终回答 + 评估"""
    t0 = time.time()

    # ① 输入护栏
    g = guard_input(user_message)
    if not g.passed:
        stats.guard_blocks += 1
        return {"reply": f"[安全拦截] {g.reason}", "evaluation": None, "time_ms": 0, "stats": await stats.snapshot()}

    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "original_question": user_message,
        "temperature": temperature,
    }
    result = await agent_app.ainvoke(initial_state)

    # 提取最终回答和评估
    msgs = result["messages"]
    reply = ""
    eval_info = None
    for m in msgs:
        if isinstance(m, AIMessage):
            c = m.content or ""
            if c.startswith("[评估:"):
                eval_info = c
            elif c and not (hasattr(m, "tool_calls") and m.tool_calls):
                reply = c

    reply = reply or "[Agent 未生成回复]"

    # ② 输出护栏 — 脱敏而非拦截
    g_out = guard_output(reply)
    if not g_out.passed:
        reply = redact_sensitive(reply)

    stats.total_calls += 1
    elapsed = (time.time() - t0) * 1000
    stats.total_time_ms += elapsed

    return {
        "reply": reply,
        "evaluation": eval_info,
        "time_ms": round(elapsed, 1),
        "stats": await stats.snapshot(),
    }


async def run_chat_stream(user_message: str, temperature: float = 0.3):
    """流式调用：输入文本 → Agent → yield SSE chunks"""
    t0 = time.time()

    g = guard_input(user_message)
    if not g.passed:
        stats.guard_blocks += 1
        yield f"[安全拦截] {g.reason}"
        return

    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "original_question": user_message,
        "temperature": temperature,
    }

    # astream_events 按 token 粒度产出
    last_reply = ""
    async for event in agent_app.astream_events(initial_state, version="v2"):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                last_reply += chunk.content
                yield chunk.content

    # 输出脱敏
    if not guard_output(last_reply).passed:
        last_reply = redact_sensitive(last_reply)
        yield f"\n[注意] 回复中敏感信息已脱敏"

    stats.total_calls += 1
    stats.total_time_ms += (time.time() - t0) * 1000
