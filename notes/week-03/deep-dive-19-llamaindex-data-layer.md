# LlamaIndex数据层 — 异构数据源统一摄入管道设计

> LlamaIndex不是又一个向量数据库封装，而是一套"让任意数据源以统一方式进入RAG管道"的数据抽象框架——它解决的问题在摄入侧，不在检索侧。

## 关键对比 / 架构认知

LlamaIndex的核心架构分三层：**Data Connectors**负责从异构数据源读取原始数据；**Index**负责把Document转换为可检索的结构（向量索引/关键词索引/知识图谱）；**Query Engine**在最上层提供统一查询接口。三层之间靠一个统一的 **Document Schema** 衔接：Document核心由text/content + metadata(dict，内含source_type/permissions等自定义字段) + embedding + node_id构成。无论上游是PDF、Confluence页面、数据库表还是Slack消息，到了Document这一层都变成同一种数据结构，下游的索引构建和查询引擎无需关心数据来源。

这个统一抽象的价值在**IngestionPipeline**中体现得最典型。管道由四个阶段串联：Reader（连接器读取）→ Transformations(切分+元数据提取+Embedding) → VectorStore（写入）。管道的每个阶段是可插拔的——你可以把Reader从PDF切到Notion只需换一个连接器，其他阶段不变。这和Java后端中数据导入管道的设计思想完全一致：Reader是Source，Transformations是Processor，VectorStore是Sink。

异构数据源映射的典型场景：PDF走Unstructured库做版面解析（处理双栏、表格、图片），数据库通过CDC（Change Data Capture）做增量同步而不是全量拉取，API类数据源用定时轮询+去重机制保证幂等。这些是企业级落地的数据接入模式，需要结合外部基础设施（Debezium/Airflow/Cron）与LlamaIndex的Reader抽象共同实现。每种数据源接入成本不同，但一旦完成Reader适配，后续流程完全复用。对比LangChain的做法：LangChain也有Document抽象，但它更偏"工具链拼装"，在索引构建和异构检索这一特定维度上，LlamaIndex的抽象更深入——LlamaIndex把Index本身作为一等公民（不同类型的索引之间可以组合查询），这是它区别于LangChain的关键设计取舍。

## Java 映射 + 面试话术

**Java 映射**：LlamaIndex的三层抽象就是Spring Data的翻版。Spring Data JPA的统一Repository接口屏蔽了底层MySQL/PostgreSQL/MongoDB的差异，业务代码只依赖`CrudRepository`接口。LlamaIndex的Document就是Spring Data的Entity，Data Connector就是DataSource的适配器层，Index就是具体的Repository实现（JpaRepository vs MongoRepository），Query Engine就是Service层调用Repository的统一入口。还有一层更深的类比：IngestionPipeline就是ETL管道。Reader=Extract，Transformations=Transform，VectorStore=Load。十年经验的后端看这个架构，会立刻认出这是典型的适配器模式+管道模式组合。

**面试话术**："LlamaIndex的核心价值不在检索加速，而在数据摄入的标准化。它定义了一个统一的Document Schema，让无论来自PDF、数据库还是API的数据，在进入RAG管道前都变成同一种结构。这种统一数据模型的设计在后端很常见——Spring Data就是这么做的，把MySQL和MongoDB的差异封在Repository接口后面。一旦数据模型统一，后面的切分、向量化、写入流程就可以完全复用。实际落地的关键挑战不在主流程，而在边缘场景——比如PDF的双栏布局解析、数据库的CDC增量同步、API的幂等去重。我选LlamaIndex而不是LangChain做数据层，就是因为它在索引侧做了更深层的抽象，数据模型的设计更像企业级的数据中台架构。"
