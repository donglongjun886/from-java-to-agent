package com.example.agentgateway.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

@ConfigurationProperties(prefix = "langchain4j.openai")
@Validated
public record LangChain4jProperties(
        @NotBlank String apiKey,
        @NotBlank String baseUrl,
        @NotBlank String modelName,
        @Min(value = 0, message = "temperature must be >= 0")
        @Max(value = 2, message = "temperature must be <= 2")
        double temperature,
        @Min(value = 1, message = "maxTokens must be > 0")
        @Max(value = 32768, message = "maxTokens must be <= 32768")
        int maxTokens) {
}
