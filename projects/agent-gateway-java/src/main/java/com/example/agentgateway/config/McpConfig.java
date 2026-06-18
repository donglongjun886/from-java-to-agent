package com.example.agentgateway.config;

import dev.langchain4j.mcp.McpToolProvider;
import dev.langchain4j.service.tool.ToolProvider;
import dev.langchain4j.mcp.client.DefaultMcpClient;
import dev.langchain4j.mcp.client.McpClient;
import dev.langchain4j.mcp.client.transport.stdio.StdioMcpTransport;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.service.AiServices;
import com.example.agentgateway.agent.McpAgent;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class McpConfig {

    /**
     * 通过 stdio 子进程连接 Python MCP Server，动态发现 get_weather 工具。
     * 路径相对于项目根目录（IDE 启动时 working dir 通常为项目根），
     * 即 from-java-to-agent/ 目录（学习项目上下文）。
     */
    @Bean(destroyMethod = "close")
    public McpClient mcpClient() {
        var transport = StdioMcpTransport.builder()
                .command(List.of(
                        ".venv/bin/python",
                        "projects/01-hello-agent/mcp_weather_server.py"
                ))
                .logEvents(true)
                .build();

        return DefaultMcpClient.builder()
                .transport(transport)
                .build();
    }

    @Bean
    public ToolProvider mcpToolProvider(McpClient mcpClient) {
        return McpToolProvider.builder()
                .mcpClients(List.of(mcpClient))
                .build();
    }

    @Bean
    public McpAgent mcpAgent(OpenAiChatModel chatModel, ToolProvider mcpToolProvider) {
        return AiServices.builder(McpAgent.class)
                .chatModel(chatModel)
                .toolProvider(mcpToolProvider)
                .build();
    }
}
