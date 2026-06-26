"""RAGAS Evaluation — 对 first_rag.py 的 RAG Pipeline 做生成质量评估

依赖:
    pip install ragas datasets

评估维度:
    Faithfulness      — 回答是否忠实于检索上下文（不编造）
    Answer Relevancy  — 回答是否紧扣问题（不跑题）
    Context Recall    — 检索上下文是否覆盖参考答案的关键信息
    Context Precision — 检索上下文中相关文档是否排在前面
"""

import os, sys, math
from pathlib import Path
from unittest.mock import MagicMock

# WORKAROUND: ragas 0.4.x imports langchain_community.chat_models.vertexai
# which is removed in langchain-community 0.4+. The stub is harmless since
# we only use DeepSeek (not VertexAI). If upgrading ragas, check release notes.
sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()
sys.modules["langchain_community.chat_models.vertexai"].ChatVertexAI = MagicMock()

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document, PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from langchain_huggingface import HuggingFaceEmbeddings as LCHFEmbeddings

# ═══════════════════════════════════════════════════════════════
# Setup: LLM + Embedding + Index (复用 first_rag.py 的配置)
# ═══════════════════════════════════════════════════════════════

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY not configured")

# LlamaIndex settings
Settings.llm = OpenAILike(
    model="deepseek-chat",
    api_key=api_key,
    api_base="https://api.deepseek.com",
    temperature=0.1,
    is_chat_model=True,
    max_retries=3,
)

Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
)

# RAGAS evaluator LLM (使用 llm_factory 注册自定义 LLM)
from openai import OpenAI as OpenAIClient
from ragas.llms import llm_factory
eval_llm = llm_factory(
    "deepseek-chat",
    client=OpenAIClient(api_key=api_key, base_url="https://api.deepseek.com", max_retries=3),
)
lc_embeddings = LCHFEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ── Documents (同 first_rag.py) ──
documents = [
    Document(text=(
        "Spring Boot auto-configuration automatically configures beans based on "
        "classpath dependencies. The @SpringBootApplication annotation combines "
        "@Configuration, @EnableAutoConfiguration, and @ComponentScan. The engine "
        "reads META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports "
        "to discover configuration classes marked with @AutoConfiguration. Conditional "
        "annotations like @ConditionalOnClass, @ConditionalOnMissingBean, and "
        "@ConditionalOnProperty control whether a configuration is activated. "
        "For example, DataSourceAutoConfiguration only triggers when spring-jdbc "
        "is on the classpath and no DataSource bean is already defined. This "
        "convention-over-configuration design eliminates boilerplate XML wiring."
    )),
    Document(text=(
        "Java Virtual Threads (JEP 444, finalized in JDK 21) are lightweight threads "
        "managed by the JVM rather than the OS kernel. Unlike platform threads that "
        "map 1:1 to OS threads, virtual threads are multiplexed onto a small pool of "
        "carrier threads. When a virtual thread blocks on I/O, the JVM unmounts it "
        "from the carrier and mounts another ready virtual thread. This enables a "
        "single JVM process to handle millions of concurrent connections. Virtual "
        "threads shine in I/O-bound workloads (microservice endpoints, database calls, "
        "HTTP clients) where threads spend most of their time waiting. CPU-bound "
        "tasks still benefit from platform threads. The API is transparent: "
        "Thread.ofVirtual().start(task) or Executors.newVirtualThreadPerTaskExecutor()."
    )),
    Document(text=(
        "HikariCP is a high-performance JDBC connection pool and the default in "
        "Spring Boot 2.x/3.x. Key optimizations: ConcurrentBag for lock-free "
        "connection borrowing, FastList to avoid ArrayList range-checking overhead "
        "in statement caching, and custom bytecode-level proxy generation instead "
        "of reflection. The pool sizing formula is: pool_size = Tn * (Cm - 1) + 1, "
        "where Tn = max thread count and Cm = max simultaneous connections per thread. "
        "For a typical microservice with 20 threads, Cm=2, that yields 21 connections. "
        "Important tuning knobs: maximumPoolSize, minimumIdle, connectionTimeout "
        "(default 30s), idleTimeout (10min), and maxLifetime (30min). Set "
        "leakDetectionThreshold during development to catch connection leaks early."
    )),
    Document(text=(
        "The Model Context Protocol (MCP) is an open standard by Anthropic for "
        "connecting AI applications to external tools and data. Architecture: MCP "
        "Host (e.g., Claude Desktop) → MCP Client → MCP Server. Servers expose "
        "three primitives: Resources (file-like data, e.g., database records), "
        "Tools (executable functions the model can invoke), and Prompts (reusable "
        "interaction templates). Communication uses JSON-RPC 2.0 over stdio or "
        "HTTP+SSE transport. This design is analogous to Java's SPI (Service "
        "Provider Interface): a standard contract allows third-party tools to be "
        "plugged in and discovered at runtime without code changes. For example, "
        "a PostgreSQL MCP server lets any MCP-compatible AI app execute SQL "
        "queries by simply adding the server endpoint."
    )),
    Document(text=(
        "LangGraph is a framework for building stateful, multi-actor agent "
        "applications. It models workflows as directed graphs: nodes are "
        "computation steps (LLM calls, tool executions, conditional logic), "
        "edges define control flow. The core abstraction is StateGraph with a "
        "typed state schema (Pydantic model or TypedDict). Key features: "
        "Checkpointing persists state after each super-step, enabling "
        "human-in-the-loop workflows, time-travel debugging, and fault recovery. "
        "Subgraphs support modular agent composition. LangGraph is analogous to "
        "Java workflow engines like Flowable or Camunda—both orchestrate processes "
        "as stateful directed graphs. LangGraph's streaming modes (values, updates, "
        "debug) enable real-time UI updates during multi-step agent reasoning."
    )),
    Document(text=(
        "RAG (Retrieval-Augmented Generation) grounds LLM responses in external "
        "knowledge. Pipeline: (1) Chunk documents into segments; (2) Embed chunks "
        "into vectors using models like all-MiniLM-L6-v2 (384-dim); (3) Store "
        "vectors in a database like ChromaDB; (4) At query time, embed the user "
        "question and retrieve top-k similar chunks via cosine similarity; "
        "(5) Inject retrieved chunks as context into the LLM prompt; (6) The LLM "
        "generates an answer grounded in that context. Advanced techniques: hybrid "
        "search combines vector similarity with BM25 keyword matching; reranking "
        "models like Cohere Rerank reorder retrieved chunks for relevance; "
        "metadata filtering narrows retrieval by date, source, or category. "
        "Chunk size is a critical hyperparameter: too small loses context, "
        "too large dilutes relevance."
    )),
]

# ── Build index ──
# Chunking experiments (2026.06.26):
#   chunk_size=128: 6 docs → 11 nodes, Q1 Faithfulness 0.50 (↓), chunks too fragmented
#   chunk_size=256: 6 docs →  6 nodes, Q1 Faithfulness N/A  (max_tokens exceeded)
#   No chunking:    6 docs →  6 nodes, Q1 Faithfulness 0.67 (↑), best for ~140-token docs
# Conclusion: docs at ~140 tokens are already well-sized. Real fix is reranker + hybrid search.

chroma_client = chromadb.Client()  # in-memory, no disk leak
collection = chroma_client.create_collection("ragas_eval")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

qa_template = PromptTemplate(
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Given the context information and not prior knowledge, "
    "answer the query. If the context contains specific formulas, numbers, "
    "or technical details, you MUST use them in your answer.\n"
    "Query: {query_str}\n"
    "Answer: "
)

query_engine = index.as_query_engine(similarity_top_k=3, text_qa_template=qa_template)

# ═══════════════════════════════════════════════════════════════
# Evaluation Dataset: 5 组 QA pairs
# ═══════════════════════════════════════════════════════════════

eval_questions = [
    # Q1: 跨文档综合 (HikariCP formula + Virtual Threads)
    {
        "question": "How should I configure HikariCP pool size when using Java virtual threads in a Spring Boot microservice, and why?",
        "ground_truth": (
            "With virtual threads, you should increase the pool size significantly because "
            "virtual threads allow millions of concurrent connections. The standard formula "
            "pool_size = Tn * (Cm - 1) + 1 still applies, but Tn should reflect the much "
            "higher concurrency possible with virtual threads. For a microservice using "
            "virtual threads with millions of concurrent I/O operations, the pool should be "
            "sized accordingly, while monitoring maximumPoolSize, connectionTimeout (default 30s), "
            "and idleTimeout (10min). HikariCP's ConcurrentBag enables lock-free borrowing which "
            "is important under high concurrency."
        ),
    },
    # Q2: 单文档精确事实 (公式 + 参数)
    {
        "question": "What is the HikariCP pool sizing formula and what do the variables represent?",
        "ground_truth": (
            "The formula is pool_size = Tn * (Cm - 1) + 1, where Tn is the maximum thread "
            "count and Cm is the maximum simultaneous connections per thread. For a typical "
            "microservice with 20 threads and Cm=2, the result is 21 connections."
        ),
    },
    # Q3: 类比概念理解 (MCP ↔ Java SPI)
    {
        "question": "How does the MCP protocol architecture work, and what Java concept is it analogous to?",
        "ground_truth": (
            "MCP architecture follows Host → Client → Server pattern. Servers expose three "
            "primitives: Resources (file-like data), Tools (executable functions), and Prompts "
            "(reusable templates). Communication uses JSON-RPC 2.0 over stdio or HTTP+SSE. "
            "It is analogous to Java's SPI (Service Provider Interface): a standard contract "
            "allows third-party tools to be plugged in and discovered at runtime without code changes."
        ),
    },
    # Q4: LangGraph 核心特征
    {
        "question": "What are the key features of LangGraph and what Java technology is it compared to?",
        "ground_truth": (
            "LangGraph models workflows as directed graphs with nodes (LLM calls, tool executions) "
            "and edges (control flow). Core abstraction is StateGraph with typed state schema. "
            "Key features include Checkpointing (persists state after each super-step for "
            "human-in-the-loop, time-travel debugging, and fault recovery) and Subgraphs for "
            "modular composition. It streams in values/updates/debug modes for real-time UI. "
            "It is analogous to Java workflow engines like Flowable or Camunda."
        ),
    },
    # Q5: RAG pipeline 全流程
    {
        "question": "Describe the complete RAG pipeline and what advanced techniques can improve retrieval quality.",
        "ground_truth": (
            "Pipeline steps: (1) Chunk documents into segments; (2) Embed chunks into vectors "
            "using embedding models like all-MiniLM-L6-v2 (384-dim); (3) Store vectors in a "
            "database like ChromaDB; (4) At query time, embed the question and retrieve top-k "
            "similar chunks via cosine similarity; (5) Inject retrieved chunks as context into "
            "the LLM prompt; (6) LLM generates answer grounded in that context. Advanced "
            "techniques: hybrid search combines vector similarity with BM25 keyword matching; "
            "reranking models like Cohere Rerank reorder chunks; metadata filtering narrows "
            "by date/source/category. Chunk size is critical: too small loses context, too large dilutes relevance."
        ),
    },
]

# ═══════════════════════════════════════════════════════════════
# Run queries and build dataset
# ═══════════════════════════════════════════════════════════════

questions, answers, contexts_list, ground_truths = [], [], [], []

print("=" * 70)
print("Running RAG queries for evaluation dataset...")
print("=" * 70)

for i, item in enumerate(eval_questions, 1):
    try:
        response = query_engine.query(item["question"])
        contexts = [node.text for node in response.source_nodes]

        questions.append(item["question"])
        answers.append(str(response))
        contexts_list.append(contexts)
        ground_truths.append(item["ground_truth"])

        print(f"\n[Q{i}] {item['question'][:80]}...")
        print(f"    Retrieved {len(contexts)} context chunks")
        for j, ctx in enumerate(contexts, 1):
            preview = ctx[:80].replace("\n", " ")
            print(f"      Chunk {j}: {preview}...")
    except Exception as e:
        print(f"\n[Q{i}] FAILED: {e}")
        questions.append(item["question"])
        answers.append("")
        contexts_list.append([])
        ground_truths.append(item["ground_truth"])

# ═══════════════════════════════════════════════════════════════
# RAGAS Evaluation
# ═══════════════════════════════════════════════════════════════

print(f"\n{'=' * 70}")
print("RAGAS Evaluation — 4 Metrics")
print("=" * 70)

eval_dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": contexts_list,
    "ground_truth": ground_truths,
})

# Run evaluation — answer_relevancy/context_recall need embeddings which may
# not work with custom LLM setups. faithfulness is the most important metric.
result = evaluate(
    eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
    llm=eval_llm,
    embeddings=lc_embeddings,
)

def _avg(lst):
    """Average of list, filtering NaN/None."""
    vals = [v for v in lst if isinstance(v, (int, float)) and not math.isnan(v)]
    return sum(vals) / len(vals) if vals else float("nan")

print(f"\n{'Metric':<25} {'Score':>8}")
print("-" * 35)
for metric_name in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]:
    raw = result[metric_name]
    score = _avg(raw) if isinstance(raw, list) else raw
    flag = "" if isinstance(score, float) and not math.isnan(score) else " (failed)"
    print(f"{metric_name:<25} {score:>8.4f}{flag}")

# ═══════════════════════════════════════════════════════════════
# Per-question breakdown
# ═══════════════════════════════════════════════════════════════

print(f"\n{'=' * 70}")
print("Per-Question Detail")
print("=" * 70)

df = result.to_pandas()

# RAGAS uses 'user_input' not 'question' in result dataframe
q_col = "user_input" if "user_input" in df.columns else "question"

for row in df.itertuples():
    q = getattr(row, q_col, getattr(row, df.columns[0], "?") if len(df.columns) > 0 else "?")
    q_str = str(q)[:100]
    print(f"\n── Q{row.Index + 1} ──")
    print(f"Question: {q_str}...")
    for col in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]:
        if col in df.columns:
            val = getattr(row, col, None)
            if isinstance(val, (int, float)) and not math.isnan(val):
                print(f"  {col:<20} {val:>8.4f}")
            else:
                print(f"  {col:<20} {'N/A':>8}")
        else:
            print(f"  {col:<20} {'N/A':>8}")

# ═══════════════════════════════════════════════════════════════
# Diagnosis: 基于 Faithfulness 诊断（最核心指标）
# ═══════════════════════════════════════════════════════════════

print(f"\n{'=' * 70}")
print("Diagnosis & Improvement Guide")
print("=" * 70)

faithfulness_scores = result["faithfulness"]
avg_f = _avg(faithfulness_scores) if isinstance(faithfulness_scores, list) else faithfulness_scores

if not isinstance(avg_f, float) or math.isnan(avg_f):
    print("Faithfulness evaluation failed — check LLM compatibility.")
else:
    print(f"Faithfulness = {avg_f:.4f} — {'GOOD' if avg_f >= 0.7 else 'NEEDS WORK'}")

    if avg_f < 0.7:
        print(
            "\nFaithfulness LOW → LLM may be using prior knowledge instead of retrieved context.\n"
            "  Fix: strengthen prompt template to forbid external knowledge; lower temperature;\n"
            "  add explicit instruction 'if the context does not contain the answer, say so.'"
        )
    else:
        print("LLM is faithfully using retrieved context. Well-tuned prompt template.")

    print(
        "\nContext Recall / Precision / Answer Relevancy use the same embedding\n"
        "model as the retrieval pipeline (all-MiniLM-L6-v2). If any metric still fails,\n"
        "verify ragas version compatibility with langchain_huggingface."
    )
