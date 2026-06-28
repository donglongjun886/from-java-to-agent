"""异构数据摄入管道 — 模拟企业研报系统三种数据源

数据源: PDF 研报(Document模拟) / 数据库记录(dict模拟SQL) / API JSON(dict模拟REST)
12 篇: research(3pub+1conf) trading(2pub+2conf) compliance(3pub+1conf)
所有 metadata 用标量类型(str/bool), ChromaDB 兼容
"""

import os
import sys
from unittest.mock import MagicMock
from collections import Counter

# 已知 workaround: langchain_community.vertexai 在非 GCP 环境导入会报错，
# 提前 mock 避免 LlamaIndex 导入链触发异常，不影响功能。
sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()
sys.modules["langchain_community.chat_models.vertexai"].ChatVertexAI = MagicMock()

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from dataclasses import dataclass

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

# ═══════════════ Document Specs（12 篇，9 字段命名元组定义） ═══════════════

@dataclass
class DocDef:
    """文档定义 — 替代裸元组，字段名自解释。"""
    text: str
    tenant: str
    access_level: str
    role_intern: bool
    role_engineer: bool
    role_manager: bool
    source_type: str
    doc_id: str
    timestamp: str

_DOCS = [
    # ── research: 3 public + 1 confidential ──
    DocDef("Q3 2026 Financial Report: Revenue 38.2B CNY (+18% YoY), net profit 5.8B. Growth driven by cloud computing (+35%) and AI (+62%). Gross margin 48.2%, up from 45.1%. Q4 guidance 40-42B, full-year target 150B. Operating expenses +12% due to AI chip R&D expansion.",
     "research", "public", True, True, True, "pdf_report", "RES_PDF_001", "2026-06-20T09:00:00"),

    DocDef("Semiconductor Industry Trend H1 2026: AI chip demand surged 45% YoY driven by LLM training infrastructure. Domestic substitution rate for 14nm+ processes reached 65% (48% in 2025). Key players: SMIC (28nm capacity +30%), Hua Hong (IGBT), YMTC (232-layer NAND). Risk: US EUV export controls, wafer price +8%. Overweight semiconductor equipment sector.",
     "research", "public", True, True, True, "pdf_report", "RES_PDF_002", "2026-06-18T14:00:00"),

    DocDef("Company Fundamentals (2026-06-25): Market Cap 520B CNY, PE(TTM) 35.2, PB 4.8, PS 6.1. Revenue TTM 142B, Net Income 18.5B. ROE 18.5%, ROA 8.2%. D/E 0.45, Current Ratio 1.8, FCF 22B. Revenue CAGR(3yr) 22%, EPS CAGR 19%. Dividend yield 0.8%. Institutional ownership 62%.",
     "research", "public", True, True, True, "db_record", "RES_DB_001", "2026-06-25T16:30:00"),

    DocDef("CONFIDENTIAL — Credit Risk Assessment Q2 2026: Three corporate clients downgraded to Watch, total exposure 2.4B CNY. Real estate sector exposure reduced from 15% to 8%. Counterparty risk for OTC derivatives with EU banks elevated due to Basel IV uncertainty. Provision coverage increase from 2.1% to 2.8% by Q4 2026.",
     "research", "confidential", False, True, True, "pdf_report", "RES_PDF_003", "2026-06-22T11:00:00"),

    # ── trading: 2 public + 2 confidential (1 manager-only) ──
    DocDef("H2 2026 Market Outlook: A-share SSE Composite 3200-3600 range, CSI 300 target 4200-4500. Overweight financials (banks+insurers), underweight real estate. Catalysts: PBOC RRR cut (expected Q3), SOE reform acceleration, northbound capital recovery. Risk: US election tariff policy shift.",
     "trading", "public", True, True, True, "pdf_report", "TRD_PDF_001", "2026-06-24T10:00:00"),

    DocDef("Real-time Market Data (2026-06-25 15:00 CST): CSI 300 3958.2 (+1.2%), SSE Composite 3356.7 (+0.8%), SZSE Component 10820.5 (+1.5%), ChiNext 2150.3 (+1.8%), HSI 19820.5 (-0.3%), HSCEI 7120.3 (+0.2%). FX: USD/CNY 7.12, EUR/CNY 7.78. Commodities: Gold 2350 USD/oz, Brent 82.5 USD/bbl.",
     "trading", "public", True, True, True, "api_json", "TRD_API_001", "2026-06-25T15:00:00"),

    DocDef("CONFIDENTIAL — Position Summary (2026-06-25): Total AUM 8.5B CNY. Allocation: Tech 35%, Financials 25%, Consumer 18%, Healthcare 12%, Energy 10%. Top 3: CITIC Securities 1.2B (cost 22.5), Moutai 0.95B (cost 1680), CATL 0.82B (cost 195). Unrealized P&L +380M YTD. Leverage 1.15x (limit 1.5x).",
     "trading", "confidential", False, True, True, "db_record", "TRD_DB_001", "2026-06-25T18:00:00"),

    DocDef("CONFIDENTIAL — Quantitative Trading Signal (2026-06-25 14:30): BUY 600036 CMB. Multi-factor confidence 0.87. Technical: MACD golden cross, RSI(14)=42 (oversold bounce), volume 1.8x avg. Target 45.2 (+15% from 39.3), stop 36.5 (-7%). Signal expires 48h. Position sizing: 2% of AUM.",
     "trading", "confidential", False, False, True, "api_json", "TRD_API_002", "2026-06-25T14:30:00"),

    # ── compliance: 3 public + 1 confidential (manager-only) ──
    DocDef("CSRC Regulation 2026-47: Pre-trade risk controls mandatory for all algorithmic trading by Jan 2027. Requirements: real-time order validation (price/volume limits), kill-switch within 50ms, full audit trail logging per order. Penalty: up to 5M CNY + trading suspension. Impact: ~20% existing algo strategies need modification, compliance cost +3-5M per desk.",
     "compliance", "public", True, True, True, "pdf_report", "CMP_PDF_001", "2026-06-21T09:30:00"),

    DocDef("Audit Trail Summary Q2 2026: 12,847 trades reviewed. 3 flagged: Desk B 2026-04-15 (suspected wash trading, 85M CNY), Desk A 2026-05-02 (cross-exchange manipulation, 120M CNY), Desk C 2026-05-20 (unauthorized algo parameter change). Compliance score 94.2/100 (below 95 target).",
     "compliance", "public", True, True, True, "db_record", "CMP_DB_001", "2026-06-23T14:00:00"),

    DocDef("OFAC SDN List Update (2026-06-24): 6 entities added, 2 applicable to APAC network. Entity A: Shanghai shipping co. (DPRK sanctions evasion). Entity B: HK trading firm (Iran oil). Required: freeze assets, block transactions, file SAR 30 days. Existing exposure: zero.",
     "compliance", "public", True, True, True, "api_json", "CMP_API_001", "2026-06-25T08:00:00"),

    DocDef("CONFIDENTIAL — Internal Investigation Case 2026-07: Trader at Desk B (ID TRD-3421) executed unauthorized cross-border transfer 5M USD to Cayman Islands entity on 2026-05-28, bypassing internal approval. Root cause: dual-control disabled during system upgrade. Recommend: immediate termination, mandatory 4-eyes for transfers >1M, revoke Desk B supervisor license.",
     "compliance", "confidential", False, False, True, "pdf_report", "CMP_PDF_002", "2026-06-19T16:00:00"),
]

# ═══════════════ Build Index ═══════════════

all_docs = [
    Document(text=d.text, metadata={
        "tenant": d.tenant, "access_level": d.access_level,
        "role_intern": d.role_intern, "role_engineer": d.role_engineer, "role_manager": d.role_manager,
        "source_type": d.source_type, "doc_id": d.doc_id, "timestamp": d.timestamp,
    })
    for d in _DOCS
]

chroma_client = chromadb.EphemeralClient()
try: chroma_client.delete_collection("smart_report")
except ValueError: pass
collection = chroma_client.get_or_create_collection("smart_report")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(all_docs, storage_context=storage_context)

# ═══════════════ Ingestion Report ═══════════════

print("=" * 70)
print("Smart Report Agent — 异构数据摄入报告")
print("=" * 70)
print(f"\nTotal documents indexed: {len(all_docs)}")
print(f"  Research (研报组):   4 docs (3 public + 1 confidential, eng/mgr)")
print(f"  Trading (交易组):    4 docs (2 pub + 2 conf, 1 mgr-only)")
print(f"  Compliance (合规组):  4 docs (3 pub + 1 conf, mgr-only)")

# 统计
tn_ct = Counter(d.metadata["tenant"] for d in all_docs)
src_ct = Counter(d.metadata["source_type"] for d in all_docs)
lvl_ct = Counter(d.metadata["access_level"] for d in all_docs)
print(f"\nBy tenant:  research={tn_ct['research']}, trading={tn_ct['trading']}, compliance={tn_ct['compliance']}")
print(f"By source:  pdf_report={src_ct['pdf_report']}, db_record={src_ct['db_record']}, api_json={src_ct['api_json']}")
print(f"By level:   public={lvl_ct['public']}, confidential={lvl_ct['confidential']}")
print(f"\nCollection: smart_report (in-memory)")
print(f"Embedding: 384-dim (all-MiniLM-L6-v2)")
print(f"LLM: deepseek-chat (OpenAILike)")
print(f"Metadata: tenant, access_level, role_intern/engineer/manager, source_type, doc_id, timestamp")
print(f"All metadata values are scalar types (str/bool) — ChromaDB compatible.")
