"""NDCG & MRR 排序质量评估 — 与 RAGAS 生成评估互补

依赖: 同 ragas_evaluation.py

评估维度:
    MRR  (Mean Reciprocal Rank)    — 第一个相关文档排在第几位？简单直观
    NDCG (Normalized Discounted Cumulative Gain) — 考虑排序位置 + 相关度分级的综合排序质量

与 RAGAS 的关系:
    RAGAS Context Precision 测检索排序 → 用 LLM 判断相关，黑盒
    NDCG/MRR 测检索排序 → 用人工标注的 qrels（relevance judgments），白盒可解释
    两者从不同角度验证同一件事 → 面试能讲的交叉验证
"""

import os
import sys
import math
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
import numpy as np

# ═══════════════════════════════════════════════════════════════
# Setup (复用 ragas_evaluation.py 配置)
# ═══════════════════════════════════════════════════════════════

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

documents = [
    Document(text="Spring Boot auto-configuration automatically configures beans based on classpath dependencies. The @SpringBootApplication annotation combines @Configuration, @EnableAutoConfiguration, and @ComponentScan. The engine reads META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports to discover configuration classes marked with @AutoConfiguration. Conditional annotations like @ConditionalOnClass, @ConditionalOnMissingBean, and @ConditionalOnProperty control whether a configuration is activated. For example, DataSourceAutoConfiguration only triggers when spring-jdbc is on the classpath and no DataSource bean is already defined. This convention-over-configuration design eliminates boilerplate XML wiring.", metadata={"doc_id": "D1-SpringBoot"}),
    Document(text="Java Virtual Threads (JEP 444, finalized in JDK 21) are lightweight threads managed by the JVM rather than the OS kernel. Unlike platform threads that map 1:1 to OS threads, virtual threads are multiplexed onto a small pool of carrier threads. When a virtual thread blocks on I/O, the JVM unmounts it from the carrier and mounts another ready virtual thread. This enables a single JVM process to handle millions of concurrent connections. Virtual threads shine in I/O-bound workloads (microservice endpoints, database calls, HTTP clients) where threads spend most of their time waiting. CPU-bound tasks still benefit from platform threads. The API is transparent: Thread.ofVirtual().start(task) or Executors.newVirtualThreadPerTaskExecutor().", metadata={"doc_id": "D2-VirtualThreads"}),
    Document(text="HikariCP is a high-performance JDBC connection pool and the default in Spring Boot 2.x/3.x. Key optimizations: ConcurrentBag for lock-free connection borrowing, FastList to avoid ArrayList range-checking overhead in statement caching, and custom bytecode-level proxy generation instead of reflection. The pool sizing formula is: pool_size = Tn * (Cm - 1) + 1, where Tn = max thread count and Cm = max simultaneous connections per thread. For a typical microservice with 20 threads, Cm=2, that yields 21 connections. Important tuning knobs: maximumPoolSize, minimumIdle, connectionTimeout (default 30s), idleTimeout (10min), and maxLifetime (30min). Set leakDetectionThreshold during development to catch connection leaks early.", metadata={"doc_id": "D3-HikariCP"}),
    Document(text="The Model Context Protocol (MCP) is an open standard by Anthropic for connecting AI applications to external tools and data. Architecture: MCP Host (e.g., Claude Desktop) → MCP Client → MCP Server. Servers expose three primitives: Resources (file-like data, e.g., database records), Tools (executable functions the model can invoke), and Prompts (reusable interaction templates). Communication uses JSON-RPC 2.0 over stdio or HTTP+SSE transport. This design is analogous to Java's SPI (Service Provider Interface): a standard contract allows third-party tools to be plugged in and discovered at runtime without code changes. For example, a PostgreSQL MCP server lets any MCP-compatible AI app execute SQL queries by simply adding the server endpoint.", metadata={"doc_id": "D4-MCP"}),
    Document(text="LangGraph is a framework for building stateful, multi-actor agent applications. It models workflows as directed graphs: nodes are computation steps (LLM calls, tool executions, conditional logic), edges define control flow. The core abstraction is StateGraph with a typed state schema (Pydantic model or TypedDict). Key features: Checkpointing persists state after each super-step, enabling human-in-the-loop workflows, time-travel debugging, and fault recovery. Subgraphs support modular agent composition. LangGraph is analogous to Java workflow engines like Flowable or Camunda—both orchestrate processes as stateful directed graphs. LangGraph's streaming modes (values, updates, debug) enable real-time UI updates during multi-step agent reasoning.", metadata={"doc_id": "D5-LangGraph"}),
    Document(text="RAG (Retrieval-Augmented Generation) grounds LLM responses in external knowledge. Pipeline: (1) Chunk documents into segments; (2) Embed chunks into vectors using models like all-MiniLM-L6-v2 (384-dim); (3) Store vectors in a database like ChromaDB; (4) At query time, embed the user question and retrieve top-k similar chunks via cosine similarity; (5) Inject retrieved chunks as context into the LLM prompt; (6) The LLM generates an answer grounded in that context. Advanced techniques: hybrid search combines vector similarity with BM25 keyword matching; reranking models like Cohere Rerank reorder retrieved chunks for relevance; metadata filtering narrows retrieval by date, source, or category. Chunk size is a critical hyperparameter: too small loses context, too large dilutes relevance.", metadata={"doc_id": "D6-RAG"}),
]

# ── Build index ──
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("ndcg_eval")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

query_engine = index.as_query_engine(similarity_top_k=3)

# ═══════════════════════════════════════════════════════════════
# Qrels: 人工标注的相关度判断 (graded relevance 0-3)
#
#  0 = 不相关    1 = 边缘相关    2 = 相关    3 = 高度相关(精确命中)
#
# Q1 跨文档综合题 — HikariCP 公式 + Virtual Threads 并发行为都需要
# Q2-Q5 单文档题 — 各自只有一个高度相关文档
# ═══════════════════════════════════════════════════════════════

qrels = {
    #                      D1-SB  D2-VT  D3-HCP D4-MCP D5-LG  D6-RAG
    "Q1-HikariCP+VT":    [0,     2,     3,     0,     0,     0    ],
    "Q2-HikariCP-only":  [0,     0,     3,     0,     0,     0    ],
    "Q3-MCP":            [0,     0,     0,     3,     0,     0    ],
    "Q4-LangGraph":      [0,     0,     0,     0,     3,     0    ],
    "Q5-RAG":            [0,     0,     0,     0,     0,     3    ],
}

doc_ids = ["D1-SpringBoot", "D2-VirtualThreads", "D3-HikariCP",
           "D4-MCP", "D5-LangGraph", "D6-RAG"]

queries = {
    "Q1-HikariCP+VT":   "How should I configure HikariCP pool size when using Java virtual threads in a Spring Boot microservice, and why?",
    "Q2-HikariCP-only": "What is the HikariCP pool sizing formula and what do the variables represent?",
    "Q3-MCP":           "How does the MCP protocol architecture work, and what Java concept is it analogous to?",
    "Q4-LangGraph":     "What are the key features of LangGraph and what Java technology is it compared to?",
    "Q5-RAG":           "Describe the complete RAG pipeline and what advanced techniques can improve retrieval quality.",
}

# ═══════════════════════════════════════════════════════════════
# Metrics Implementation
# ═══════════════════════════════════════════════════════════════

def dcg_at_k(relevances, k):
    """Discounted Cumulative Gain: 位置越靠后，权重衰减越大。"""
    relevances = relevances[:k]
    # DCG = sum(rel_i / log2(i+1)) for i in 1..k (1-indexed)
    discounts = [1.0 / math.log2(i + 2) for i in range(len(relevances))]
    # 使用指数变体 (2^rel - 1)，这是 TREC 等 IR 评测的标准做法，
    # 能够对高度相关文档给予指数级加权，而非线性加权
    return sum(((2**r - 1) * d) for r, d in zip(relevances, discounts))

def ndcg_at_k(predicted, ideal, k):
    """Normalized DCG: 实际 DCG / 理想 DCG。值域 [0, 1]，1 = 完美排序。"""
    dcg = dcg_at_k(predicted, k)
    idcg = dcg_at_k(sorted(ideal, reverse=True), k)
    return dcg / idcg if idcg > 0 else 0.0

def mrr(predicted_relevances):
    """Mean Reciprocal Rank: 第一个相关文档排在第几位？1/rank。

    rel > 0 包含了边缘相关（relevance >= 1 即视为命中），不要求高度相关(3)。
    这符合 MRR 的经典定义：只要文档对 query 有一定相关性，就算作命中。
    """
    for i, rel in enumerate(predicted_relevances, 1):
        if rel > 0:
            return 1.0 / i
    return 0.0

# ═══════════════════════════════════════════════════════════════
# Run retrieval + compute metrics
# ═══════════════════════════════════════════════════════════════

print("=" * 70)
print("NDCG & MRR 排序质量评估")
print("=" * 70)

print(f"\n{'Query':<22} {'Retrieved (top-3)':<55} {'NDCG@3':>7} {'MRR':>7}")
print("-" * 95)

ndcg_scores, mrr_scores = [], []

for qid, query_text in queries.items():
    response = query_engine.query(query_text)
    # 从 node.metadata 读取 doc_id，而非文本前缀匹配
    retrieved_ids = []
    for node in response.source_nodes:
        doc_id = node.metadata.get("doc_id")
        if doc_id is None:
            raise ValueError(
                f"无法匹配文档: node.metadata 中未找到 doc_id，"
                f"node.text 前60字符: {node.text[:60]!r}"
            )
        retrieved_ids.append(doc_id)

    # Build predicted relevance list from retrieved order
    ideal = qrels[qid]
    predicted = []
    for rid in retrieved_ids:
        if rid in doc_ids:
            predicted.append(ideal[doc_ids.index(rid)])

    # Pad with 0s for any missing docs (shouldn't happen with top_k=3 from 6 docs)
    while len(predicted) < 3:
        predicted.append(0)

    n = ndcg_at_k(predicted, ideal, k=3)
    m = mrr(predicted)

    ndcg_scores.append(n)
    mrr_scores.append(m)

    retrieved_str = " → ".join(retrieved_ids)
    print(f"{qid:<22} {retrieved_str:<55} {n:>7.4f} {m:>7.4f}")

# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════

print(f"\n{'=' * 70}")
print("Summary")
print("=" * 70)

avg_ndcg = np.mean(ndcg_scores)
avg_mrr = np.mean(mrr_scores)

print(f"  Avg NDCG@3:  {avg_ndcg:.4f}")
print(f"  Avg MRR:     {avg_mrr:.4f}")

# ═══════════════════════════════════════════════════════════════
# Cross-validation with RAGAS
# ═══════════════════════════════════════════════════════════════

print(f"\n{'=' * 70}")
print("Cross-Validation: NDCG/MRR vs RAGAS Context Precision")
print("=" * 70)

print("""
  维度           │ 测量方式              │ 优势
  ───────────────┼───────────────────────┼─────────────────
  NDCG/MRR       │ 人工 qrels + 数学公式  │ 白盒、可复现、不花钱
  Context Precis │ LLM 逐条判断相关度     │ 无需人工标注、可规模化

  面试要点: 两者从不同角度验证同一件事。NDCG=1.0 的 query，
  RAGAS Context Precision 也应该接近 1.0。如果偏差大，说明
  要么 qrels 标错了，要么 LLM 评估器自己判断有问题。
  → 这就是「评估体系的交叉验证」。
""")

# ═══════════════════════════════════════════════════════════════
# Limitation: 小数据集指标失真
# ═══════════════════════════════════════════════════════════════

print("=" * 70)
print("Dataset Size Trap: 为什么小数据集所有指标都满分")
print("=" * 70)

print(f"""
  当前: 6 docs, top_k=3, 5 queries
  → 每次检索返回 50% 的语料库
  → 高度相关文档几乎必然在前 3
  → NDCG@3 = MRR = 1.0, 无法区分检索器好坏

  真实场景: 10万+ chunks, top_k=5-20
  → 检索返回语料库的 0.005%-0.02%
  → 排序质量直接决定答案质量
  → Context Precision 从 0.0 到 1.0 才有区分度

  面试: "我们的 RAG 评估分两个粒度 — 离线用 NDCG@20 测排序，
  在线用 RAGAS Faithfulness 测生成。小数据集先跑通流程，
  生产环境换成 Langfuse 全量追踪。"
  → 既承认 demo 局限，又体现工程思维。
""")

# ═══════════════════════════════════════════════════════════════
# Q1 deep-dive: 为什么 NDCG 比 MRR 更细粒度
# ═══════════════════════════════════════════════════════════════

print("=" * 70)
print("Q1 Deep-Dive: NDCG vs MRR 的区分力")
print("=" * 70)

# 两个假想排序，MRR 相同但 NDCG 不同
scenario_a = [3, 0, 2]  # 高度相关排第一，相关排第三
scenario_b = [2, 3, 0]  # 相关排第一，高度相关排第二

print(f"""
  Scenario A: retrieved = [HikariCP(3), SpringBoot(0), VirtualThreads(2)]
    NDCG@3 = {ndcg_at_k(scenario_a, sorted(scenario_a, reverse=True), 3):.4f}
    MRR    = {mrr(scenario_a):.4f}

  Scenario B: retrieved = [VirtualThreads(2), HikariCP(3), SpringBoot(0)]
    NDCG@3 = {ndcg_at_k(scenario_b, sorted(scenario_b, reverse=True), 3):.4f}
    MRR    = {mrr(scenario_b):.4f}

  MRR 只看「第一个相关在哪」，Scenario A/B 都排第1 → MRR 一样。
  NDCG 区分了高度相关(3)和边缘相关(2)的位置 → 能区分两个排序。
  → 面试: "MRR 够用但粗粒度，NDCG 适合有多级相关度的场景（电商/搜索）。"
""")
