package com.example.agentgateway.controller;

import com.example.agentgateway.agent.WeatherAgent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AgentController {

    private final WeatherAgent weatherAgent;

    public AgentController(WeatherAgent weatherAgent) {
        this.weatherAgent = weatherAgent;
    }

    @GetMapping("/agent/weather")
    public String weather(@RequestParam(defaultValue = "杭州今天天气怎么样？") String msg) {
        return weatherAgent.chat(msg);
    }
}
