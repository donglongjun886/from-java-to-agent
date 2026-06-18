package com.example.agentgateway.controller;

import com.example.agentgateway.agent.WeatherAgent;
import com.example.agentgateway.agent.McpAgent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AgentController {

    private final WeatherAgent weatherAgent;
    private final McpAgent mcpAgent;

    public AgentController(WeatherAgent weatherAgent, McpAgent mcpAgent) {
        this.weatherAgent = weatherAgent;
        this.mcpAgent = mcpAgent;
    }

    /** 本地 @Tool 注册（WeatherTools.java 的 @Tool 方法） */
    @GetMapping("/agent/weather")
    public String weather(@RequestParam(defaultValue = "杭州今天天气怎么样？") String message) {
        return weatherAgent.chat(message);
    }

    /** MCP 动态发现（工具来自 Python MCP Server，通过 MCP 协议获取） */
    @GetMapping("/agent/mcp")
    public String mcp(@RequestParam(defaultValue = "杭州今天天气怎么样？") String message) {
        return mcpAgent.chat(message);
    }
}
