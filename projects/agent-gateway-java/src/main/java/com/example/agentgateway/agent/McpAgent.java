package com.example.agentgateway.agent;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;

public interface McpAgent {

    @SystemMessage("""
            你是智能助手，用中文回答，简洁准确。
            你可以使用 MCP 协议动态发现的所有工具来完成用户请求。
            """)
    String chat(@UserMessage @V("message") String message);
}
