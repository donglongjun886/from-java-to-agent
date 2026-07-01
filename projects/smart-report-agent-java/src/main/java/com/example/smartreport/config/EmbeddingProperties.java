package com.example.smartreport.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Embedding 模型独立配置 — 因 DeepSeek 不支持 /v1/embeddings 端点，
 * 嵌入模型走 DashScope 兼容模式，与 Chat Model 分离。
 */
@ConfigurationProperties(prefix = "langchain4j.embedding")
public record EmbeddingProperties(
        String apiKey,
        String baseUrl,
        String model
) {
    @Override
    public String toString() {
        return "EmbeddingProperties[apiKey=***, baseUrl=" + baseUrl + ", model=" + model + "]";
    }
}
