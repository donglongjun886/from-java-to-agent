# Day 11 (2026.06.23 一) — IR 基础 + Embedding + 首个 RAG Pipeline

## Part 1: IR 理论基础 ✅

### 核心认知

信息检索的本质是**召回+排序两阶段**，不是并列方案而是递进关系。 以前对 IR 的理解停留在「ES 全文搜索」这个层次——知道倒排索引、知道 `BM25` 是默认算法，但没想过这三个东西之间的结构关系。

今天把这个结构理清楚了：

| 概念 | 本质 | 关系 |
|------|------|------|
| 倒排索引 | 数据结构（term -> posting list） | 检索的底层存储引擎 |
| `TF-IDF` | 相关性评分公式 | 基于倒排索引的评分逻辑 |
| `BM25` | `TF-IDF` 的工业加强版 | 解决 TF 饱和 + 文档长度归一化两个核心缺陷 |

三者不是平行选项，而是逐层递进。倒排索引是地基，`TF-IDF` 是第一代评分方案，`BM25` 是迭代了二十年的最优解。很多人把倒排索引和 `BM25` 并列说「选倒排索引还是 `BM25`」，这等于在问「选 B+Tree 还是选 MySQL」——根本不在一个抽象层级。

**`BM25`** 的两个核心改进，用 Java 类比讲得通：
- **TF 饱和**：一篇文档提 100 次"分布式"和提 10 次，相关性差距不是 10 倍——词频有边际递减效应。类比缓存命中率：QPS 从 0 到 1000 收益巨大，从 10000 到 11000 几乎没区别。`BM25` 的 `k1` 参数（通常 1.2~1.5）控制饱和速度，类似 Guava Cache 的 `maximumSize`。
- **文档长度归一化**：短文档天然每个词的 TF 更高，如果不用 `b` 参数（通常 0.75）做长度惩罚，短文档会永远霸占 top-k。类似 JVM 里如果只看吞吐不看延迟，批处理会永远抢占交互式任务的 CPU 时间。

稠密检索解决的是稀疏检索的致命伤：**词不匹配（vocabulary mismatch）**。 搜「分布式锁」找不到写「Redisson」的文档——ES 只能靠人工维护同义词表，但 `Embedding` 模型天然把语义相近的文本映射到向量空间的邻近区域。这个能力不是「调参优化」，是底层范式的跨越：从「匹配字符串」到「匹配语义」。

混合检索的互补逻辑很简单：`BM25` 保证精确匹配不丢（序列号、错误码、API 名），向量保证模糊语义不丢（同义词、口语化表达、跨语言）。两路召回后用 `RRF`（Reciprocal Rank Fusion）融合——`1/(k+rank)` 的公式让排名越高的文档贡献越大，不依赖两路原始分数的绝对值（`BM25` 分数和余弦相似度本身不可比）。Java 类比：两个微服务各返回一个排序列表，`RRF` 就是那个加权合并策略。

### 笔记产出

- [information-retrieval-basics.md](../../notes/week-03/information-retrieval-basics.md)：倒排索引/`TF-IDF`/`BM25`/稠密检索/混合检索/`RRF` 融合，从数据结构层讲到评分公式层再到融合策略层

---

## Part 2: Embedding 向量化实战 ✅

### 核心认知

`Embedding` 是把「语言」翻译成「坐标系」，让计算机做**语义加减法**。 模型选的是 `all-MiniLM-L6-v2`——80MB 本地运行，384 维输出，单条推理 10ms，零成本。这个选择有刻意性：第一手的 RAG 实践应该从最朴素的方案开始，先理解维度、相似度、归一化这些基本概念，再谈换大模型。

`embedding_explorer.py` 做了三件事：
1. 8 条文本（3 条 Java 技术 + 3 条 AI 技术 + 2 条生活类）全部编码为 384 维向量并 L2 归一化
2. 分四组计算余弦相似度：Java↔Java、AI↔AI、Java↔AI、Tech↔Misc，验证同类文本向量距离更近的直觉
3. 用「How to build an AI agent with Java Spring」做查询，对 8 条文档做相似度排序——结果最相关的是 Java 和 AI 的混合文档，misc 类排名垫底，语义排序完全符合预期

实验中最直观的发现：同类文本余弦相似度普遍 0.5~0.7，跨领域（Java↔Misc）降到 0.2 以下。384 维在这个小规模场景下完全够用——语义区分度明显，不需要上 1536 维大模型。

关于**维度**的认知：384 维不是「阉割版」，是「够用版」。384 维实数空间理论上能编码远超 384 个正交方向，实际语义特征集中在低秩子空间。百万级文档场景下，384 维 = 1.5GB，1536 维 = 6GB——存储和检索延迟的差异是指数级的。先跑通再优化，而不是一上来就堆资源。这个工程习惯来自 Java 后端的教训：先压测看瓶颈在哪，再决定优化谁，不要预判。

### 代码产出

- `embedding_explorer.py`：`SentenceTransformer` 编码 + L2 归一化 + 分组余弦相似度对比 + 检索演示（查询向量与文档矩阵点积排序）

### 笔记产出

- [embeddings-and-vector-db.md](../../notes/week-03/embeddings-and-vector-db.md)：`Embedding` 本质/本地模型参数与局限/三种相似度计算对比/`ChromaDB` 核心概念分层/where 子句语法与边界条件

---

## Part 3: LlamaIndex + ChromaDB 首次跑通 RAG Pipeline ✅

### 核心认知

**`LlamaIndex`** 相当于 Spring Data JPA，它不创造新能力，但把散落的底层操作统一成一个**数据层抽象**。 以前 RAG 的印象是：自己调用 `Embedding` API、自己管理向量库连接、自己拼接 Prompt、自己解析结果——每步都是手写的胶水代码。`LlamaIndex` 做的事就是把「文档加载 → 索引构建 → 检索 → 生成」这条链路上的 boilerplate 全部封装掉。

`first_rag.py` 的完整 Pipeline：
1. **数据准备**：6 篇技术文档（Spring Boot 自动配置、Java 虚拟线程、HikariCP 连接池、MCP 协议、LangGraph 编排、RAG 原理），直接用 `Document` 对象包装
2. **LLM 层**：DeepSeek V4 Pro 通过 OpenAI 兼容模式接入（使用 `LlamaIndex` 的 `OpenAILike` 类原生接入任意 OpenAI 兼容 API，无需模型名校验。勿劫持私有方法如 `_get_model_name`，框架小版本升级即可导致崩溃）
   > API Key 通过 `.env` 文件加载，严禁硬编码在代码中。

3. **Embedding 层**：`HuggingFaceEmbedding` 本地运行 `all-MiniLM-L6-v2`，384 维，与 Part 2 同模型
4. **向量库层**：`ChromaDB` PersistentClient 落盘存储，`get_or_create_collection` 管理索引生命周期
5. **索引层**：`VectorStoreIndex.from_documents()` 一行完成文档切分、编码、入库，对开发者透明的默认切分策略（`LlamaIndex` 内置 tokenizer 默认 1024 token/chunk + 20 token overlap）
6. **查询层**：自定义 PromptTemplate（要求优先使用上下文中的具体数字和公式），`similarity_top_k=3` 检索最相关 chunk，`source_nodes` 获得引用溯源

**查询测试用的是刻意设计的复合问题**：「How should I configure HikariCP pool size when using Java virtual threads in a Spring Boot microservice, and why?」这个问题需要同时理解连接池公式（HikariCP 文档）、虚拟线程特性（JVM 文档）、Spring Boot 自动配置（Spring 文档）——三篇文档横跨 Java 基础设施的不同层次。RAG 必须从 6 篇文档中准确召回这 3 篇并做交叉融合。输出结果正确引用了 pool size = `Tn * (Cm - 1) + 1` 公式和虚拟线程 I/O-bound 场景分析，说明检索+生成的链路是通的。

`ChromaDB` 的认知定位：`ChromaDB` 在向量数据库生态里相当于 SQLite 在关系型数据库里——不是最强的，但是最快上手的。PersistentClient 落盘到 `chroma_db/` 目录，DuckDB/SQLite 做底层存储，单进程访问。如果要上多客户端/团队共享，需要切换到 Client-Server 模式。当前阶段 Persistent 够用，后续企业级场景（多租户隔离、文档 ACL）再深入 Client-Server + metadata 过滤。

### 代码产出

- `first_rag.py`：完整的 RAG Pipeline，`LlamaIndex` 统一编排 + `ChromaDB` 向量存储 + DeepSeek 生成 + local `Embedding` 编码 + 引用溯源打印

---

## 今日统计

- **笔记**：2 篇（IR 基础 + Embedding/向量数据库）
- **代码**：2 个 Python 文件（Embedding Explorer + First RAG）
- **提交**：2 个 commit（Part1+2 合一个，Part3 单独一个）

> **核心认知锚点**：IR 的本质是召回+排序两阶段，不是并列方案而是递进关系——倒排索引是地基，`TF-IDF` 是第一代评分，`BM25` 是二十年迭代的最优解。`Embedding` 不是替代 `BM25`，是补齐它不会做的事（语义泛化），两者互补耦合才构成混合检索。`LlamaIndex` 封装的不是「新技术」，是「把这些东西串在一起的 boilerplate」——理解了底层再看框架，才知道每一层抽象在解决什么问题。
