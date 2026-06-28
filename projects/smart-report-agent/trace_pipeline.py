"""Langfuse 全链路追踪 — 企业 RAG 可观测层

查询→检索→生成全链路接入 Langfuse:
  - 每条查询一条 Trace（retrieval span + generation span）
  - 自动记录: 检索命中数、延迟、来源分布
  - Langfuse 不可用时优雅降级（_NoopSpan + console fallback）

面试:
  "Langfuse 全链路追踪——不是等投诉才发现问题。Dashboard 实时 Faithfulness 分布，
   低于 0.7 自动告警。离线 RAGAS 定基线, 在线做漂移检测, 避免 embedding 退化才发现。"
"""

import os, sys, time
from pathlib import Path
from unittest.mock import MagicMock

sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()
sys.modules["langchain_community.chat_models.vertexai"].ChatVertexAI = MagicMock()

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document, PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# ═══════════════ Langfuse 初始化（优雅降级） ═══════════════

LANGFUSE_AVAILABLE = False
_langfuse = None
try:
    from langfuse import Langfuse
    _langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
    )
    if _langfuse.auth_check():
        LANGFUSE_AVAILABLE = True
        print("[Langfuse] Connected.")
    else:
        print("[Langfuse] Not configured — console only.")
except Exception as e:
    print(f"[Langfuse] Unavailable ({e}) — console only.")

# ═══════════════ Setup: LLM + Embedding + Index ═══════════════

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY not configured")

Settings.llm = OpenAILike(
    model="deepseek-chat", api_key=api_key, api_base="https://api.deepseek.com",
    temperature=0.1, is_chat_model=True, max_retries=3,
)
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 7 篇代表性文档（覆盖 3 租户 × 3 数据源）
_DOCS = [
    ("Q3 2026 Revenue 38.2B (+18% YoY), profit 5.8B. Cloud +35%, AI +62%. Q4 guidance 40-42B.",
     "research", "public", "pdf_report", "RES_PDF_001"),
    ("Fundamentals: PE 35.2, PB 4.8, ROE 18.5%, D/E 0.45, Market Cap 520B, FCF 22B.",
     "research", "public", "db_record", "RES_DB_001"),
    ("CONFIDENTIAL: Credit risk — 3 clients Watch, exposure 2.4B. Provision coverage target 2.8%.",
     "research", "confidential", "pdf_report", "RES_PDF_003"),
    ("H2 2026 Outlook: CSI 300 target 4200-4500. Overweight financials. PBOC RRR cut Q3.",
     "trading", "public", "pdf_report", "TRD_PDF_001"),
    ("Market Data: CSI 300 3958.2 (+1.2%), HSI 19820.5 (-0.3%). USD/CNY 7.12, Gold 2350.",
     "trading", "public", "api_json", "TRD_API_001"),
    ("CSRC 2026-47: Pre-trade risk controls for algo trading by Jan 2027. Kill-switch 50ms.",
     "compliance", "public", "pdf_report", "CMP_PDF_001"),
    ("OFAC SDN: 6 entities added, 2 APAC-applicable. Freeze assets, SAR 30 days.",
     "compliance", "public", "api_json", "CMP_API_001"),
]
documents = [Document(text=t, metadata={
    "tenant": tn, "access_level": al, "source_type": st, "doc_id": did,
}) for t, tn, al, st, did in _DOCS]

chroma_client = chromadb.Client()
try: chroma_client.delete_collection("trace_demo")
except (ValueError, chromadb.errors.NotFoundError): pass
collection = chroma_client.get_or_create_collection("trace_demo")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

# ═══════════════ Traced RAG Pipeline ═══════════════

class TracedRAGPipeline:
    """Langfuse 全链路追踪 RAG Pipeline。

    Trace 结构: smart-report-query
      ├── span: acl-retrieval (延迟/命中数/来源分布)
      ├── generation: llm-answer (model + tokens)
      └── score: retrieved_count (事后追加 faithfulness 等)
    """

    def __init__(self, idx):
        self.query_engine = idx.as_query_engine(similarity_top_k=3, text_qa_template=PromptTemplate(
            "Context:\n{context_str}\n\nAnswer using context. Include specific numbers.\nQuery: {query_str}\nAnswer: "))

    def query(self, question, user_id="alice"):
        trace = None
        if LANGFUSE_AVAILABLE:
            trace = _langfuse.trace(name="smart-report-query", user_id=user_id,
                                     metadata={"question": question})

        # Retrieval span
        span = trace.span(name="acl-retrieval", metadata={"top_k": 3}) if trace else _NoopSpan()
        with span:
            t0 = time.time()
            response = self.query_engine.query(question)
            elapsed = round((time.time() - t0) * 1000, 1)
            docs = []
            for node in response.source_nodes:
                meta = node.metadata
                docs.append({"doc_id": meta.get("doc_id"), "source_type": meta.get("source_type"),
                             "tenant": meta.get("tenant"), "snippet": node.text[:100]})
            span.update(metadata={"latency_ms": elapsed}, output={"count": len(docs), "docs": docs})

        # Generation span
        if trace:
            gen = trace.generation(name="llm-answer", model="deepseek-chat",
                input={"question": question, "context_count": len(docs)},
                output={"answer": str(response)})
            gen.end()
            trace.score(name="retrieved_count", value=len(docs))
            trace.update(output={"answer": str(response)})

        return {"answer": str(response), "retrieved_docs": docs,
                "latency_ms": elapsed, "traced": LANGFUSE_AVAILABLE}


class _NoopSpan:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def update(self, **kwargs): pass

# ═══════════════ Demo ═══════════════

if __name__ == "__main__":
    pipeline = TracedRAGPipeline(index)
    print("=" * 70)
    print(f"Smart Report Agent — Langfuse 全链路追踪")
    print(f"Langfuse: {'CONNECTED' if LANGFUSE_AVAILABLE else 'UNAVAILABLE (console)'}")
    print("=" * 70)

    queries = [
        ("alice", "What is the Q3 2026 revenue and growth drivers?"),
        ("dave",  "What is the H2 2026 market outlook and current index levels?"),
        ("frank", "What new regulations affect algorithmic trading?"),
    ]
    for uid, q in queries:
        print(f"\n{'─'*70}\nUser={uid} | Query: {q}")
        r = pipeline.query(q, user_id=uid)
        print(f"Latency: {r['latency_ms']}ms | Docs: {len(r['retrieved_docs'])} | Traced: {r['traced']}")
        print(f"Answer: {r['answer'][:150]}...")
        for d in r["retrieved_docs"]:
            print(f"  → [{d['source_type']}:{d['doc_id']}] {d['snippet'][:70]}...")

    print(f"\n{'='*70}\nTrace 结构\n{'='*70}")
    print("""
  smart-report-query (trace)
  ├── acl-retrieval (span)
  │     ├── metadata: top_k=3, latency_ms=xxx
  │     └── output: [{doc_id, source_type, tenant, snippet}, ...]
  ├── llm-answer (generation)
  │     ├── model: deepseek-chat, input: question+context
  │     └── output: answer text
  └── Scores: retrieved_count (+ 生产环境异步追加 faithfulness 等)

  生产流程: 查询 → Langfuse trace → 10%采样异步 RAGAS → score 回写
           → Dashboard 趋势图 → Faithfulness 掉到 0.6 → PagerDuty 告警
""")
    if not LANGFUSE_AVAILABLE:
        print("""启动本地 Langfuse:
  docker run -d --name langfuse -p 3000:3000 -p 3030:3030 langfuse/langfuse
  export LANGFUSE_PUBLIC_KEY=pk-xxx LANGFUSE_SECRET_KEY=sk-xxx LANGFUSE_HOST=http://localhost:3000
""")
