"""First RAG Pipeline — LlamaIndex + ChromaDB + DeepSeek

依赖安装:
    pip install llama-index chromadb python-dotenv \
                llama-index-embeddings-huggingface \
                llama-index-vector-stores-chroma

环境变量:
    DEEPSEEK_API_KEY  (从项目根目录 .env 读取)
    HF_ENDPOINT=https://hf-mirror.com  (国内镜像)
"""

import os
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document, PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# ── LLM: DeepSeek via OpenAI compatible mode ──
# LlamaIndex 的 OpenAI 类内置模型名校验不认识 deepseek-chat，用 gpt-4 绕过校验，
# 再把 model 改回 deepseek-chat 让 API 调用正确，同时劫持 _get_model_name 保 metadata 校验通过。
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY 未在环境变量或 .env 文件中配置")

Settings.llm = OpenAI(
    model="gpt-4",
    api_key=api_key,
    api_base="https://api.deepseek.com",
    temperature=0.1,
)
Settings.llm._get_model_name = lambda: "gpt-4"
Settings.llm.model = "deepseek-chat"

# ── Embedding: local all-MiniLM-L6-v2 ──
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
)

# ── Documents: 6 technical docs across Java/Agent/Infra domains ──
documents = [
    Document(
        text=(
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
        ),
    ),
    Document(
        text=(
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
        ),
    ),
    Document(
        text=(
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
        ),
    ),
    Document(
        text=(
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
        ),
    ),
    Document(
        text=(
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
        ),
    ),
    Document(
        text=(
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
        ),
    ),
]

# ── Build ChromaDB Index ──
db_path = Path(__file__).resolve().parent / "chroma_db"
chroma_client = chromadb.PersistentClient(path=str(db_path))
try:
    chroma_client.delete_collection("tech_docs")
except ValueError:
    pass
collection = chroma_client.get_or_create_collection("tech_docs")

vector_store = ChromaVectorStore(chroma_collection=collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

# ── Query ──
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

query_engine = index.as_query_engine(
    similarity_top_k=3,
    text_qa_template=qa_template,
)
query = (
    "How should I configure HikariCP pool size when using Java virtual threads "
    "in a Spring Boot microservice, and why?"
)
response = query_engine.query(query)

print("=" * 60)
print(f"Query: {query}")
print("=" * 60)
print(f"\n{response}\n")
print("=" * 60)
print("Retrieved Source Chunks:")
print("=" * 60)
for i, node in enumerate(response.source_nodes, 1):
    print(f"\n[Source {i}]  Score: {node.score:.4f}")
    print(f"{node.text[:300]}...")
