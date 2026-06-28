"""双维评估 — RAGAS 生成质量 + NDCG/MRR 排序质量 交叉验证

面试: "评估体系双维——RAGAS 四维测生成质量(LLM黑盒), NDCG/MRR 测排序质量(人工qrels白盒)。
       两者从不同角度验证同一件事, 交叉验证比单一指标可靠。生产加 Langfuse 做在线漂移检测。"
"""

import os
import sys
import math
from unittest.mock import MagicMock

# 已知 workaround: langchain_community.vertexai 在非 GCP 环境导入会报错，
# 提前 mock 避免 LlamaIndex 导入链触发异常，不影响功能。
sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()
sys.modules["langchain_community.chat_models.vertexai"].ChatVertexAI = MagicMock()

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document, PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb, numpy as np

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from langchain_huggingface import HuggingFaceEmbeddings as LCHFEmbeddings

# ═══════════════ Setup ═══════════════

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY not configured")

# Demo 模式：直接设置全局 Settings，生产环境应通过参数显式传入。
Settings.llm = OpenAILike(
    model="deepseek-chat", api_key=api_key, api_base="https://api.deepseek.com",
    temperature=0.1, is_chat_model=True, max_retries=3,
)

from openai import OpenAI as OpenAIClient
from ragas.llms import llm_factory
eval_llm = llm_factory("deepseek-chat",
    client=OpenAIClient(api_key=api_key, base_url="https://api.deepseek.com", max_retries=3))

# 只加载一次 embedding 模型，llama_index 通过 LangchainEmbedding 复用同一个实例
lc_embeddings = LCHFEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
from llama_index.embeddings.langchain import LangchainEmbedding
Settings.embed_model = LangchainEmbedding(lc_embeddings)

# ═══════════════ Documents（12 篇精简版，同 ingest.py） ═══════════════
# (text, doc_id)
_DOC_PAIRS = [
    ("Q3 2026 Revenue 38.2B CNY (+18% YoY), net profit 5.8B. Cloud +35%, AI +62%. Gross margin 48.2%. Q4 guidance 40-42B, full-year target 150B.", "RES_PDF_001"),
    ("Semiconductor Trend: AI chip demand +45% YoY. Domestic substitution 65% for 14nm+. SMIC 28nm capacity +30%. Recommend overweight equipment sector.", "RES_PDF_002"),
    ("Fundamentals: Market Cap 520B, PE(TTM) 35.2, PB 4.8. ROE 18.5%, ROA 8.2%. D/E 0.45, Current Ratio 1.8. Revenue CAGR 22%, FCF 22B.", "RES_DB_001"),
    ("CONFIDENTIAL: Credit risk assessment — 3 clients Watch, exposure 2.4B CNY. Provision coverage increase from 2.1% to 2.8% by Q4 2026.", "RES_PDF_003"),
    ("H2 2026 Market Outlook: SSE 3200-3600, CSI 300 target 4200-4500. Overweight financials, underweight real estate. PBOC RRR cut expected Q3.", "TRD_PDF_001"),
    ("Market Data 6/25: CSI 300 3958.2 (+1.2%), SSE 3356.7 (+0.8%), SZSE 10820.5 (+1.5%), HSI 19820.5 (-0.3%). USD/CNY 7.12, Gold 2350, Brent 82.5.", "TRD_API_001"),
    ("CONFIDENTIAL: Positions AUM 8.5B. Tech 35%, Financials 25%. Top holdings: CITIC Sec 1.2B, Moutai 0.95B, CATL 0.82B. YTD P&L +380M CNY.", "TRD_DB_001"),
    ("CONFIDENTIAL: BUY signal 600036 CMB. Confidence 0.87. MACD golden cross, RSI 42. Target 45.2 (+15%), stop 36.5 (-7%). Expires 48 hours.", "TRD_API_002"),
    ("CSRC Regulation 2026-47: Pre-trade risk controls mandatory for algo trading by Jan 2027. Kill-switch 50ms, full audit trail. Penalty up to 5M CNY + suspension.", "CMP_PDF_001"),
    ("Audit Q2 2026: 12,847 trades reviewed, 3 flagged (wash trading 85M, manipulation 120M, unauthorized algo change). Compliance score 94.2/100.", "CMP_DB_001"),
    ("OFAC SDN Update 6/24: 6 entities added, 2 APAC-applicable (DPRK-linked shipping, Iran oil). Required: freeze assets, file SAR within 30 days.", "CMP_API_001"),
    ("CONFIDENTIAL: Investigation Case 2026-07 — Trader TRD-3421 unauthorized 5M USD transfer to Cayman. Dual-control bypassed. Recommend termination.", "CMP_PDF_002"),
]
documents = [Document(text=t, metadata={"doc_id": did}) for t, did in _DOC_PAIRS]

# Build index (no ACL filter — evaluating retrieval quality itself)
chroma_client = chromadb.EphemeralClient()
try: chroma_client.delete_collection("smart_report_eval")
except ValueError: pass
collection = chroma_client.get_or_create_collection("smart_report_eval")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
query_engine = index.as_query_engine(similarity_top_k=5, text_qa_template=PromptTemplate(
    "Context:\n{context_str}\n\nAnswer using context only. Include specific numbers.\nQuery: {query_str}\nAnswer: "))

# ═══════════════ 5 QA Pairs（跨源/单一/跨部门） ═══════════════

QA_PAIRS = [
    ("What was the Q3 2026 revenue, net profit, and what drove the growth?",
     "Q3 2026 revenue 38.2B CNY (+18% YoY), net profit 5.8B. Growth drivers: cloud computing +35%, AI business +62%. Gross margin improved to 48.2%. Q4 guidance 40-42B CNY."),
    ("What is the current PE ratio, ROE, and debt-to-equity ratio of the company?",
     "PE(TTM) 35.2, PB 4.8, ROE 18.5%, ROA 8.2%. D/E ratio 0.45, Current Ratio 1.8. Market Cap 520B CNY, Revenue CAGR 22% (3yr), FCF 22B CNY."),
    ("What are the semiconductor industry trends and the H2 2026 market outlook?",
     "AI chip demand +45% YoY, domestic substitution 65% for 14nm+. SMIC 28nm capacity +30%. H2 2026: SSE 3200-3600, CSI 300 target 4200-4500, overweight financials, PBOC RRR cut expected Q3."),
    ("What new regulations affect algorithmic trading and what are the requirements?",
     "CSRC Regulation 2026-47 mandates pre-trade risk controls for all algorithmic trading by January 2027. Requirements: real-time order validation, kill-switch within 50ms, full audit trail. Penalty up to 5M CNY + suspension."),
    ("What are the current market index levels, gold price, oil price, and USD/CNY exchange rate?",
     "CSI 300 at 3958.2 (+1.2%), SSE Composite 3356.7 (+0.8%), SZSE 10820.5 (+1.5%), HSI 19820.5 (-0.3%). USD/CNY 7.12. Gold 2350 USD/oz. Brent crude 82.5 USD/bbl."),
]

# ═══════════════ Part 1: RAGAS Evaluation ═══════════════

print("=" * 70)
print("Part 1: RAGAS Evaluation — 生成质量四维评估")
print("=" * 70)

questions, answers, contexts_list, ground_truths = [], [], [], []
# 缓存 Part1 的 response 对象，Part2 直接复用，避免重复查询破坏交叉验证前提
_cached_responses = []
for i, (q, gt) in enumerate(QA_PAIRS, 1):
    try:
        response = query_engine.query(q)
        questions.append(q); answers.append(str(response))
        contexts_list.append([n.text for n in response.source_nodes])
        ground_truths.append(gt)
        _cached_responses.append(response)
        print(f"  [Q{i}] {(q[:60]+'...'):<63} contexts={len(contexts_list[-1])}")
    except Exception as e:
        # 查询失败时跳过该样本，不追加空数据污染评估指标
        print(f"  [Q{i}] SKIPPED (query failed): {e}")
        continue

eval_dataset = Dataset.from_dict({
    "question": questions, "answer": answers, "contexts": contexts_list, "ground_truth": ground_truths,
})
ragas_result = evaluate(eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
    llm=eval_llm, embeddings=lc_embeddings)

def _avg(lst):
    vals = [v for v in lst if isinstance(v, (int, float)) and not math.isnan(v)]
    return sum(vals) / len(vals) if vals else float("nan")

ragas_scores = {}
print(f"\n{'Metric':<22} {'Score':>8}\n{'-'*32}")
for m in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]:
    raw = ragas_result[m]
    score = _avg(raw) if isinstance(raw, list) else raw
    ragas_scores[m] = score
    flag = " ✓" if isinstance(score, float) and not math.isnan(score) and score >= 0.6 else ""
    print(f"{m:<22} {score:>8.4f}{flag}")

# ═══════════════ Part 2: NDCG@5 + MRR（排序质量，人工 qrels） ═══════════════

print(f"\n{'='*70}\nPart 2: NDCG@5 & MRR — 排序质量（人工 qrels 3=精确 2=相关 1=边缘 0=无关）\n{'='*70}")

doc_ids = [did for _, did in _DOC_PAIRS]
# qrels 按 doc_ids 顺序（RES_PDF_001..CMP_PDF_002）
qrel_lists = {
    "Q1-Revenue":       [3,0,1,0, 0,0,0,0, 0,0,0,0],
    "Q2-Fundamentals":  [1,0,3,0, 0,0,0,0, 0,0,0,0],
    "Q3-TrendOutlook":  [0,3,0,0, 2,1,0,0, 0,0,0,0],
    "Q4-Regulation":    [0,0,0,0, 0,0,0,0, 3,2,0,0],
    "Q5-MarketData":    [0,0,0,0, 1,3,0,0, 0,0,0,0],
}
_qmap = {did: i for i, did in enumerate(doc_ids)}

def dcg(r, k):
    return sum(((2**v - 1) / math.log2(i + 2)) for i, v in enumerate(r[:k]))

def ndcg_k(pred, ideal, k):
    d, i = dcg(pred, k), dcg(sorted(ideal, reverse=True), k)
    return d / i if i > 0 else 0.0

def mrr_val(pred):
    for i, r in enumerate(pred, 1):
        if r > 0: return 1.0 / i
    return 0.0

queries_ndcg = {f"Q{i+1}-{k.split()[0]}": QA_PAIRS[i][0] for i, k in enumerate(
    ["Revenue", "Fundamentals", "TrendOutlook", "Regulation", "MarketData"])}

print(f"\n{'Query':<22} {'Top-5 Retrieved (doc_id:rel)':<55} {'NDCG@5':>8} {'MRR':>8}\n{'-'*95}")
ndcg_s, mrr_s = [], []
# Part2 复用 Part1 缓存的 response，不再重复查询，保证交叉验证的可比性
_qid_to_idx = {"Q1-Revenue": 0, "Q2-Fundamentals": 1, "Q3-TrendOutlook": 2,
               "Q4-Regulation": 3, "Q5-MarketData": 4}
top_k = 5
for qid, qtext in queries_ndcg.items():
    qi = _qid_to_idx.get(qid, -1)
    if qi < 0 or qi >= len(_cached_responses):
        print(f"{qid:<22} {'(no cached response)':<55} {'N/A':>8} {'N/A':>8}")
        continue
    resp = _cached_responses[qi]
    ret_ids = [n.metadata.get("doc_id","?") for n in resp.source_nodes]
    ideal = qrel_lists[qid]
    pred = [ideal[_qmap[rid]] if rid in _qmap else 0 for rid in ret_ids]
    while len(pred) < top_k: pred.append(0)
    # MRR 计算前强制截断到 top_k，避免长度不一致导致误差
    n, m = ndcg_k(pred, ideal, top_k), mrr_val(pred[:top_k])
    ndcg_s.append(n); mrr_s.append(m)
    print(f"{qid:<22} {', '.join(f'{rid}({r})' for rid,r in zip(ret_ids,pred)):<55} {n:>8.4f} {m:>8.4f}")

# ═══════════════ Part 3: 双维交叉验证报告 ═══════════════

avg_n, avg_m = np.mean(ndcg_s), np.mean(mrr_s)
print(f"\n{'='*70}\nPart 3: 双维交叉验证报告\n{'='*70}")
print(f"""
  维度 A — RAGAS 生成质量:
    faithfulness      {ragas_scores.get('faithfulness', 'N/A'):>10}
    answer_relevancy  {ragas_scores.get('answer_relevancy', 'N/A'):>10}
    context_recall    {ragas_scores.get('context_recall', 'N/A'):>10}
    context_precision {ragas_scores.get('context_precision', 'N/A'):>10}

  维度 B — NDCG/MRR 排序质量:
    Avg NDCG@5  {avg_n:.4f}
    Avg MRR     {avg_m:.4f}

  交叉验证逻辑:
    RAGAS Context Precision — LLM 判断「检索出的文档是否相关」(黑盒)
    NDCG@5 + MRR — 公式计算「相关文档是否排在前面」(白盒)
    → 两者都高 = 检索质量可靠；相差大 = 需排查 qrels 标注或 LLM 评估器
""")
print("=" * 70)
print("面试要点")
print("=" * 70)
print("""
  1. "双维评估: RAGAS 四维 + NDCG/MRR 排序, 交叉验证比单一指标可靠"
  2. "RAGAS 用 LLM 判断相关性(黑盒可规模化), NDCG 用人工 qrels(白盒可解释)"
  3. "Context Precision ≈ NDCG 高正相关时 → 评估体系自身可信"
  4. "生产加 Langfuse 在线追踪: 离线定基线, 在线做漂移检测"
""")
