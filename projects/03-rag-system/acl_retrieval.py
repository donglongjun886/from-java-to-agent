"""ACL 权限感知检索 — 企业 RAG vs Demo RAG 的核心差异

为什么权限必须在检索层做而不是生成层？
  1. 安全: 检索出来的敏感文档在 prompt 里已经泄露给 LLM
  2. 成本: 无权访问的文档占用 context window → 浪费 token
  3. 合规: 多租户 SaaS 下租户间数据隔离是基本要求

面试一句话:
  "我们参考了 Zoom 的多租户 RAG 架构，用 tenant_id metadata 在 ChromaDB
   查询时做预过滤，保证每个租户只检索自己的文档。权限模型是 document-level
   的 access_level + allowed_roles，在 query 阶段就生效，不等 LLM 生成后校验。"
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()
sys.modules["langchain_community.chat_models.vertexai"].ChatVertexAI = MagicMock()

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY not configured")

Settings.llm = OpenAILike(
    model="deepseek-chat", api_key=api_key, api_base="https://api.deepseek.com",
    temperature=0.1, is_chat_model=True, max_retries=3,
)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
)

# ═══════════════════════════════════════════════════════════════
# 8 篇文档: 2 租户 × 2 级别 × 2 角色
# metadata 字段: tenant, access_level, allowed_roles
# ═══════════════════════════════════════════════════════════════

documents = [
    # ── ACME (3 public + 2 confidential) ──
    Document(text="ACME Q3 revenue increased 18% driven by the new cloud platform launch in APAC markets.", metadata={
        "tenant": "acme", "access_level": "public", "role_intern": True, "role_engineer": True, "role_manager": True}),
    Document(text="ACME microservices architecture uses Kubernetes with Istio service mesh for east-west traffic.", metadata={
        "tenant": "acme", "access_level": "public", "role_intern": True, "role_engineer": True, "role_manager": True}),
    Document(text="ACME product roadmap includes AI-powered analytics dashboard, targeting Q4 2026 release.", metadata={
        "tenant": "acme", "access_level": "public", "role_intern": True, "role_engineer": True, "role_manager": True}),
    Document(text="ACME confidential: server cost optimization plan targets 30% reduction via spot instances.", metadata={
        "tenant": "acme", "access_level": "confidential", "role_intern": False, "role_engineer": True, "role_manager": True}),
    Document(text="ACME confidential: pending acquisition of DataFlow Inc for $120M, closing Q1 2027.", metadata={
        "tenant": "acme", "access_level": "confidential", "role_intern": False, "role_engineer": False, "role_manager": True}),

    # ── GLOBEX (2 public + 1 confidential) ──
    Document(text="GLOBEX expansion plan targets European market entry with Berlin office in Q2 2026.", metadata={
        "tenant": "globex", "access_level": "public", "role_intern": True, "role_engineer": True, "role_manager": True}),
    Document(text="GLOBEX partner ecosystem now includes 200+ certified integration partners worldwide.", metadata={
        "tenant": "globex", "access_level": "public", "role_intern": True, "role_engineer": True, "role_manager": True}),
    Document(text="GLOBEX confidential: restructuring plan reduces headcount by 15% in legacy division.", metadata={
        "tenant": "globex", "access_level": "confidential", "role_intern": False, "role_engineer": False, "role_manager": True}),
]

# ── Build index ──
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("acl_demo")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)


def retrieve(query_text, tenant=None, role=None, access_level=None, top_k=5):
    """权限感知检索: tenant 精确匹配 + role 布尔过滤 + access_level 过滤。

    注意: 这里直接调用 ChromaDB collection.query() 而非 LlamaIndex 的
    as_retriever + MetadataFilters，原因是 ChromaDB where clause 对布尔字段
    (role_intern/role_engineer/role_manager) 的过滤支持更为直接。
    LlamaIndex MetadataFilters 在处理 $and + 布尔值组合时存在兼容性问题，
    因此采用绕过 LlamaIndex 抽象层、直接操作 ChromaDB 的方式。
    如果未来仅需过滤 tenant 等字符串字段，可改用 as_retriever 方案。
    """
    query_embedding = Settings.embed_model.get_query_embedding(query_text)

    where_clause = {}
    conditions = []
    if tenant:
        conditions.append({"tenant": tenant})
    if role:
        conditions.append({f"role_{role}": True})  # {"role_intern": True}
    if access_level:
        conditions.append({"access_level": access_level})

    if len(conditions) == 1:
        where_clause = conditions[0]
    elif len(conditions) > 1:
        where_clause = {"$and": conditions}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause if where_clause else None,
        include=["documents", "metadatas", "distances"],
    )
    return results


def print_results(scenario, query_text, filters_desc, results, is_filtered=False):
    """格式化打印检索结果。

    is_filtered: 是否启用了权限过滤。False 表示无过滤（场景1），
                 此时出现的 confidential 文档标记为跨租户泄露。
    """
    print(f"\n{'=' * 70}")
    print(f"场景: {scenario}")
    print(f"{'=' * 70}")
    print(f"Query: \"{query_text}\"")
    print(f"Filters: {filters_desc}")

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not docs:
        print("  (no documents retrieved)")
        return

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
        tenant = meta.get("tenant", "?")
        level = meta.get("access_level", "?")
        # 重建角色字符串: role_intern/role_engineer/role_manager → "intern,engineer"
        role_names = []
        if meta.get("role_intern"): role_names.append("intern")
        if meta.get("role_engineer"): role_names.append("engineer")
        if meta.get("role_manager"): role_names.append("manager")
        roles = ",".join(role_names)
        snippet = doc[:80].replace("\n", " ")
        flag = ""
        if level == "confidential" and not is_filtered:
            flag = " ← 跨租户泄露!"
        elif level == "confidential":
            flag = " ← confidential"
        print(f"  {i}. [{tenant.upper()}] {snippet}... (access_level={level}, roles={roles}){flag}")


# ═══════════════════════════════════════════════════════════════
# 四个场景
# ═══════════════════════════════════════════════════════════════

query = "revenue growth strategy expansion plan"

# 场景1: 无过滤 — 所有文档都可被检索到
r1 = retrieve(query)
print_results("无权限过滤（不安全）", query, "none", r1, is_filtered=False)

# 场景2: 租户隔离 — 只返回 tenant=acme
r2 = retrieve(query, tenant="acme")
print_results("租户隔离（tenant=acme）", query, "tenant=acme", r2, is_filtered=True)

# 场景3: 角色级 ACL — tenant=acme, role=intern
r3 = retrieve(query, tenant="acme", role="intern")
print_results("角色级 ACL（tenant=acme, role=intern）", query, "tenant=acme, role=intern", r3, is_filtered=True)

# 场景3b: 访问级别过滤 — tenant=acme, access_level=public（过滤掉 confidential 文档）
r3b = retrieve(query, tenant="acme", access_level="public")
print_results("访问级别过滤（tenant=acme, access_level=public）", query, "tenant=acme, access_level=public", r3b, is_filtered=True)



# ═══════════════════════════════════════════════════════════════
# 架构总结
# ═══════════════════════════════════════════════════════════════

print(f"\n{'=' * 70}")
print("架构总结")
print("=" * 70)
print("""
  检索流程:
    User Query → Tenant Resolver → Metadata Filter → Vector Search → Top-K Results

  关键设计决策:
    1. Tenant ID 在索引时写入 document metadata
    2. 查询前从 JWT/session 解析 tenant + role
    3. ChromaDB where clause 在向量搜索前做预过滤
    4. 权限校验不依赖 LLM — 即使 LLM 被 prompt 注入也不会泄露跨租户数据

  面试模板:
    "企业 RAG 和 Demo RAG 的核心差异在三点: 异构数据摄入、权限隔离、可审计的引用链路。
     权限隔离不能等 LLM 生成后校验 — 检索阶段的 metadata 预过滤既保安全又省 token。"
""")
