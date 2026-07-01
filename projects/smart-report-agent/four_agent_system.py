"""四 Agent 协同: Retrieval Planner → Multi-Source Retriever → Generator → Evaluator
纯 OpenAI API + 代码编排, 不依赖 Agent 框架。四个 system_prompt 区隔角色, 显式控制串/并行。
"""
import os
import json
import re
import logging
try:
    import jieba
except ImportError:
    jieba = None

from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key: raise RuntimeError("DEEPSEEK_API_KEY not configured")
client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"))
MODEL = "deepseek-chat"

# ── 模拟企业数据（与 multi_agent_collab.py / agentic_retrieval.py 共用） ──
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
    {"topic": "infrastructure", "text": "AI平台组使用K8s 1.30+A100 GPU集群训练模型, 日均50TB, 推理P99<80ms(10K QPS)。H2扩容30%算力。"},
    {"topic": "data_platform", "text": "数据工程组Q1完成Airflow→Dagster迁移, ETL覆盖200+表/12数据源, SLA从99.2%→99.7%。"},
    {"topic": "budget", "text": "Q3研发部新增12人(60% AI平台,40%数据工程), H2增量预算1500万。服务器折旧待评估。"},
    {"topic": "cost", "text": "研发部Q3云支出480万(AI训练占65%), 同比+22%。GPU按需占比30%→55%, 预留实例成本可降18%。"},
]

class LLMError(Exception):
    """LLM API 调用异常, 区别于业务逻辑错误"""
    pass

def ask_llm(system_prompt: str, user_content: str, temperature: float = 0.1) -> str:
    # 【Context Reset】每次调用创建独立 messages 列表，不保留历史上下文。
    # 四个 Agent 之间传递的是结构化数据（plan dict / retrieved dict / answer str），而非共享消息数组。
    try:
        resp = client.chat.completions.create(model=MODEL, temperature=temperature,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_content}])
    except Exception as e:
        logging.error("LLM call failed: %s: %s", type(e).__name__, e)
        raise LLMError(f"LLM API 调用失败: {type(e).__name__}") from e
    return (resp.choices[0].message.content or "") if resp.choices else "[API返回空]"

# ── 四个数据源检索函数 ──
def retrieve_org(department: str) -> str:
    dept = department.strip()
    for key, info in ORG_HIERARCHY.items():
        if dept in key or key in dept:
            return json.dumps({"部门": key, **info}, ensure_ascii=False)
    return json.dumps({}, ensure_ascii=False)

def retrieve_finance(department: str) -> str:
    results = [f for f in FINANCIALS if department.strip() in f["部门"] or f["部门"] in department.strip()]
    return json.dumps(results, ensure_ascii=False)

def retrieve_vector(query: str) -> str:
    # jieba 中文分词, 未安装时 fallback 为单字符遍历子串匹配
    if jieba is not None:
        keywords = [w for w in jieba.cut(query) if len(w) > 1]
    else:
        keywords = [query[i:i+2] for i in range(len(query)-1)]
    matched = [d["text"] for d in TECH_DOCS
               if any(kw.lower() in (d["topic"] + d["text"]).lower() for kw in keywords)]
    return json.dumps(matched or [{"message": "未找到相关技术文档"}], ensure_ascii=False)

def retrieve_compare() -> str:
    parts = []
    for dept_name, info in ORG_HIERARCHY.items():
        fin = next((f for f in FINANCIALS if f["部门"] == dept_name), {})
        q3b, q3a = fin.get("Q3预算", 0), fin.get("Q3实际", 0)
        util = f"{q3a/q3b*100:.1f}%" if q3b > 0 else "N/A"
        parts.append({"部门": dept_name, "主管": info["主管"], "人数": info["人数"],
                       "Q3预算(万)": q3b, "Q3实际(万)": q3a, "预算利用率": util})
    return json.dumps(parts, ensure_ascii=False)

RETRIEVER_MAP = {"org": retrieve_org, "finance": retrieve_finance,
                  "vector": retrieve_vector, "compare": retrieve_compare}

# ── Agent 1: Retrieval Planner ──
PLANNER_PROMPT = (
    "你是检索规划专家。分析用户问题，拆解为子任务，每个子任务标注需要的数据源类型。\n"
    "可用数据源: vector(技术文档) / org(组织架构) / finance(财务) / compare(跨部门对比)\n"
    "输出严格JSON数组，不要额外文字:\n"
    '[{"source":"vector", "sub_query":"子查询"}, {"source":"org", "sub_query":"子查询"}]\n'
    "规则: 简单查询分配1个源; 跨源综合分配多个; 对比分析用compare。"
)

def run_planner(user_query: str) -> list[dict]:
    try:
        raw = ask_llm(PLANNER_PROMPT, f"用户问题: {user_query}").strip()
    except LLMError:
        raw = ""  # LLM 不可用时直接走关键词回退
    # 正则提取 JSON 数组, 兼容 markdown 代码块包裹等变体
    match = re.search(r'\[.*\]', raw, re.DOTALL) if raw else None
    if match:
        try:
            plan = json.loads(match.group(0))
            return [plan] if isinstance(plan, dict) else plan
        except json.JSONDecodeError:
            pass
    # 容错: 正则未匹配或 JSON 解析失败时用关键词回退
    q = user_query
    subs = []
    if any(k in q for k in ["预算", "财务", "支出"]): subs.append({"source": "finance", "sub_query": q})
    if any(k in q for k in ["技术", "架构", "平台", "文档"]): subs.append({"source": "vector", "sub_query": q})
    if any(k in q for k in ["组织", "部门人", "多少人"]): subs.append({"source": "org", "sub_query": q})
    if any(k in q for k in ["对比", "比较", "哪个部门"]): subs.append({"source": "compare", "sub_query": q})
    return subs or [{"source": "vector", "sub_query": q}]

# ── Agent 2: Multi-Source Retriever ──
def run_retriever(subtasks: list[dict]) -> dict[str, str]:
    results, tasks = {}, []
    for task in subtasks:
        src = task.get("source", "vector")
        fn = RETRIEVER_MAP.get(src)
        if fn is None: results[f"{src}(未知)"] = f"未知数据源: {src}"; continue
        # compare 无参, 其他源统一传参; 空字符串兜底为 "全部"
        if src == "compare":
            tasks.append((src, fn, None))
        else:
            arg = task.get("sub_query", "") or "全部"
            tasks.append((src, fn, arg))
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for src, fn, arg in tasks:
            f = executor.submit(fn) if arg is None else executor.submit(fn, arg)
            futures[f] = (src, arg if arg is not None else "全部门对比")
        for f in as_completed(futures):
            src, label = futures[f]
            try: results[src] = f.result()
            except Exception as e: results[src] = f"[检索异常] {e}"
    return results

# ── Agent 3: Generator ──
GENERATOR_PROMPT = (
    "你是企业报告生成专家。基于检索上下文回答用户问题。\n"
    "要求: 1)不编造数据 2)关键数据标注来源[org/finance/vector] 3)结构化输出 4)不足时指出缺口"
)
def run_generator(user_query: str, retrieved: dict[str, str]) -> str:
    ctx = "\n\n".join(f"[{s}]\n{c}" for s, c in retrieved.items())
    return ask_llm(GENERATOR_PROMPT, f"用户问题: {user_query}\n\n检索上下文:\n{ctx}")

# ── Agent 4: Evaluator（独立评估，非 Generator 自评） ──
EVALUATOR_PROMPT = (
    "你是独立评估专家。基于原始问题和检索上下文，评估生成回答的质量（不要补充回答）。\n"
    "1. Faithfulness (0-1): 回答是否完全基于检索上下文？有无编造？\n"
    "2. Answer Relevancy (0-1): 回答是否切题？覆盖关键点？\n"
    "输出格式（不要额外文字）:\n"
    "Faithfulness: <分数>\nAnswer Relevancy: <分数>\n建议: <一句话建议>"
)
def run_evaluator(user_query: str, answer: str, retrieved: dict[str, str]) -> dict:
    ctx = "\n\n".join(f"[{s}]\n{c}" for s, c in retrieved.items())
    raw = ask_llm(EVALUATOR_PROMPT, f"原始问题: {user_query}\n\n检索上下文:\n{ctx}\n\n生成回答:\n{answer}")
    result = {"faithfulness": None, "relevancy": None, "suggestion": ""}
    for line in raw.split("\n"):
        l = line.strip()
        if l.lower().startswith("faithfulness"):
            match = re.search(r'(\d+\.?\d*)', l)
            if match:
                try: result["faithfulness"] = float(match.group(1))
                except ValueError: pass
        elif l.lower().startswith("answer relevancy"):
            match = re.search(r'(\d+\.?\d*)', l)
            if match:
                try: result["relevancy"] = float(match.group(1))
                except ValueError: pass
        elif l.startswith("建议") and ":" in l:
            result["suggestion"] = l.split(":", 1)[-1].strip()
    return result

# ── 主流水线 ──
def run_pipeline(user_query: str, verbose: bool = True) -> dict:
    # 【Context Reset】每次调用 run_pipeline 都是独立上下文，不累积历史。所有中间结果（plan/retrieved/answer/evaluation）
    # 均为局部变量，管道执行完毕后即释放，确保多个查询之间互不污染。
    log = []
    try:
        plan = run_planner(user_query)
        log.append(f"[Planner] 拆解为 {len(plan)} 个子任务:")
        for i, t in enumerate(plan, 1): log.append(f"  {i}. [{t['source']}] {t['sub_query']}")

        retrieved = run_retriever(plan)
        log.append(f"\n[Retriever] 并行检索 {len(plan)} 个数据源...")
        for src, content in retrieved.items():
            pv = content[:100].replace("\n", " ") + ("..." if len(content) > 100 else "")
            log.append(f"  {src}: {pv}")

        answer = run_generator(user_query, retrieved)
        log.append(f"\n[Generator] 基于检索结果生成回答...")

        ev = run_evaluator(user_query, answer, retrieved)
        log.append(f"\n[Evaluator] 独立评估:")
        log.append(f"  Faithfulness: {ev['faithfulness']}")
        log.append(f"  Answer Relevancy: {ev['relevancy']}")
        log.append(f"  建议: {ev['suggestion']}")

        if verbose: logging.info("\n".join(log))
        return {"plan": plan, "retrieved": retrieved, "answer": answer, "evaluation": ev}
    except LLMError as e:
        logging.error("Pipeline 中断于 LLM 调用异常: %s", e)
        return {"plan": [], "retrieved": {}, "answer": f"[流水线中断] {e}", "evaluation": {}}

# ── 演示: 3 组查询 ──
if __name__ == "__main__":
    DEMOS = [
        "研发部Q3预算利用率是多少？",                                   # 单源
        "分析研发部Q3的技术投入和预算效率，给出Q4建议",                    # 跨源综合
        "对比各个部门的预算利用率，哪个部门最需要优化？",                  # 对比分析
    ]
    for qi, q in enumerate(DEMOS, 1):
        # 【Context Reset】每个查询独立调用 run_pipeline，前一个查询的 plan/retrieved/answer/evaluation
        # 不会传递到下一个查询。每次管道调用从零开始构建上下文，确保查询之间互不污染。
        logging.info("=" * 70)
        logging.info(f"查询 {qi}: {q}")
        logging.info("=" * 70)
        r = run_pipeline(q, verbose=True)
        logging.info(f"\n{'─' * 70}\n[最终回答]\n{r['answer']}\n")

    logging.info("=" * 70)
    logging.info("面试四句话")
    logging.info("=" * 70)
    logging.info(
        '1. "四个Agent各司其职: Planner管策略、Retriever管执行、Generator管输出、Evaluator管质量"\n'
        '2. "Evaluator不能是Generator自己——外部独立评估才能发现幻觉"\n'
        '3. "Retrieval Planner的价值在复杂查询: 用户问\'对比各部门预算效率\'，Planner自动拆成4个子查询"\n'
        '4. "这套架构对标 Zoom JD 的 multi-step, tool-using AI agents"'
    )
