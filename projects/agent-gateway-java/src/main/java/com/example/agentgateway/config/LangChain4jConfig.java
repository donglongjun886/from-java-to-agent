package com.example.agentgateway.config;

import com.example.agentgateway.agent.WeatherAgent;
import com.example.agentgateway.tool.WeatherTools;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.service.AiServices;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class LangChain4jConfig {

    @Value("${langchain4j.openai.api-key}")
    private String apiKey;

    @Value("${langchain4j.openai.base-url}")
    private String baseUrl;

    @Value("${langchain4j.openai.model-name:deepseek-chat}")
    private String modelName;

    @Bean
    public OpenAiChatModel openAiChatModel() {
        return OpenAiChatModel.builder()
                .apiKey(apiKey)
                .baseUrl(baseUrl)
                .modelName(modelName)
                .temperature(0.7)
                .maxTokens(2048)
                .build();
    }

    @Bean
    public WeatherAgent weatherAgent(OpenAiChatModel chatModel, WeatherTools weatherTools) {
        return AiServices.builder(WeatherAgent.class)
                .chatModel(chatModel)
                .tools(weatherTools)
                .build();
    }
}
