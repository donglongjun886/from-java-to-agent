package com.example.smartreport.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * LangChain4j 配置属性 — 外置化到 application.yml。
 * 对应 Python 版中通过 os.getenv + OpenAILike 构造参数的逻辑。
 * 和 agent-gateway-java 的 LangChain4jProperties 模式保持一致。
 */
@ConfigurationProperties(prefix = "langchain4j.openai")
public record RagProperties(
        String apiKey,
        String baseUrl,
        String chatModel,
        Double temperature,
        Integer maxTokens
) {
    @Override
    public String toString() {
        return "RagProperties[apiKey=***, baseUrl=" + baseUrl
                + ", chatModel=" + chatModel
                + ", temperature=" + temperature
                + ", maxTokens=" + maxTokens + "]";
    }
}
