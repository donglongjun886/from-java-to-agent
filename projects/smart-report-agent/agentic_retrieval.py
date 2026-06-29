"""Agentic Retrieval — Agent 自主决策检索策略 vs 静态 RAG Pipeline

不依赖 LlamaIndex Agent 框架, 直接用 OpenAI 兼容 Tool Calling API。
核心: Agent 根据问题类型, 自主选择 [向量检索 | 结构化查询 | 财务数据 | 跨部门对比]

面试一句话:
  "静态 RAG 的检索路径是固定的 (query → top-k → generate)。
   Agentic Retrieval 让 LLM 自己做路由 — 问架构调向量检索, 问预算调财务工具,
   问跨部门对比 Agent 可能调用多个工具然后融合结果。"
"""

import os, sys, json, inspect
from unittest.mock import MagicMock
sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()
sys.modules["langchain_community.chat_models.vertexai"].ChatVertexAI = MagicMock()

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from openai import OpenAI

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY not configured")

client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"))
MODEL = "deepseek-chat"

# ═══════════════════════════════════════════════════════════════
# 模拟企业知识库 — 不同数据源分布在不同的「检索工具」中
# ═══════════════════════════════════════════════════════════════

ORG_HIERARCHY = {
    "研发部": {"主管": "张伟", "人数": 45, "下属组": ["AI平台组", "数据工程组", "基础架构组"]},
    "市场部": {"主管": "李娜", "人数": 32, "下属组": ["品牌组", "增长组", "内容组"]},
    "销售部": {"主管": "王强", "人数": 28, "下属组": ["华东区", "华南区", "华北区"]},
    "财务部": {"主管": "陈芳", "人数": 15, "下属组": ["核算组", "预算组"]},
}

FINANCIALS = [
    {"部门": "研发部", "Q2预算": 850, "Q3预算": 920, "Q2实际": 830, "Q3实际": 905},
    {"部门": "市场部", "Q2预算": 500, "Q3预算": 550, "Q2实际": 510, "Q3实际": 548},
    {"部门": "销售部", "Q2预算": 650, "Q3预算": 700, "Q2实际": 680, "Q3实际": 720},
    {"部门": "财务部", "Q2预算": 200, "Q3预算": 220, "Q2实际": 195, "Q3实际": 215},
]

TECH_DOCS = [
    {"topic": "infrastructure", "text": "AI Platform Group uses Kubernetes 1.30 with GPU scheduling (A100) for model training. Pipeline ingests 50TB daily, inference P99 < 80ms under 10K QPS."},
    {"topic": "data_platform", "text": "Data Engineering Team migrated Airflow→Dagster Q1 2026. ETL processes 200+ tables across 12 sources. Data quality SLA: 99.2%→99.7%."},
    {"topic": "budget", "text": "Q3 2026: R&D headcount +12 FTE (60% AI platform, 40% data eng). Total incremental budget 15M CNY for H2 2026."},
    {"topic": "sales", "text": "Sales Q3 achieved 118% quota. East China 45% of revenue. Top3: 某新能源汽车(1.2亿), 某半导体(0.95亿), 某金融科技(0.82亿)."},
]


# ═══════════════════════════════════════════════════════════════
# 四个检索工具 — 作为 Function Definitions
# ═══════════════════════════════════════════════════════════════

def search_vector(query: str):
    """向量语义检索 — 适合概念性问题"""
    # 简化版: 关键词匹配
    results = []
    for doc in TECH_DOCS:
        keywords = doc["topic"].replace("_", " ") + " " + doc["text"]
        if query.lower() in keywords.lower():
            results.append({"topic": doc["topic"], "text": doc["text"][:120]})
    if not results:
        return json.dumps({"message": "未找到相关技术文档"}, ensure_ascii=False)
    return json.dumps(results, ensure_ascii=False)

def search_org(department: str):
    """组织架构查询 — 查部门主管/人数/下属组"""
    info = ORG_HIERARCHY.get(department)
    if info:
        return json.dumps(info, ensure_ascii=False)
    return json.dumps({"错误": f"未找到部门'{department}'，可用部门: {list(ORG_HIERARCHY.keys())}"}, ensure_ascii=False)

def search_financial(departments: list[str]):
    """财务数据查询 — 查指定部门的预算/实际支出。departments: 部门名列表"""
    results = []
    for f in FINANCIALS:
        if f["部门"] in departments:
            results.append(f)
    return json.dumps(results, ensure_ascii=False)

def search_compare(query: str):
    """跨部门综合对比 — 对比所有部门的组织+财务+技术投入"""
    parts = []
    for dept_name, info in ORG_HIERARCHY.items():
        fin = next((f for f in FINANCIALS if f["部门"] == dept_name), {})
        parts.append({
            "部门": dept_name, "主管": info["主管"], "人数": info["人数"],
            "Q3预算": fin.get("Q3预算"), "Q3实际": fin.get("Q3实际"),
            "预算利用率": f"{fin.get('Q3实际',0)/(fin.get('Q3预算') or 1)*100:.0f}%"
        })
    return json.dumps(parts, ensure_ascii=False)

# OpenAI Tool Definitions
TOOLS = [
    {"type": "function", "function": {
        "name": "search_vector",
        "description": "语义检索技术文档。用于概念/架构/技术问题, 如'AI平台技术栈''数据管线用什么'",
        "parameters": {
            "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
        }
    }},
    {"type": "function", "function": {
        "name": "search_org",
        "description": "查询部门组织架构: 主管、人数、下属组。如'研发部多少人''谁管市场部'",
        "parameters": {
            "type": "object", "properties": {"department": {"type": "string"}}, "required": ["department"]
        }
    }},
    {"type": "function", "function": {
        "name": "search_financial",
        "description": "查询财务预算和支出。如'研发部和市场部的Q3预算'",
        "parameters": {
            "type": "object", "properties": {
                "departments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "部门名列表，如['研发部','市场部']"
                }
            }, "required": ["departments"]
        }
    }},
    {"type": "function", "function": {
        "name": "search_compare",
        "description": "跨部门综合对比。一次性获取所有部门的组织+财务数据。如'对比各部门的预算利用率'",
        "parameters": {
            "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
        }
    }},
]

TOOL_MAP = {"search_vector": search_vector, "search_org": search_org,
            "search_financial": search_financial, "search_compare": search_compare}


def agentic_query(user_query: str) -> tuple[list[str], str]:
    """Agentic 查询: LLM 自主决策调用哪些工具, 融合结果后生成回答。"""
    messages = [
        {"role": "system", "content": (
            "你是企业数据查询助手。根据用户问题, 自主选择最合适的工具:\n"
            "- 概念/技术问题 → search_vector\n"
            "- 单部门组织信息 → search_org\n"
            "- 财务预算数据 → search_financial\n"
            "- 多部门综合对比 → search_compare\n"
            "可以调用多个工具，但不要浪费时间在不需要的工具上。"
        )},
        {"role": "user", "content": user_query},
    ]

    tool_calls_made = []

    # 第一轮: LLM 决定调用哪些工具
    response = client.chat.completions.create(
        model=MODEL, messages=messages, tools=TOOLS, temperature=0.1,
    )
    msg = response.choices[0].message

    # 如果 LLM 决定调工具（最多 5 轮迭代，防止死循环）
    for _ in range(5):
        if not msg.tool_calls:
            break

        # 追加 assistant 消息 (含 tool_calls)
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        })

        # 执行每个工具调用, 追加结果
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            args = json.loads(tc.function.arguments)
            fn = TOOL_MAP.get(tool_name)
            if fn is None:
                result = json.dumps({"错误": f"未知工具: {tool_name}"}, ensure_ascii=False)
                tool_calls_made.append(f"{tool_name}(未知工具)")
                messages.append({
                    "role": "tool", "tool_call_id": tc.id, "content": result,
                })
                continue

            # 过滤 LLM 可能幻觉出的额外参数，只保留函数签名中存在的参数
            valid_kw = {k: v for k, v in args.items() if k in inspect.signature(fn).parameters}
            try:
                result = fn(**valid_kw)
            except Exception as e:
                result = json.dumps({"错误": f"工具执行异常: {str(e)}"}, ensure_ascii=False)
            tool_calls_made.append(f"{tool_name}({json.dumps(valid_kw, ensure_ascii=False)})")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

        # 继续: LLM 决定是否需要更多工具
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, temperature=0.1,
        )
        msg = response.choices[0].message

    # 最终回答
    if msg.tool_calls:
        final_answer = "警告: 达到最大迭代次数(5轮), Agent 可能陷入循环, 请简化查询重试。"
    else:
        final_answer = msg.content or ""
    return tool_calls_made, final_answer


# ═══════════════════════════════════════════════════════════════
# Demo: 三类查询 × Agentic
# ═══════════════════════════════════════════════════════════════

test_queries = [
    # Q1: 单源 — 只该调 search_org
    "研发部有多少人? 主管是谁?",
    # Q2: 跨源 — 应该调 search_financial + search_compare
    "对比研发部和市场部的Q3预算和实际支出, 哪个部门预算利用率更高?",
    # Q3: 语义 — 应该调 search_vector
    "AI平台的技术架构是怎样的? 数据管线用什么工具?",
]

print("=" * 70)
print("Agentic Retrieval — LLM 自主决策调用哪些检索工具")
print("=" * 70)

for i, query in enumerate(test_queries, 1):
    print(f"\n{'─' * 60}")
    print(f"Q{i}: {query}")
    print(f"{'─' * 60}")

    tools_used, answer = agentic_query(query)

    print(f"\n  Agent 调用的工具: {tools_used}")
    print(f"  最终回答: {answer}")

# ═══════════════════════════════════════════════════════════════
# vs 静态 RAG 对比
# ═══════════════════════════════════════════════════════════════

print(f"\n{'=' * 70}")
print("Agentic Retrieval vs 静态 RAG — 面试速查")
print("=" * 70)
print("""
  维度           │ 静态 RAG            │ Agentic Retrieval
  ───────────────┼─────────────────────┼─────────────────────────
  检索路径        │ Query → Top-K (固定) │ Agent 自主选择工具
  多源协同        │ 需手动编排           │ LLM 自动路由
  多步推理        │ 不支持               │ 支持 (链式调用)
  延迟            │ ~1s                 │ ~3-10s (多轮 LLM)
  成本            │ 低 (1 次 LLM)       │ 中 (N 次 LLM + Tool)
  适合场景         │ FAQ / 单源文档问答   │ 跨域分析 / 复杂查询

  面试金句:
  "Agentic 不是'更准'而是'更灵活'。静态 RAG 够用时不上 Agent。
   Agent 的价值在不确定性 — 你不知道下一问会涉及哪个数据源。"
""")
