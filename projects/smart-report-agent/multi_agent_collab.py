"""多Agent协作模式演示 — 三种经典模式, 纯 OpenAI 兼容 API 实现

三种模式各用一个场景演示, 不依赖 LangGraph/CrewAI 框架。
核心: 用 system_prompt 模拟 Agent 角色, 直接在代码里控制交互逻辑。
"""

import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from openai import OpenAI

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY not configured")

client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"))
MODEL = "deepseek-chat"

# ═══════════════════════════════════════════════════════════════
# 模拟企业数据（与 agentic_retrieval.py 共用同一套数据源）
# 注意: 以下数据含模拟人名(张伟/李娜等)和虚构预算数字, 仅用于演示。
# 生产环境应从 RAG 知识库检索而非硬编码全量数据, 避免数据泄露和过时问题。
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
    {"topic": "infrastructure", "text": "AI平台组使用K8s 1.30 + A100 GPU集群训练模型, 日均处理50TB数据, 推理P99<80ms(10K QPS)。H2计划扩容30%算力。"},
    {"topic": "data_platform", "text": "数据工程组Q1完成Airflow→Dagster迁移, ETL覆盖200+表/12个数据源, 数据质量SLA从99.2%提升到99.7%。"},
    {"topic": "budget", "text": "Q3研发部新增12人(60% AI平台, 40% 数据工程), H2增量预算1500万。服务器折旧方案待评估。"},
    {"topic": "cost", "text": "研发部Q3云支出480万(AI训练占65%), 同比+22%。GPU按需实例占比从30%→55%, 预留实例成本可降18%。"},
]


def ask_agent(system_prompt: str, user_content: str) -> str:
    """通用 Agent 调用: 用 system_prompt 区分 Agent 角色。"""
    try:
        resp = client.chat.completions.create(
            model=MODEL, temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
    except Exception as e:
        return f"[API调用失败] {type(e).__name__}: {e}"

    if not resp.choices:
        return "[API返回空] choices列表为空, 无可用响应"
    return resp.choices[0].message.content or ""


# ═══════════════════════════════════════════════════════════════
# 模式1: Manager-Worker（管理-执行）
#   Manager 分析请求 → 拆解子任务 → 分派 Worker → 汇总报告
# ═══════════════════════════════════════════════════════════════

MANAGER_PROMPT = (
    "你是技术管理顾问。用户提出一个分析需求后, 你需要:\n"
    "1. 分析这个需求需要哪几类信息(组织/财务/技术)\n"
    "2. 列出每个子任务的具体查询内容\n"
    "3. 收到所有 Worker 结果后, 生成一份综合分析报告(含Q4优化建议)\n"
    "输出格式: 先列出子任务清单, 然后等待 Worker 数据。"
)

WORKER_PROMPTS = {
    "org":     "你是组织架构查询助手。根据给定的部门名, 用下面数据回答问题。\n" + json.dumps(ORG_HIERARCHY, ensure_ascii=False),
    "finance": "你是财务数据查询助手。根据给定的部门名, 用下面数据回答问题。\n" + json.dumps(FINANCIALS, ensure_ascii=False),
    "tech":    "你是技术文档检索助手。根据给定问题, 用下面数据回答问题。\n" + json.dumps(TECH_DOCS, ensure_ascii=False),
}


def demo_manager_worker():
    print("=" * 70)
    print("模式1: Manager-Worker（管理-执行）")
    print("=" * 70)

    user_query = "分析研发部的技术投入和预算效率, 给出Q4优化建议"

    # Step 1: Manager 拆解任务
    print(f"\n  [用户问题] {user_query}")
    print(f"  [Manager 分析中...]")

    mgr_plan = ask_agent(MANAGER_PROMPT, f"请分析以下需求, 列出需要哪些子任务:\n{user_query}")
    print(f"  [Manager 拆解] {mgr_plan[:200]}...")

    # Step 2: 并行分派三个 Worker
    # 注意: 演示环境下用预定义的 worker_queries 保证输出稳定;
    # 生产环境应从 mgr_plan 中解析 JSON 后动态生成子任务分派。
    worker_queries = {
        "org":     "研发部的组织架构、人数、主管、下属组有哪些?",
        "finance": "研发部Q2和Q3的预算和实际支出分别是多少? 预算利用率如何?",
        "tech":    "研发部技术投入情况: AI平台架构、数据管线、云支出、扩容计划",
    }

    worker_results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(ask_agent, WORKER_PROMPTS[name], query): name
            for name, query in worker_queries.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            label = f"Worker-{name}"
            query = worker_queries[name]
            result = future.result()
            worker_results[name] = result
            print(f"\n  [{label}] {query}")
            print(f"  [{label} 回答] {result[:150]}...")

    # Step 3: Manager 汇总
    summarize_prompt = (
        "你是技术管理顾问。现在汇总以下三个 Worker 的查询结果, 生成一份关于"
        f"「{user_query}」的综合分析报告(200字内), 含Q4优化建议。\n"
        f"——组织信息——\n{worker_results['org']}\n"
        f"——财务数据——\n{worker_results['finance']}\n"
        f"——技术文档——\n{worker_results['tech']}"
    )
    report = ask_agent(MANAGER_PROMPT, summarize_prompt)
    print(f"\n  [Manager 汇总报告]\n{report}")


# ═══════════════════════════════════════════════════════════════
# 模式2: Pipeline（流水线）
#   Rewriter → Retriever → Reviewer 三阶段接力
# ═══════════════════════════════════════════════════════════════

PIPELINE_DATA = json.dumps({
    "研发部": {"Q3预算": "920万", "Q3实际": "905万", "利用率": "98.4%",
            "人员": "45人", "云支出": "480万/季", "新增预算": "1500万(H2)"},
    "市场部": {"Q3预算": "550万", "Q3实际": "548万", "利用率": "99.6%",
            "人员": "32人", "投放支出": "320万/季"},
}, ensure_ascii=False)


def demo_pipeline():
    print("\n" + "=" * 70)
    print("模式2: Pipeline（流水线）")
    print("=" * 70)

    raw_question = "算算研发部花了多少钱"

    # 阶段1: 改写 — 口语化问题 → 精确检索 query
    rewriter_prompt = (
        "你是查询改写专家。把用户的口语化问题改写成精确的数据查询语句。"
        "只输出改写后的查询, 不要解释。"
    )
    rewritten = ask_agent(rewriter_prompt, f"改写: <user_input>{raw_question}</user_input>")
    print(f"\n  [阶段1 - 改写] 原始: \"{raw_question}\"")
    print(f"              改写: \"{rewritten}\"")

    # 阶段2: 检索 — 用改写后的 query 查数据
    retriever_prompt = (
        "你是数据检索助手。根据查询语句, 从以下知识库中精确提取相关数据。"
        f"只输出查到的数据, 不要补充解释。\n知识库:\n{PIPELINE_DATA}"
    )
    retrieved = ask_agent(retriever_prompt, f"查询: {rewritten}")
    print(f"\n  [阶段2 - 检索] 查到: {retrieved[:150]}")

    # 阶段3: 审核 — 检查检索结果是否覆盖原始问题
    reviewer_prompt = (
        "你是检索质量审核员。对比原始问题和检索结果, 判断:\n"
        "1. 检索结果是否完整覆盖了原始问题? (是/否)\n"
        "2. 如有遗漏, 指出具体缺失什么信息。\n"
        "只用输出审核结论, 不要补充额外的数据。"
    )
    review = ask_agent(reviewer_prompt,
                       f"原始问题: <user_input>{raw_question}</user_input>\n检索结果: <retrieved_data>{retrieved}</retrieved_data>")
    print(f"\n  [阶段3 - 审核]\n{review}")


# ═══════════════════════════════════════════════════════════════
# 模式3: Peer-to-Peer（对等协作）
#   两个 Agent 独立分析 → 互相辩论 → 融合输出
# ═══════════════════════════════════════════════════════════════

def demo_peer_to_peer():
    print("\n" + "=" * 70)
    print("模式3: Peer-to-Peer（对等协作）")
    print("=" * 70)

    issue = "研发部Q3预算利用率98.4%, 市场部99.6%。是否应该削减研发预算转给市场部?"

    # Agent A: 技术视角（捍卫研发投入）
    tech_prompt = (
        "你是CTO视角的技术顾问, 始终从技术长期价值出发分析问题。\n"
        f"已知数据:\n{json.dumps({'研发部': FINANCIALS[0], '研发部技术': [d['text'] for d in TECH_DOCS if '研发' in d['text'] or 'AI' in d['text'] or 'GPU' in d['text'] or 'K8s' in d['text']]}, ensure_ascii=False)}\n"
        "你的立场: 技术投入是长期竞争力, 不应仅凭单季利用率做削减决策。输出你的论据(3点, 100字内)。"
    )
    tech_opinion = ask_agent(tech_prompt, issue)
    print(f"\n  [Agent A - 技术视角]\n{tech_opinion}")

    # Agent B: 财务视角（关注资金效率）
    finance_prompt = (
        "你是CFO视角的财务顾问, 始终从资金使用效率出发分析问题。\n"
        f"已知数据:\n{json.dumps(FINANCIALS, ensure_ascii=False)}\n"
        "你的立场: 预算应向高效率部门倾斜, 低利用率意味着资金沉淀。输出你的论据(3点, 100字内)。"
    )
    finance_opinion = ask_agent(finance_prompt, issue)
    print(f"\n  [Agent B - 财务视角]\n{finance_opinion}")

    # 辩论融合: 提取双方论据, 给出平衡建议
    fusion_prompt = (
        "你是CEO视角的决策顾问, 需要在CTO(技术)和CFO(财务)的观点之间做平衡。\n"
        f"背景问题: {issue}\n"
        f"——CTO观点——\n{tech_opinion}\n"
        f"——CFO观点——\n{finance_opinion}\n"
        "要求: 提取双方合理论据, 给出一个权衡后的综合建议(3点, 150字内)。"
    )
    fusion = ask_agent(fusion_prompt, "请综合双方观点给出决策建议。")
    print(f"\n  [辩论融合 - 综合建议]\n{fusion}")


# ═══════════════════════════════════════════════════════════════
# Demo 入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    demo_manager_worker()
    demo_pipeline()
    demo_peer_to_peer()

    print("\n" + "=" * 70)
    print("面试速查: 三种多Agent协作模式的适用场景")
    print("=" * 70)
    print("""
  ┌──────────────────┬────────────────────────────────┬──────────────────────────────────┐
  │ 模式             │ 核心机制                        │ 适用场景                          │
  ├──────────────────┼────────────────────────────────┼──────────────────────────────────┤
  │ Manager-Worker   │ 一个Manager拆解任务→多个Worker │ 复杂任务拆解、多源数据聚合、         │
  │ (管理-执行)       │ 并行执行→Manager汇总            │ 报告生成、客服工单多部门流转        │
  ├──────────────────┼────────────────────────────────┼──────────────────────────────────┤
  │ Pipeline         │ 多个Agent串行, 前一阶段输出     │ 文档处理(翻译→润色→校对)、         │
  │ (流水线)          │ 是下一阶段输入                  │ 数据ETL、多级审核流程              │
  ├──────────────────┼────────────────────────────────┼──────────────────────────────────┤
  │ Peer-to-Peer     │ 多Agent独立分析→互相评审→       │ 风险评估、投资决策、代码审查、       │
  │ (对等协作)         │ 辩论融合输出                    │ 需要多视角避免单一偏见的场景        │
  └──────────────────┴────────────────────────────────┴──────────────────────────────────┘

  面试金句:
  "多Agent协作不是把一个大模型切成多个小模型——而是用不同的system_prompt给LLM
   戴上不同的'角色眼镜'。关键不是Agent数量, 而是交互结构(并行/串行/辩论)匹配业务场景。
   Manager-Worker解决'拆', Pipeline解决'串', Peer-to-Peer解决'辩'。"
""")
