package com.example.agentgateway.config;

import com.example.agentgateway.agent.WeatherAgent;
import com.example.agentgateway.tool.WeatherTools;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.service.AiServices;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(LangChain4jProperties.class)
public class LangChain4jConfig {

    private final LangChain4jProperties props;

    public LangChain4jConfig(LangChain4jProperties props) {
        this.props = props;
    }

    @Bean
    public OpenAiChatModel openAiChatModel() {
        return OpenAiChatModel.builder()
                .apiKey(props.apiKey())
                .baseUrl(props.baseUrl())
                .modelName(props.modelName())
                .temperature(props.temperature())
                .maxTokens(props.maxTokens())
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
