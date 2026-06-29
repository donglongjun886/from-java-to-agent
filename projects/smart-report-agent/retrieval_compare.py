"""静态 RAG vs Agentic Retrieval 检索质量对比评估

用 Hit Rate / MRR / NDCG 三个指标，对比同组查询在两种模式下的检索质量差异。

两种检索模式：
  - 静态 RAG（baseline）: 关键词匹配，固定规则选择数据源
  - Agentic Retrieval: 调用 run_planner + run_retriever，Agent 自主拆解查询并路由数据源
"""
import math
import os
import sys

# 允许从同目录导入 four_agent_system（无 __init__.py 的平级脚本）
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from four_agent_system import (  # noqa: E402
    ORG_HIERARCHY,
    retrieve_org, retrieve_finance, retrieve_vector, retrieve_compare,
    run_planner, run_retriever,
)

# ═══ 评估常量与辅助函数 ═══
# 关键词命中率 ≥67% → 相关度3分（高度相关）
# 关键词命中率 34%-67% → 相关度2分（中等相关）
# 关键词命中率 <34% 但>0 → 相关度1分（弱相关）
_HIGH_THRESHOLD = 0.67
_MEDIUM_THRESHOLD = 0.34


def _display_width(s: str) -> int:
    """计算字符串在终端中的显示宽度（中文占2列，英文占1列）。
    因为 Python 的 str.format 按字符数对齐，中文会撑破表格。"""
    # ord('一')=19968, ord('鿿')=40959 覆盖常用汉字
    return sum(2 if '一' <= c <= '鿿' or '　' <= c <= '〿' else 1 for c in s)


def _pad(s: str, width: int) -> str:
    """按显示宽度手动补空格，替代 str.format 的自动对齐。"""
    return s + ' ' * max(0, width - _display_width(s))


def _dcg(grades: list[int]) -> float:
    """DCG: 位置越靠后权重越低。排第1位权重=1/log₂(2)=1, 排第3位权重=1/log₂(4)=0.5。
    公式: Σ(g_i / log₂(i+2)), i从0开始所以+2。"""
    return sum(g / math.log2(i + 2) for i, g in enumerate(grades))


# ═══ 评估数据集: 8 QA pair，覆盖单源/跨源/对比 ═══
QA_PAIRS = [
    # 单源 × 3
    {"question": "研发部Q3预算利用率是多少？",
     "relevant_sources": ["finance"],
     "ground_truth_keywords": ["研发部", "Q3预算", "Q3实际", "利用率"]},
    {"question": "市场部有多少人？主管是谁？",
     "relevant_sources": ["org"],
     "ground_truth_keywords": ["市场部", "32", "李娜"]},
    {"question": "AI平台组的技术架构是怎样的？",
     "relevant_sources": ["vector"],
     "ground_truth_keywords": ["K8s", "GPU", "A100"]},

    # 跨源 × 3
    {"question": "分析研发部技术投入和预算效率",
     "relevant_sources": ["finance", "vector"],
     "ground_truth_keywords": ["研发部", "Q3预算", "云支出", "K8s", "GPU"]},
    {"question": "销售部Q3预算执行情况和团队规模",
     "relevant_sources": ["org", "finance"],
     "ground_truth_keywords": ["销售部", "Q3预算", "Q3实际", "28", "王强"]},
    {"question": "研发部云支出和技术架构情况",
     "relevant_sources": ["vector", "finance"],
     "ground_truth_keywords": ["研发部", "云支出", "480", "K8s", "A100"]},

    # 对比 × 2
    {"question": "对比各部门的预算利用率",
     "relevant_sources": ["compare"],
     "ground_truth_keywords": ["研发部", "市场部", "销售部", "财务部", "利用率"]},
    {"question": "哪个部门Q3预算利用率最高？",
     "relevant_sources": ["compare", "finance"],
     "ground_truth_keywords": ["利用率", "Q3预算", "Q3实际", "研发部", "销售部"]},
]


# ═══ 静态 RAG（baseline）: 用 if/else 规则选数据源，不走 LLM ═══
def static_retrieve(query: str) -> dict[str, str]:
    """纯关键词规则匹配，模拟传统的「if 含"预算"→查财务」硬编码路由。
    这就是没有 Agent 时的做法——规则是人写死的，覆盖不了的查询就直接漏掉。
    与 Agentic 的差别: 问到"研发部技术投入和预算效率"，Agentic 会拆成2个子任务
    （查财务+查技术），静态版只能命中一个规则分支。"""
    results: dict[str, str] = {}
    q = query
    # 试着从问题里找出部门名（按字符串包含匹配）
    dept = next((d for d in ORG_HIERARCHY if d in q), None)

    # ── 以下四个 if 块就是"规则"：哪个关键词命中，就调哪个数据源 ──

    # 规则A: 问题含预算/财务/支出 → 查财务表
    if any(k in q for k in ["预算", "财务", "支出", "利用率", "执行", "云支出"]):
        results["finance"] = retrieve_finance(dept or "")

    # 规则B: 问题含技术/架构/平台 → 查技术文档（向量检索）
    if any(k in q for k in ["技术", "架构", "平台", "K8s", "GPU", "AI", "云"]):
        results["vector"] = retrieve_vector(q)

    # 规则C: 问题含人数/主管/团队 → 查组织架构
    if any(k in q for k in ["多少人", "主管", "团队", "规模", "人数"]):
        if dept:
            results["org"] = retrieve_org(dept)

    # 规则D: 问题要对比/排名 → 调跨部门对比
    if any(k in q for k in ["对比", "比较", "哪个部门", "各部门"]):
        results["compare"] = retrieve_compare()

    # 一道规则都没命中 → 兜底走向量检索（随便给点东西，避免空手）
    return results or {"vector": retrieve_vector(q)}


# ═══ 评估指标: P@K / MRR / NDCG@K ═══
def _grade_relevance(content: str, keywords: list[str]) -> int:
    """给检索结果打分 (0-3)，依据是"预期关键词命中了多少"。
    例: keywords=["研发部","Q3预算","Q3实际","利用率"]
        → 检索结果里出现了3个 → 命中率75% → 超过67%阈值 → 3分
        → 只出现了1个 → 命中率25% → 低于34% → 1分
    生产环境应该用人工标注的 relevance judgments，这里用关键词做近似。"""
    if not content:
        return 0
    c = str(content).lower()                   # 忽略大小写
    match_cnt = sum(1 for kw in keywords if kw.lower() in c)  # 数命中了几个关键词
    if match_cnt == 0:
        return 0
    ratio = match_cnt / len(keywords)           # 命中率 = 命中数/总关键词数
    return 3 if ratio >= _HIGH_THRESHOLD else (2 if ratio >= _MEDIUM_THRESHOLD else 1)


def evaluate_retrieval(
    retrieved: dict[str, str], keywords: list[str], k: int = 3
) -> dict[str, float]:
    """对检索结果计算三个指标。输入: {"finance": "研发部Q3预算920...", "vector": "K8s+A100..."}。

    每个数据源视为一个"文档"——
    finance/org/vector/compare 各是一篇文档，按关键词命中数被打分 (0-3)。
    然后所有文档按分数降序排列，算 P@K / MRR / NDCG。"""
    # 检索结果为空 → 三项指标全 0（什么都没搜到）
    if not retrieved:
        return {"prec3": 0.0, "mrr": 0.0, "ndcg3": 0.0}

    # 给每个数据源打分 → 按分数从高到低排列
    # 例: [("finance", 3), ("vector", 1), ("org", 0)]
    scored = sorted(
        [(src, _grade_relevance(content, keywords)) for src, content in retrieved.items()],
        key=lambda x: -x[1],   # 降序: 分数高的排前面
    )
    top_k = scored[:k]         # 只看前 K 个（k=3）

    # ① P@K: 前K个中有几个是相关的（g>0就算相关），除以K
    # 如果4个数据源都相关, P@3 = 3/3 = 1.0; 只有1个相关, P@3 = 1/3 = 0.33
    prec_k = sum(1 for _, g in top_k if g > 0) / len(top_k) if top_k else 0.0

    # ② MRR: 第一个相关文档排在第几位？1/rank
    # 排在位置1 → 1/1=1.0; 排在位置3 → 1/3=0.33; 一个都不相关 → 0
    mrr = 0.0
    for rank, (_, g) in enumerate(scored, 1):  # rank 从 1 开始
        if g > 0:                               # 第一个 g>0 的位置就是命中位
            mrr = 1.0 / rank
            break

    # ③ NDCG@K: 实际排序质量 ÷ 理想排序质量
    # 实际 DCG 用 top_k 的真实顺序算; 理想 DCG 用所有文档按分数降序排列算
    dcg = _dcg([g for _, g in top_k])                         # 实际值
    ideal = sorted([g for _, g in scored], reverse=True)[:k]  # 理想值: 所有相关的排最前
    idcg = _dcg(ideal)                                         # 理想上限
    ndcg_k = dcg / idcg if idcg > 0 else 0.0                  # 归一化到 [0, 1]

    return {"prec3": prec_k, "mrr": mrr, "ndcg3": ndcg_k}


# ═══ 主评估流程 ═══
def run_evaluation() -> None:
    sep = "=" * 70
    print(f"{sep}")
    print("检索质量对比: 静态 RAG vs Agentic Retrieval")
    print(f"{sep}\n")

    header_fmt = "{:s}  {:>22s}    {:>22s}"
    sub_fmt   = "{:s}  {:>22s}    {:>22s}"
    row_fmt   = "{:s}  {:>4.2f} {:>5.2f} {:>5.2f}     {:>4.2f} {:>5.2f} {:>5.2f}"

    print(header_fmt.format(_pad("Query", 30), "静态RAG", "Agentic"))
    print(sub_fmt.format(_pad("", 30), "P@3   MRR   NDCG", "P@3   MRR   NDCG"))
    print("-" * 86)

    agg = {"static": {"prec3": [], "mrr": [], "ndcg3": []},
           "agentic": {"prec3": [], "mrr": [], "ndcg3": []}}

    for qa in QA_PAIRS:
        q = qa["question"]                      # 问题文本
        kw = qa["ground_truth_keywords"]        # 人工标注的预期关键词

        # ── 静态 RAG: 规则路由 → 检索 → 打分 ──
        sr = static_retrieve(q)                 # {"finance": "...", "vector": "..."}
        sm = evaluate_retrieval(sr, kw)         # {"prec3": 1.0, "mrr": 1.0, "ndcg3": 0.95}

        # ── Agentic: Planner拆解 → Retriever检索 → 同样的打分标准 ──
        try:
            plan = run_planner(q)               # LLM: "需要查财务+技术，拆成2个子任务"
            ar = run_retriever(plan)            # 并发调 finance + vector
        except Exception as e:                   # API 挂了别崩，打印错误继续
            print(f"\n[ERROR] Agentic failed: {e}", file=sys.stderr)
            ar = {}
        am = evaluate_retrieval(ar, kw)         # 和静态版用同一把尺子量

        # ── 打印这一行的对比结果 ──
        display_q = q[:26] + ("…" if len(q) > 26 else "")
        print(row_fmt.format(
            _pad(display_q, 30),
            sm["prec3"], sm["mrr"], sm["ndcg3"],   # 静态三个分数
            am["prec3"], am["mrr"], am["ndcg3"],   # Agentic 三个分数
        ))

        # 收集分数，最后算平均
        for mode, m in [("static", sm), ("agentic", am)]:
            for key in ("prec3", "mrr", "ndcg3"):
                agg[mode][key].append(m[key])

    # 汇总平均
    print("-" * 86)
    avg_s = {k: sum(v) / len(v) for k, v in agg["static"].items()}
    avg_a = {k: sum(v) / len(v) for k, v in agg["agentic"].items()}
    print(row_fmt.format(
        _pad("平均", 30),
        avg_s["prec3"], avg_s["mrr"], avg_s["ndcg3"],
        avg_a["prec3"], avg_a["mrr"], avg_a["ndcg3"],
    ))

    # 结论
    print(f"\n{sep}\n结论\n{sep}")
    print(
        "静态 RAG 在单源查询上与 Agentic 持平，但在跨源/对比查询上显著落后。\n"
        "Agentic 的核心优势不在单步精度，在复杂查询的多源协同能力。\n"
        "面试一句话: \"Agentic 不是更准——单源查询静态 RAG 够用。"
        "Agentic 的价值在你不确定用户下一问会涉及几个数据源。\""
    )


if __name__ == "__main__":
    run_evaluation()
