# agent-gateway-java

> Day 2 晚段对照：**Spring Boot + Spring AI Alibaba + 阿里云通义千问** Hello World。
> 对照白天 Python 项目的 OpenAI 兼容 API 调用方式。

## 跑通步骤

```bash
# 1. 确认环境
java -version    # 需要 Java 17+
mvn -version     # 需要 Maven 3.8+

# 2. 确认环境变量
echo $DASHSCOPE_API_KEY    # 不能为空
# 如果没设：export DASHSCOPE_API_KEY=sk-xxx
# 或从项目根 .env 加载：export $(cat ../.env | xargs)

# 3. 启动
mvn spring-boot:run

# 4. 测试（另开终端）
curl "http://localhost:8080/chat?msg=你好"
```

## 项目结构

```
agent-gateway-java/
├── pom.xml                                    # Spring Boot 3.3 + Spring AI Alibaba 1.0
├── src/main/java/com/example/agentgateway/
│   ├── AgentGatewayApplication.java           # 启动类
│   └── ChatController.java                    # REST 控制器
├── src/main/resources/
│   └── application.yml                        # DashScope 配置
└── README.md
```

## Python ↔ Java 对照

| 概念 | Python (白天主线) | Java (本项目) |
|------|-------------------|--------------|
| HTTP 框架 | FastAPI / Flask | Spring Boot MVC |
| LLM 客户端 | `openai.OpenAI()` | `ChatClient` (Spring AI) |
| 消息发送 | `client.chat.completions.create(...)` | `chatClient.prompt().user(msg).call().content()` |
| 配置文件 | `.env` | `application.yml` |
| API Key | 环境变量 | `${DASHSCOPE_API_KEY}` |
| 启动命令 | `python main.py` | `mvn spring-boot:run` |
| 依赖管理 | `pyproject.toml` / `requirements.txt` | `pom.xml` |
| Bean 管理 | 手动 / 第三方 DI | Spring IoC 容器自动注入 |

## 关键代码 1:1 对照

**Python (OpenAI 兼容)**：
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen-turbo",
    temperature=0.7,
    messages=[{"role": "user", "content": "你好"}]
)
print(response.choices[0].message.content)
```

**Java (Spring AI Alibaba)**：
```java
@RestController
public class ChatController {
    private final ChatClient chatClient;

    public ChatController(ChatClient.Builder builder) {
        this.chatClient = builder.build();
    }

    @GetMapping("/chat")
    public String chat(@RequestParam String msg) {
        return chatClient.prompt()
                .user(msg)
                .call()
                .content();
    }
}
```

## 关键设计差异

1. **依赖注入**：Java 用 Spring IoC 自动注入 `ChatClient.Builder`，Python 没有这一步（手动创建 client）
2. **配置外置**：Java 用 `application.yml`（Spring Boot 标准），Python 用 `.env`（约定俗成）
3. **类型安全**：Java 编译期校验 `chatClient.prompt().user().call()` 的链式调用，Python 是鸭子类型
4. **启动开销**：Java JVM 启动慢（秒级），Python 进程启动快（毫秒级）—— 这是 AI 工具调用场景下 Python 主流的隐性原因

## 依赖版本

| 组件 | 版本 |
|------|------|
| Spring Boot | 3.3.5 |
| Spring AI | 1.0.0 (BOM) |
| spring-ai-starter-model-openai | (由 BOM 管理) |
| Java | 17 |

## ⚠️ 关键坑：DashScope 兼容模式

**不要用 `spring-ai-alibaba-starter-dashscope`**（走 DashScope 原生 API `/api/v1/services/aigc/...`），对 qwen3.7+ 等新模型不识别，会返回 `url error`。

**正确做法：用 `spring-ai-starter-model-openai` + DashScope 兼容模式**：

```yaml
spring:
  ai:
    openai:
      api-key: ${DASHSCOPE_API_KEY}   # 通义千问 Key 直接用
      base-url: https://dashscope.aliyuncs.com/compatible-mode   # 注意：不要带 /v1
      chat:
        options:
          model: qwen3.7-plus    # 兼容模式支持所有 Qwen 模型
```

**base-url 千万不要带 `/v1`**，否则 Spring AI 会拼成 `/compatible-mode/v1/v1/chat/completions`（v1 重复）。

**为什么这样能行**：
- DashScope 提供了 OpenAI 兼容的 API endpoint（`/compatible-mode/v1/chat/completions`）
- 所有 Qwen 模型（qwen-turbo / qwen-plus / qwen-max / qwen3.x / qwen3.7.x）都支持
- 复用 Spring AI 官方的 OpenAI starter，比等 alibaba 库更新要快

---

*最后更新：2026-06-08（Day 2 晚段）*
