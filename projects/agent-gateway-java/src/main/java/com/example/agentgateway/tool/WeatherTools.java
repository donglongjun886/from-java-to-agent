package com.example.agentgateway.tool;

import dev.langchain4j.agent.tool.Tool;
import dev.langchain4j.agent.tool.P;
import org.springframework.stereotype.Component;

@Component
public class WeatherTools {

    @Tool("查询指定城市的天气信息（演示数据）")
    public String getWeather(@P("城市名称") String city) {
        return switch (city) {
            case "杭州" -> "杭州：晴，28°C，湿度65%，风力2级";
            case "北京" -> "北京：多云，22°C，湿度40%，风力3级";
            case "深圳" -> "深圳：雷阵雨，31°C，湿度85%，风力1级";
            case "上海" -> "上海：阴，25°C，湿度70%，风力2级";
            case "成都" -> "成都：晴，29°C，湿度55%，风力1级";
            default -> city + "：暂无天气数据，请确认城市名称";
        };
    }
}
