package com.example.agentgateway.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import jakarta.validation.constraints.NotBlank;

@ConfigurationProperties(prefix = "langchain4j.openai")
@Validated
public record LangChain4jProperties(
        @NotBlank String apiKey,
        @NotBlank String baseUrl,
        @NotBlank String modelName,
        double temperature,
        int maxTokens) {
}
