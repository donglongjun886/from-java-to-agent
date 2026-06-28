"""Langfuse 全链路追踪 — 将 RAG Pipeline 接入可观测平台

依赖:
    pip install langfuse

启动本地 Langfuse（Docker）:
    docker run -p 3000:3000 -p 3030:3030 \
      -e LANGFUSE_HOST=http://localhost:3000 \
      langfuse/langfuse

    首次访问 http://localhost:3000 注册账号，获取 Public/Secret Key，
    填入下方 LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY。

面试一句话:
    "我们用 Langfuse 做 RAG 全链路追踪 —— 每个用户查询从检索到生成到评估分数
     全部记录在一条 trace 里。线上 Faithfulness 低于阈值自动告警，
     比离线跑 RAGAS 脚本快一个数量级发现问题。"
"""

import os, sys
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

# ═══════════════════════════════════════════════════════════════
# Langfuse 初始化
# ═══════════════════════════════════════════════════════════════

LANGFUSE_AVAILABLE = False
try:
    from langfuse import Langfuse
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
        # 如果没配 key，Langfuse 会静默失败不抛异常，适合 demo 场景
    )
    if langfuse.auth_check():
        LANGFUSE_AVAILABLE = True
        print("Langfuse connected: traces will be recorded.")
    else:
        print("Langfuse not configured: traces will be printed to console only.")
except Exception:
    print("Langfuse not available: traces will be printed to console only.")


# ═══════════════════════════════════════════════════════════════
# RAG Pipeline Setup (复用已有配置)
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
    Document(text="HikariCP is a high-performance JDBC connection pool and the default in Spring Boot 2.x/3.x. The pool sizing formula is: pool_size = Tn * (Cm - 1) + 1, where Tn = max thread count and Cm = max simultaneous connections per thread. For a typical microservice with 20 threads, Cm=2, that yields 21 connections.", metadata={"doc_id": "D1-HikariCP"}),
    Document(text="Java Virtual Threads (JEP 444, finalized in JDK 21) are lightweight threads managed by the JVM. They are multiplexed onto a small pool of carrier threads. When a virtual thread blocks on I/O, the JVM unmounts it and mounts another ready virtual thread, enabling millions of concurrent connections in a single JVM process.", metadata={"doc_id": "D2-VirtualThreads"}),
    Document(text="RAG (Retrieval-Augmented Generation) grounds LLM responses in external knowledge. Pipeline: chunk → embed → store → retrieve top-k → inject into prompt → generate. Chunk size is critical: too small loses context, too large dilutes relevance.", metadata={"doc_id": "D3-RAG"}),
    Document(text="The Model Context Protocol (MCP) connects AI apps to external tools via JSON-RPC 2.0. Three primitives: Resources, Tools, Prompts. It is analogous to Java's SPI — a standard contract for runtime plugin discovery.", metadata={"doc_id": "D4-MCP"}),
]

chroma_client = chromadb.Client()
try:
    chroma_client.delete_collection("langfuse_demo")
except (ValueError, chromadb.errors.NotFoundError):
    pass
collection = chroma_client.get_or_create_collection("langfuse_demo")
vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)


# ═══════════════════════════════════════════════════════════════
# 可观测 RAG Pipeline
# ═══════════════════════════════════════════════════════════════

class TracedRAGPipeline:
    """带 Langfuse 追踪的 RAG Pipeline。

    Trace 结构:
      User Query (trace)
        ├── Retrieval (span)
        │     └── Embedding + Vector Search (observation)
        ├── LLM Generation (generation)
        │     └── input: prompt + context
        │     └── output: answer
        └── Score (事后)
              ├── faithfulness
              ├── answer_relevancy
              └── context_recall
    """

    def __init__(self, index, trace_name="rag-query"):
        self.query_engine = index.as_query_engine(
            similarity_top_k=3,
            text_qa_template=PromptTemplate(
                "Context:\n{context_str}\n\n"
                "Answer the query using the context above.\n"
                "Query: {query_str}\nAnswer: "
            ),
        )
        self.trace_name = trace_name

    def query(self, question: str, user_id: str = "demo-user") -> dict:
        """执行 RAG 查询，Langfuse 自动追踪全链路。"""
        trace = None
        if LANGFUSE_AVAILABLE:
            trace = langfuse.trace(
                name=self.trace_name,
                user_id=user_id,
                metadata={"question": question},
            )

        # Step 1: Retrieval
        if trace:
            retrieval_span = trace.span(name="retrieval", metadata={"top_k": 3})
        else:
            retrieval_span = _NoopSpan()

        with retrieval_span:
            response = self.query_engine.query(question)
            retrieved_docs = [
                {"text": node.text[:120], "score": round(node.score or 0, 4)}
                for node in response.source_nodes
            ]
            retrieval_span.update(metadata={"retrieved_count": len(retrieved_docs)})
            retrieval_span.update(output={"retrieved_docs": retrieved_docs})

        # Step 2: Generation (Langfuse tracks LLM calls as "generations")
        if trace:
            gen = trace.generation(
                name="llm-generation",
                model="deepseek-chat",
                input={
                    "question": question,
                    "context": [d["text"] for d in retrieved_docs],
                },
                output={"answer": str(response)},
            )
            gen.end()

        # Step 3: Attach evaluation scores (事后打分，生产环境异步做)
        if trace:
            trace.score(name="retrieved_count", value=len(retrieved_docs))

        if trace:
            trace.update(output={"answer": str(response)})

        return {
            "answer": str(response),
            "retrieved_docs": retrieved_docs,
        }

    def score_trace(self, trace_id: str, scores: dict):
        """将 RAGAS 评估结果回写到 trace 上。

        生产流程: RAG 查询 → Langfuse trace → 异步评估 → 写回 scores
        不是每次都实时评估，而是采样（如 10%）或用缓存评估 LLM 批量打分。
        """
        if not LANGFUSE_AVAILABLE:
            print(f"[Offline] Scores for trace={trace_id}: {scores}")
            return
        trace = langfuse.trace(id=trace_id)
        for metric, value in scores.items():
            trace.score(name=metric, value=value)
        print(f"[Langfuse] Scores written to trace={trace_id}")


class _NoopSpan:
    """当 Langfuse 不可用时，提供无操作的 context manager 替代。"""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def update(self, **kwargs):
        pass


# ═══════════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pipeline = TracedRAGPipeline(index)

    print("=" * 70)
    print("Langfuse 全链路追踪 Demo")
    print("=" * 70)

    queries = [
        "What is the HikariCP pool sizing formula?",
        "How do virtual threads affect connection pooling?",
    ]

    for q in queries:
        print(f"\nQuery: {q}")
        result = pipeline.query(q)
        print(f"Answer: {result['answer'][:120]}...")
        print(f"Retrieved: {len(result['retrieved_docs'])} docs")

    print(f"\n{'=' * 70}")
    print("Trace 结构说明")
    print("=" * 70)
    print("""
  每个用户查询在 Langfuse 中生成一条 Trace:

    Trace: "rag-query"
    ├── Span: "retrieval"
    │     ├── metadata: top_k=3
    │     ├── output: [{text, score}, ...]
    │     └── duration: 自动计时
    ├── Generation: "llm-generation"
    │     ├── model: deepseek-chat
    │     ├── input: question + context
    │     ├── output: answer
    │     └── usage: {prompt_tokens, completion_tokens, total_tokens}
    └── Scores: {retrieved_count, faithfulness, ...}

  面试要点:
    1. "我们不是等用户投诉才知道 RAG 出问题 — Langfuse dashboard 实时显示
        Faithfulness 分数分布，低于 0.7 的 trace 自动拉警报。"
    2. "离线评估 (RAGAS) 测模型质量，在线追踪 (Langfuse) 测运行质量。
       两者配合: 离线定基线，在线做漂移检测。"
    3. "Context Recall 从 0.85 掉到 0.6 → embedding 模型退化 →
       需要重新训练或切换模型。没有 tracing 根本发现不了。"
""")

    if not LANGFUSE_AVAILABLE:
        print("""──
  启动本地 Langfuse 查看实际 trace:
    docker run -d --name langfuse \\
      -p 3000:3000 -p 3030:3030 \\
      -e LANGFUSE_HOST=http://localhost:3000 \\
      langfuse/langfuse

  然后设置环境变量:
    export LANGFUSE_PUBLIC_KEY=pk-xxx
    export LANGFUSE_SECRET_KEY=sk-xxx
    export LANGFUSE_HOST=http://localhost:3000
""")
