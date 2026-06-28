"""权限感知查询引擎 — 租户隔离 + 角色 ACL + 可审计引用

特性: mock session 解析 tenant/role → ChromaDB where clause 预过滤 → 来源标注 + 引用列表
面试: "权限在检索层做——where clause 预过滤，敏感文档不进入 context window。
       既安全（防 prompt 注入泄露）又省 token（只送有权文档给 LLM）。"
"""

import os
import sys
from unittest.mock import MagicMock

# 已知 workaround: langchain_community.vertexai 在非 GCP 环境导入会报错，
# 提前 mock 避免 LlamaIndex 导入链触发异常，不影响功能。
sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()
sys.modules["langchain_community.chat_models.vertexai"].ChatVertexAI = MagicMock()

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# ═══════════════ Setup ═══════════════

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY not configured")

# Demo 模式：直接设置全局 Settings，生产环境应通过参数显式传入。
Settings.llm = OpenAILike(
    model="deepseek-chat", api_key=api_key, api_base="https://api.deepseek.com",
    temperature=0.1, is_chat_model=True, max_retries=3,
)
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ═══════════════ Mock Session（生产环境替换为 JWT + Redis） ═══════════════

MOCK_SESSIONS = {
    "alice":  {"tenant": "research",   "role": "manager"},
    "bob":    {"tenant": "research",   "role": "engineer"},
    "carol":  {"tenant": "research",   "role": "intern"},
    "dave":   {"tenant": "trading",    "role": "manager"},
    "eve":    {"tenant": "trading",    "role": "intern"},
    "frank":  {"tenant": "compliance", "role": "manager"},
    "grace":  {"tenant": "compliance", "role": "intern"},
}

def resolve_session(user_id):
    session = MOCK_SESSIONS.get(user_id)
    if not session:
        raise ValueError(f"Unknown user: {user_id}")
    return session

# ═══════════════ ACL Filter（继承 Day13 acl_retrieval.py 权限模型） ═══════════════

ALLOWED_ROLES = {"intern", "engineer", "manager"}

def build_acl_where(tenant, role):
    """ChromaDB where clause: tenant 精确匹配 + role_XXX 布尔过滤。
    LlamaIndex MetadataFilters 在 $and + 布尔组合上兼容性不稳定，直接调 ChromaDB。"""
    if role and role not in ALLOWED_ROLES:
        raise ValueError(f"Invalid role: {role}")
    return {"$and": [{"tenant": tenant}, {f"role_{role}": True}]}

# ═══════════════ Document Specs（12 篇，元组驱动精简定义） ═══════════════
# (text, tenant, access_level, intern, engineer, manager, source_type, doc_id, timestamp)

_DOCS = [
    # research: 3 public + 1 confidential
    ("[RES_PDF_001] Q3 2026 Revenue 38.2B CNY (+18% YoY), profit 5.8B. Cloud +35%, AI +62%. Gross margin 48.2%. Q4 guidance 40-42B.",
     "research", "public", True, True, True, "pdf_report", "RES_PDF_001", "2026-06-20"),
    ("[RES_PDF_002] Semiconductor Trend: AI chip demand +45% YoY. Domestic substitution 65% for 14nm+. SMIC 28nm capacity +30%. Overweight equipment.",
     "research", "public", True, True, True, "pdf_report", "RES_PDF_002", "2026-06-18"),
    ("[RES_DB_001] Fundamentals: Market Cap 520B, PE 35.2, PB 4.8, ROE 18.5%. Revenue TTM 142B, FCF 22B. D/E 0.45, CAGR 3yr 22%.",
     "research", "public", True, True, True, "db_record", "RES_DB_001", "2026-06-25"),
    ("[RES_PDF_003] CONFIDENTIAL: Credit risk — 3 clients Watch, total exposure 2.4B. Provision coverage target 2.8% by Q4.",
     "research", "confidential", False, True, True, "pdf_report", "RES_PDF_003", "2026-06-22"),
    # trading: 2 public + 2 confidential
    ("[TRD_PDF_001] H2 2026 Outlook: SSE 3200-3600, CSI 300 target 4200-4500. Overweight financials. PBOC RRR cut expected Q3.",
     "trading", "public", True, True, True, "pdf_report", "TRD_PDF_001", "2026-06-24"),
    ("[TRD_API_001] Market 6/25: CSI 300 3958.2 (+1.2%), SSE 3356.7, HSI 19820.5 (-0.3%). USD/CNY 7.12, Gold 2350, Brent 82.5.",
     "trading", "public", True, True, True, "api_json", "TRD_API_001", "2026-06-25"),
    ("[TRD_DB_001] CONFIDENTIAL: Positions AUM 8.5B. Tech 35%, Financials 25%. Top: CITIC Sec 1.2B, Moutai 0.95B, CATL 0.82B. +380M YTD.",
     "trading", "confidential", False, True, True, "db_record", "TRD_DB_001", "2026-06-25"),
    ("[TRD_API_002] CONFIDENTIAL: BUY 600036 CMB. Confidence 0.87. Target 45.2 (+15%), stop 36.5. MACD golden cross, RSI 42. Expires 48h.",
     "trading", "confidential", False, False, True, "api_json", "TRD_API_002", "2026-06-25"),
    # compliance: 3 public + 1 confidential
    ("[CMP_PDF_001] CSRC 2026-47: Pre-trade risk controls for algo trading by Jan 2027. Kill-switch 50ms, audit trail. Penalty up to 5M+ CNY.",
     "compliance", "public", True, True, True, "pdf_report", "CMP_PDF_001", "2026-06-21"),
    ("[CMP_DB_001] Audit Q2: 12,847 trades reviewed. 3 flagged (wash trading 85M, manipulation 120M, unauthorized algo). Score 94.2/100.",
     "compliance", "public", True, True, True, "db_record", "CMP_DB_001", "2026-06-23"),
    ("[CMP_API_001] OFAC SDN Update: 6 entities added, 2 APAC-applicable (DPRK shipping, Iran oil). Zero exposure.",
     "compliance", "public", True, True, True, "api_json", "CMP_API_001", "2026-06-25"),
    ("[CMP_PDF_002] CONFIDENTIAL: Case 2026-07 — Trader TRD-3421 unauthorized 5M USD to Cayman. Dual-control bypassed. Recommend termination.",
     "compliance", "confidential", False, False, True, "pdf_report", "CMP_PDF_002", "2026-06-19"),
]

def _build_index():
    """从 tuple 规格构建 ChromaDB 索引。"""
    documents = [
        Document(text=t, metadata={
            "tenant": tn, "access_level": al,
            "role_intern": ri, "role_engineer": re, "role_manager": rm,
            "source_type": st, "doc_id": did, "timestamp": ts,
        })
        for t, tn, al, ri, re, rm, st, did, ts in _DOCS
    ]
    chroma_client = chromadb.EphemeralClient()
    try:
        chroma_client.delete_collection("smart_report_query")
    except ValueError:
        pass
    collection = chroma_client.get_or_create_collection("smart_report_query")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex.from_documents(documents, storage_context=storage_context), collection

# ═══════════════ ACL Query Engine ═══════════════

def acl_query(collection, query_text, user_id, top_k=5):
    """权限感知查询：session → where clause → ChromaDB 检索 → LLM 生成 → 引用。
    返回 {answer, citations, retrieved_count, filtered_by}"""
    session = resolve_session(user_id)
    where_clause = build_acl_where(session["tenant"], session["role"])

    query_embedding = Settings.embed_model.get_query_embedding(query_text)
    # 直接调 ChromaDB collection.query() 而非 LlamaIndex 抽象层，
    # 原因：需要 ChromaDB where clause 做布尔字段过滤（$and + role_XXX），
    # LlamaIndex MetadataFilters 对 $and + 布尔值组合存在兼容性问题。
    results = collection.query(
        query_embeddings=[query_embedding], n_results=top_k,
        where=where_clause, include=["documents", "metadatas", "distances"],
    )
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        return {"answer": "No documents found in your access scope.",
                "citations": [], "retrieved_count": 0,
                "filtered_by": f"tenant={session['tenant']}, role={session['role']}"}

    # 构建 context + citations
    context_parts, citations = [], []
    for i, (doc, meta) in enumerate(zip(docs, metas), 1):
        label = f"[{meta.get('source_type')}:{meta.get('doc_id')}]"
        context_parts.append(f"{label} {doc}")
        citations.append({"index": i, "source_type": meta.get("source_type"),
                          "doc_id": meta.get("doc_id"), "tenant": meta.get("tenant"),
                          "access_level": meta.get("access_level")})

    prompt = (
        "You are a financial assistant. Answer using ONLY the context below. "
        "Cite source labels like [pdf_report:RES_PDF_001]. Use specific data points.\n\n"
        f"Context:\n{chr(10).join(context_parts)}\n\n"
        f"Query: {query_text}"
    )
    try:
        answer = str(Settings.llm.complete(prompt))
    except Exception as e:
        import logging
        logging.error(f"LLM generation failed: {e}")
        answer = "(抱歉，系统暂时无法处理您的请求，请稍后重试。)"

    return {"answer": answer, "citations": citations,
            "retrieved_count": len(docs),
            "filtered_by": f"tenant={session['tenant']}, role={session['role']}"}

# ═══════════════ Demo: 6 个权限场景 ═══════════════

if __name__ == "__main__":
    index, collection = _build_index()

    scenarios = [
        ("alice", "What is the Q3 revenue and current PE ratio?"),
        ("bob",   "What are the internal credit risk assessments?"),
        ("carol", "What are the internal credit risk assessments?"),
        ("dave",  "What trading positions and signals do we have?"),
        ("eve",   "What trading positions and signals do we have?"),
        ("frank", "What internal investigation findings exist?"),
    ]

    print("=" * 70)
    print("Smart Report Agent — 权限感知查询演示")
    print("=" * 70)

    for user_id, query in scenarios:
        session = resolve_session(user_id)
        result = acl_query(collection, query, user_id, top_k=4)
        print(f"\n{'─'*70}")
        print(f"User: {user_id} | Tenant: {session['tenant']} | Role: {session['role']}")
        print(f"Query: {query}")
        print(f"Filter: {result['filtered_by']} | Retrieved: {result['retrieved_count']} docs")
        if result["citations"]:
            for c in result["citations"]:
                flag = " [LOCKED]" if c["access_level"] == "confidential" else ""
                print(f"  [{c['index']}] {c['source_type']}:{c['doc_id']} "
                      f"(tenant={c['tenant']}, {c['access_level']}){flag}")
        else:
            print("  (no documents — access denied)")
        print(f"Answer: {result['answer'][:200]}...")

    print(f"\n{'='*70}\n架构总结\n{'='*70}")
    print("""
  流程: User Query → Session Resolver → ACL Where Builder → ChromaDB → LLM → Citation
  关键: 权限在检索层(防泄露+省token) | 租户隔离 | 角色ACL | 可审计引用(sourcetype:docid)
""")
