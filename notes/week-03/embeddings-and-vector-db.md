# Embedding 与向量数据库

> 面向有多年后端经验的 Java 工程师。目标：理解 Embedding 的"是什么/怎么用/什么坑"，以及 ChromaDB 在生产环境中的正确使用姿势。

---

## 1. Embedding 本质

**Embedding = 把文本映射到一个固定维度的浮点向量，语义相近的文本向量距离近。**

```
"猫"    → [0.12, -0.34, 0.78, ..., 0.05]   (384维)
"小猫"  → [0.11, -0.33, 0.76, ..., 0.04]   ← 距离近
"云计算" → [-0.21, 0.67, -0.15, ..., 0.82]  ← 距离远
```

一句话解释：Embedding 是把"语言"翻译成"坐标系"，让计算机可以做语义加减法—— `国王 - 男人 + 女人 ≈ 女王`。

| 传统搜索（关键词匹配） | 向量语义搜索 |
|---|---|
| SQL: `WHERE content LIKE '%弹簧%'` | `SELECT * ORDER BY cosine_distance(query_embedding, doc_embedding) LIMIT 10` |
| "弹簧" 搜不到"弹性部件" | "弹簧" 能搜到"弹性部件"、"减震器" |
| 分词器决定一切（中文分词是噩梦） | 模型理解语义，不依赖分词 |
| 索引结构：倒排索引（term → posting list 映射） | 索引结构：近似最近邻 ANN（HNSW 图） |

---

## 2. 本地模型：all-MiniLM-L6-v2

### 基础参数

| 属性 | 值 | 备注 |
|------|-----|------|
| 模型大小 | ~80MB | 下载一次，本地运行 |
| 输出维度 | 384 | 中等偏小 |
| 最大输入长度 | 256 token | 超长文本需要切 chunk |
| 推理速度 | ~10ms/条（MacBook Pro） | 纯 CPU，无 GPU 也能用 |
| 中文支持 | 有，但不如英文 | 模型主要用英文语料训练 |

### 使用体验

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embedding = model.encode("Java是一门面向对象的编程语言")  # shape: (384,) float32
embeddings = model.encode(["Java 21 虚拟线程", "Spring Boot 3"])  # 批量更快: (2, 384)
```

### 优点

- **零摩擦启动**：不调 API，不花钱，离线可用
- **速度快**：单条 10-20ms，批量更优
- **维度低**：384 维存 DB 空间小，相似度计算快

### 局限（面试重点）

- **上下文窗口仅 256 token**：一篇 2000 字的文章必须先切块再分别编码，丢失跨段语义
- **中文表现一般**：训练语料以英文为主，中文歧义词区分度不高（如"苹果"是水果还是公司）
- **固定 384 维**：无法根据场景权衡精度/速度，不如 OpenAI text-embedding-3 那样支持动态降维
- **无指令感知**：不像 text-embedding-3-large 那样可以根据 `instruction` 参数调整编码行为

### 适用场景

原型验证、英文为主的知识库、召回率要求不高的场景。

---

## 3. 相似度计算：三种方式对比

| 方法 | 公式（简化） | 值域 | 适用场景 |
|------|-------------|------|---------|
| **余弦相似度** | `cos = A·B / (|A|×|B|)` | [-1, 1] | **最常用**，文本语义检索，消除向量长度影响 |
| **欧氏距离** | `dist = sqrt(∑(Ai-Bi)²)` | [0, ∞) | 向量做聚类（K-Means），需要绝对值差异的场景 |
| **点积** | `dot = ∑(Ai×Bi)` | (-∞, ∞) | 模型已在训练时归一化，直接用点积 = 余弦 |

### 实际选择

```python
# 语义搜索 → 余弦（默认，几乎所有模型都假定用余弦检索）
# 聚类分析 → 欧氏距离  (KMeans metric='euclidean')
# API模型输出已归一化 → 点积=余弦（省一次除法，大批量时有用）
```

**面试触发点**：API 模型（如 text-embedding-3）返回的向量默认已 L2 归一化，此时余弦 = 点积，常常成为追问点。

---

## 4. ChromaDB 核心概念

### 分层对比

| ChromaDB 概念 | Java/后端类比 | 说明 |
|---|---|---|
| **Client** | DataSource / ConnectionPool | 管理数据库连接（Persistent / Ephemeral） |
| **Collection** | 数据库 Table | 存一组 embedding + metadata + document 的容器 |
| **Document** | 一行记录的 text 字段 | 原始文本，用于展示给用户或喂给 LLM |
| **Embedding** | 不可见的索引列 | 自动向量化（也可手动传入） |
| **Metadata** | 行级别的 JSON 属性 | 用于过滤、排序，**必须可序列化**（str/int/float/bool） |
| **ID** | 主键 | 字符串类型，add 重复 ID 会抛异常，覆盖需用 upsert |

### Persistent vs Ephemeral

```python
# Ephemeral：进程内内存，进程退出数据消失（原型开发用）
client = chromadb.Client()
# Persistent：落盘，重启后恢复（小规模生产）
client = chromadb.PersistentClient(path="./chroma_data")
```

| 模式 | 存储位置 | 适用场景 | 并发支持 |
|------|---------|---------|---------|
| **Ephemeral** | 内存 | 原型验证、单元测试 | 无 |
| **Persistent** | 磁盘（DuckDB/SQLite） | 开发/小规模生产 | 单进程 |
| **Client-Server** | ChromaDB Server | 多客户端/团队共享 | 原生支持 |

---

## 5. ChromaDB where 子句

### 基本语法

```python
collection.query(where={"source": "jd_report"})         # $eq 隐含
collection.query(where={"word_count": {"$gt": 100}})     # > 100
collection.query(where={"status": {"$ne": "archived"}})  # !=
# 范围: {"$gte": 0, "$lte": 10}  BETWEEN
# 集合: {"$in": ["a","b"]} IN  /  {"$nin": ["x","y"]} NOT IN
```

### 逻辑组合

```python
# AND（高频）
collection.query(where={"$and": [{"category": "tech"}, {"date": {"$gte": "2026-01-01"}}]})
# OR
collection.query(where={"$or": [{"priority": "high"}, {"source": "alert"}]})
```

### 字符串匹配

```python
{"title": {"$contains": "Java"}}   # LIKE '%Java%'
```

### 边界条件（考试级坑点）

- **Metadata 只支持四种类型**：str / int / float / bool。存 datetime / list / nested dict 会报错或行为不确定
- **`$contains` 区分大小写**
- **集合级别没有 metadata schema 约束**：不声明字段，不校验类型，新增字段零开销（类似 MongoDB，不像 MySQL）
- **`where` 过滤发生在向量检索之前**：ChromaDB 先按 metadata where 条件预过滤，再在过滤结果上做 ANN 检索。若 where 条件极苛刻（筛掉 99% 数据），metadata 扫描本身可能成为瓶颈——metadata 字段没有自动索引。

---

## 6. Java 生态类比总表

| Java/后端概念 | AI/Embedding 对应 | 关键差异 |
|---|---|---|
| Lucene 倒排索引 | Embedding 语义向量 | Lucene 搜字符串，Embedding 搜语义 |
| Elasticsearch 索引 | ChromaDB Collection | ES 全文搜索为主，ChromaDB 向量搜索为主 |
| MySQL Table | Collection | Collection 没有固定 Schema，Metadata 可随时加字段 |
| MyBatis Mapper | `collection.query()` / `collection.get()` | 参数结构类似 SQL where |
| SQL `ORDER BY score DESC` | `ORDER BY cosine_distance` | ES 的 `_score` 更接近：相关性评分 |
| Redis 缓存 | 短期记忆 / Conversation Buffer | Embedding 适用于长期语义记忆 |
| Jackson 序列化 | Metadata 字段的 JSON 序列化 | 必须存基本类型，存不下按 JSON string 存 |

---

## 7. 面试要点：为什么 384 维够用/不够用

### 够用的理由

- **低秩子空间**：384 维实数空间可编码远多于 384 个正交方向，实际语义特征集中在低秩子空间，384 维足够表达常见语义区分
- **性价比**：384 × 4B = 1.5KB/条 vs 3072 × 4B = 12KB/条。百万级文档：1.5GB vs 12GB，大部分企业知识库（几万篇）384 维绰绰有余
- **延迟优势**：维度越低 ANN 查询越快，生产环境 QPS 瓶颈通常在延迟而非精度

### 不够用的信号

| 信号 | 说明 | 行动 |
|------|------|------|
| 相似文档召回率低 | 相关文档没有被排在 Top-K | 升级更大维度的模型（768/1024/3072） |
| 多语言混用业务 | all-MiniLM 中文语料不足 | 换多语言模型（如 multilingual-e5-large） |
| 领域术语密集 | 法律/医疗/金融专有名词区分度不足 | 领域微调模型或换 text-embedding-3-large |
| 代码检索场景 | 变量名、函数签名语义与自然语言不同 | 使用 Code Embedding 专用模型（如 code-search） |
| 跨段落长文档 | 需要整篇文档级别的语义理解 | 换长上下文模型（512 token 以上）+ 分块策略优化 |

### 决策框架

```
all-MiniLM-L6-v2（免费本地）→ 召回不够 → text-embedding-3-small（512维）→ 精度还不够 → text-embedding-3-large（3072维）→ 领域特殊 → 微调
```

**面试加分回答**：不要只说"精度不够就换大模型"。先优化分块策略（chunk_size/overlap）、元数据过滤（缩小搜索空间）、混合检索（BM25+向量），成本更低且往往效果显著。
