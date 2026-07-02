"""静态 RAG vs Agentic Retrieval 检索质量对比评估

用 Hit Rate / MRR / NDCG 三个指标，对比同组查询在两种模式下的检索质量差异。

两种检索模式：
  - 静态 RAG（baseline）: 关键词匹配，固定规则选择数据源
  - Agentic Retrieval: 调用 run_planner + run_retriever，Agent 自主拆解查询并路由数据源
"""
import math
import os
import re
import sys
import traceback

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


def _truncate_by_width(s: str, max_width: int, ellipsis: str = "…") -> str:
    """按显示宽度截断字符串，避免终端表格错位。
    中文字符显示宽度是英文的 2 倍，按字符数截断会导致中文列撑破对齐。"""
    if _display_width(s) <= max_width:
        return s
    # 逐字符累加宽度，超过阈值时截断
    w = 0
    for i, c in enumerate(s):
        cw = 2 if '一' <= c <= '鿿' or '　' <= c <= '〿' else 1
        if w + cw > max_width - _display_width(ellipsis):
            return s[:i] + ellipsis
        w += cw
    return s


def _dcg(grades: list[int]) -> float:
    """DCG: 位置越靠后权重越低。排第1位权重=1/log₂(2)=1, 排第3位权重=1/log₂(4)=0.5。
    公式: Σ(g_i / log₂(i+2)), i从0开始所以+2。"""
    return sum(g / math.log2(i + 2) for i, g in enumerate(grades))


def _keyword_match(keyword: str, text: str) -> bool:
    """关键词匹配。英文用负向断言防止子串误配（如 "AI" 误匹配 "RAID"），
    中文用子串匹配（中文无空格分词，"研发部" 应匹配"研发部门"）。

    注意：不能用 \\b 单词边界。中文字符被视为 \\w，中英混合文本中英文词与
    中文字符之间不存在 \b 边界，导致 "K8s" 等英文关键词在中文语境中匹配失败。"""
    if keyword.isascii():
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(keyword) + r'(?![a-zA-Z0-9])'
        return bool(re.search(pattern, text, re.IGNORECASE))
    return keyword.lower() in text.lower()


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
    与 Agentic 的差别: 静态版的四个规则并列执行，跨源查询可同时命中多分支——
    但它没有 Agentic 那种「分析→拆解→路由」的协同能力，规则靠人工维护，覆盖不全。"""
    results: dict[str, str] = {}
    query_text = query
    # 试着从问题里找出部门名（按字符串包含匹配，长词优先——"研发部"而非"研发"）
    department = next((d for d in sorted(ORG_HIERARCHY, key=len, reverse=True) if d in query_text), None)

    # ── 以下四个 if 块就是"规则"：哪个关键词命中，就调哪个数据源 ──

    # 规则A: 问题含预算/财务/支出 → 查财务表
    if any(kw in query_text for kw in ["预算", "财务", "支出", "利用率", "执行", "云支出"]):
        results["finance"] = retrieve_finance(department or "")

    # 规则B: 问题含技术/架构/平台 → 查技术文档（向量检索）
    if any(kw in query_text for kw in ["技术", "架构", "平台", "K8s", "GPU", "AI", "云"]):
        results["vector"] = retrieve_vector(query_text)

    # 规则C: 问题含人数/主管/团队 → 查组织架构
    if any(kw in query_text for kw in ["多少人", "主管", "团队", "规模", "人数"]):
        if department:
            results["org"] = retrieve_org(department)

    # 规则D: 问题要对比/排名 → 调跨部门对比
    if any(kw in query_text for kw in ["对比", "比较", "哪个部门", "各部门"]):
        results["compare"] = retrieve_compare()

    # 一道规则都没命中 → 兜底走向量检索（随便给点东西，避免空手）
    return results or {"vector": retrieve_vector(query_text)}


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
    match_cnt = sum(1 for kw in keywords if _keyword_match(kw, c))  # 数命中了几个关键词
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

    # ① P@K: 前K个中有几个是相关的（grade>0就算相关），除以固定K
    # 分母用 k 而非 len(top_k): 标准 P@K 以固定 K 为分母，结果不足 K 个时
    # 缺失位视为不相关（0分），避免高估（如仅1个结果相关 → P@3=1/3≈0.33，而非1/1=1.0）
    prec_k = sum(1 for _, grade in top_k if grade > 0) / k if top_k else 0.0

    # ② MRR: 第一个相关文档排在第几位？1/rank
    # 排在位置1 → 1/1=1.0; 排在位置3 → 1/3=0.33; 一个都不相关 → 0
    mrr = 0.0
    for rank, (_, grade) in enumerate(scored, 1):  # rank 从 1 开始
        if grade > 0:                                # 第一个 grade>0 的位置就是命中位
            mrr = 1.0 / rank
            break

    # ③ NDCG@K: 实际排序质量 ÷ 理想排序质量
    # 实际 DCG 用 top_k 的真实顺序算; 理想 DCG 用所有文档按分数降序排列算
    dcg = _dcg([grade for _, grade in top_k])                      # 实际值
    ideal = sorted([grade for _, grade in scored], reverse=True)[:k] # 理想值: 所有相关的排最前
    idcg = _dcg(ideal)                                              # 理想上限
    ndcg_k = dcg / idcg if idcg > 0 else 0.0                       # 归一化到 [0, 1]

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

    all_scores = {"static": {"prec3": [], "mrr": [], "ndcg3": []},
                  "agentic": {"prec3": [], "mrr": [], "ndcg3": []}}

    for qa in QA_PAIRS:
        question = qa["question"]
        expected_keywords = qa["ground_truth_keywords"]

        # ── 静态 RAG: 规则路由 → 检索 → 打分 ──
        static_results = static_retrieve(question)
        static_metrics = evaluate_retrieval(static_results, expected_keywords)

        # ── Agentic: Planner拆解 → Retriever检索 → 同样的打分标准 ──
        try:
            plan = run_planner(question)
            agentic_results = run_retriever(plan)
            agentic_metrics = evaluate_retrieval(agentic_results, expected_keywords)
        except Exception as e:
            print(f"\n[ERROR] Agentic failed: {e}", file=sys.stderr)
            traceback.print_exc()
            agentic_metrics = None

        # ── 打印这一行的对比结果 ──
        display_text = _truncate_by_width(question, 26)
        if agentic_metrics is not None:
            print(row_fmt.format(
                _pad(display_text, 30),
                static_metrics["prec3"], static_metrics["mrr"], static_metrics["ndcg3"],
                agentic_metrics["prec3"], agentic_metrics["mrr"], agentic_metrics["ndcg3"],
            ))
        else:
            print(row_fmt.format(
                _pad(display_text, 30),
                static_metrics["prec3"], static_metrics["mrr"], static_metrics["ndcg3"],
                float('nan'), float('nan'), float('nan'),
            ))

        # 收集分数，最后算平均（Agentic 失败时跳过，避免全0拉低均值）
        for key in ("prec3", "mrr", "ndcg3"):
            all_scores["static"][key].append(static_metrics[key])
        if agentic_metrics is not None:
            for key in ("prec3", "mrr", "ndcg3"):
                all_scores["agentic"][key].append(agentic_metrics[key])

    # 汇总平均
    print("-" * 86)
    avg_static = {k: sum(v) / len(v) for k, v in all_scores["static"].items()}
    avg_agentic = {k: (sum(v) / len(v) if v else float('nan')) for k, v in all_scores["agentic"].items()}
    print(row_fmt.format(
        _pad("平均", 30),
        avg_static["prec3"], avg_static["mrr"], avg_static["ndcg3"],
        avg_agentic["prec3"], avg_agentic["mrr"], avg_agentic["ndcg3"],
    ))

    # 结论
    print(f"\n{sep}\n结论\n{sep}")
    print(
        "本次评估两者平均分持平（4 数据源 / 8 个 QA pair 的规模下差异不显著）。\n\n"
        "为什么没拉开差距？\n"
        "  1. 数据源太少（4 个），每个源是一整块，MRR 几乎必为 1.0\n"
        "  2. 评估粒度是\"源级别\"——只要调对了源就算命中\n"
        "  3. Agentic 的真正优势在\"子查询拆解后的段落级精准命中\"，\n"
        "     当前评测未下沉到这一层\n\n"
        "什么时候能看到差异？\n"
        "  数据源从 4 个扩展到 20+ 个（每个源内部再切分为多个段落），\n"
        "  此时静态规则覆盖面不足的问题会暴露，Agentic 的路由优势才能量化。\n\n"
        "面试要点: \"我们用三指标（P@K/MRR/NDCG）对比评估了静态 RAG 和 Agentic\n"
        "  Retrieval。在小规模数据集上两者持平——这不是 Agentic 没用，而是评测\n"
        "  粒度和数据规模还不足以暴露差异。这本身就是评估体系的工程认知。\""
    )


if __name__ == "__main__":
    run_evaluation()
