package com.example.agentgateway.agent;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;

public interface WeatherAgent {

    @SystemMessage("""
            你是天气预报助手，用中文回答，简洁准确。
            当用户询问天气时，使用 getWeather 工具查询指定城市的天气信息。
            当用户请求数学计算时，使用 calculate 工具进行运算。
            """)
    String chat(@UserMessage @V("message") String message);
}
