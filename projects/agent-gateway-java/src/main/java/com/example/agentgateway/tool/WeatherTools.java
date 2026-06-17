package com.example.agentgateway.tool;

import dev.langchain4j.agent.tool.Tool;
import dev.langchain4j.agent.tool.P;
import org.springframework.stereotype.Component;

@Component
public class WeatherTools {

    @Tool("查询指定城市的天气信息")
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

    @Tool("执行数学计算（支持加减乘除和括号）")
    public double calculate(@P("数学表达式，例如 1+2*3") String expression) {
        try {
            return evaluate(expression);
        } catch (Exception e) {
            throw new RuntimeException("计算失败: " + expression + " — " + e.getMessage());
        }
    }

    /**
     * Simple recursive descent parser for basic arithmetic (+, -, *, /, parentheses).
     * Thread-safe: each invocation creates fresh state.
     */
    private double evaluate(String str) {
        return new Object() {
            int pos = -1, ch;

            void nextChar() {
                ch = (++pos < str.length()) ? str.charAt(pos) : -1;
            }

            boolean eat(int charToEat) {
                while (ch == ' ') nextChar();
                if (ch == charToEat) {
                    nextChar();
                    return true;
                }
                return false;
            }

            double parse() {
                nextChar();
                double x = parseExpression();
                if (pos < str.length()) throw new RuntimeException("非法字符: " + (char) ch);
                return x;
            }

            double parseExpression() {
                double x = parseTerm();
                for (; ; ) {
                    if (eat('+')) x += parseTerm();
                    else if (eat('-')) x -= parseTerm();
                    else return x;
                }
            }

            double parseTerm() {
                double x = parseFactor();
                for (; ; ) {
                    if (eat('*')) x *= parseFactor();
                    else if (eat('/')) {
                        double divisor = parseFactor();
                        if (Math.abs(divisor) < 1e-10) throw new ArithmeticException("除数不能为零");
                        x /= divisor;
                    }
                    else return x;
                }
            }

            double parseFactor() {
                if (eat('+')) return parseFactor();
                if (eat('-')) return -parseFactor();
                double x;
                int startPos = this.pos;
                if (eat('(')) {
                    x = parseExpression();
                    eat(')');
                } else if ((ch >= '0' && ch <= '9') || ch == '.') {
                    while ((ch >= '0' && ch <= '9') || ch == '.') nextChar();
                    x = Double.parseDouble(str.substring(startPos, this.pos));
                } else {
                    throw new RuntimeException("非法字符: " + (char) ch);
                }
                return x;
            }
        }.parse();
    }
}
