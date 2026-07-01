package com.example.smartreport.config;

import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.model.openai.OpenAiEmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.inmemory.InMemoryEmbeddingStore;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

/**
 * LangChain4j Bean 配置 — Spring IoC 自动注入，避免手写工厂。
 * Python 版通过 LlamaIndex 的全局 Settings 对象管理依赖，Java 版用 Spring 依赖注入。
 *
 * 这里选择了 InMemoryEmbeddingStore 而不是 ChromaDB Java 客户端，原因：
 * 1. langchain4j-chroma 模块生态不够成熟（和 Python chromadb 客户端相比差距大）
 * 2. 内存存储对应 Python 版的 chromadb.EphemeralClient()，学习对照更直观
 * 3. 生产环境可替换为 PGVector (langchain4j-pgvector) 或 Elasticsearch
 */
@Configuration
@EnableConfigurationProperties({RagProperties.class, EmbeddingProperties.class})
public class LangChain4jConfig {

    private final RagProperties props;
    private final EmbeddingProperties embedProps;

    public LangChain4jConfig(RagProperties props, EmbeddingProperties embedProps) {
        this.props = props;
        this.embedProps = embedProps;
    }

    /**
     * ChatModel — OpenAI 兼容模式连 DeepSeek。
     * 和 Python 版 OpenAILike(api_base="https://api.deepseek.com", model="deepseek-chat") 等价。
     */
    @Bean
    public OpenAiChatModel chatModel() {
        return OpenAiChatModel.builder()
                .apiKey(props.apiKey())
                .baseUrl(props.baseUrl())
                .modelName(props.chatModel())
                .temperature(props.temperature())
                .maxTokens(props.maxTokens())
                .timeout(Duration.ofSeconds(60))
                .build();
    }

    /**
     * EmbeddingModel — 走 DashScope 兼容模式（OpenAI 兼容协议）。
     * DeepSeek 不支持 /v1/embeddings 端点，嵌入模型需独立配置。
     */
    @Bean
    public EmbeddingModel embeddingModel() {
        return OpenAiEmbeddingModel.builder()
                .apiKey(embedProps.apiKey())
                .baseUrl(embedProps.baseUrl())
                .modelName(embedProps.model())
                .timeout(Duration.ofSeconds(60))
                .build();
    }

    /**
     * 内存向量存储 — 对应 Python 版 chromadb.EphemeralClient()。
     * 支持 metadata 过滤 (Filter DSL)，实现租户隔离 + 角色 ACL。
     *
     * 警告：InMemoryEmbeddingStore 仅用于学习对照，数据不持久化，进程重启即丢失。
     * 生产环境必须替换为持久化方案，如 langchain4j-pgvector / langchain4j-elasticsearch。
     */
    @Bean
    public EmbeddingStore<TextSegment> embeddingStore() {
        return new InMemoryEmbeddingStore<>();
    }
}
