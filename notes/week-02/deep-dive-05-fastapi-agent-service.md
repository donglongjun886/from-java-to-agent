# FastAPI 服务化：Agent HTTP/SSE 接口设计

> FastAPI 已成为 Agent 服务化的事实标准——不是因为它比 Spring Boot 强，而是因为 Python 生态的 LLM SDK 都在 asyncio 上，FastAPI 是原生的 async 一等公民。

## 关键对比 / 架构认知

**SSE vs WebSocket 的选择**

| 维度 | SSE（Server-Sent Events） | WebSocket |
|------|--------------------------|-----------|
| 方向 | 单向（Server → Client） | 全双工 |
| 协议 | HTTP（标准语义） | 独立协议（Upgrade from HTTP） |
| 重连 | 浏览器原生支持（EventSource API） | 需手动实现 |
| 适用场景 | LLM 流式输出（token by token） | 实时双向交互（聊天室） |
| 运维友好 | 经过 HTTP 代理/网关不需要特殊配置 | 需 LB 支持 WebSocket |

**结论**：Agent 场景绝大多数走 SSE——因为交互模式是"用户发请求 → Agent 流式返回"，天然单向。WebSocket 只在 Human-in-the-Loop 需要多次交互时才有价值。

**生产级 Agent 接口设计要点**：
- 超时策略：LLM 调用可能有 30s+ 延迟，HTTP 超时需设置 60s 以上，同时在 SSE 通道发 heartbeat
- 错误码分层：LLM 错误（4xx/5xx from model provider）vs 业务错误（Tool 超时/权限拒绝）需区分
- 中断传播：SSE 连接断开 → 通知 Agent 停止推理（避免浪费 Token）

## Java 映射 + 面试话术

**Java 类比**：
- FastAPI 的 `async def` ≈ **CompletableFuture 的异步语义**——都能写非阻塞代码，但 asyncio 是单线程事件循环协作式调度，CompletableFuture 底层可用 `ForkJoinPool`（工作窃取），并发模型不完全相同
- `StreamingResponse` ≈ **WebFlux `Flux<ServerSentEvent>`**——流式推送，背压由 ASGI 框架处理
- FastAPI 依赖注入（`Depends`）≈ **Spring `@Autowired`**——只是 Python 用函数参数注入，Java 用字段注入

**面试这么说**：
> "FastAPI 服务化 Agent 我关注三个点。第一，流式输出用 SSE 不用 WebSocket——Agent 交互是单向的 token 流，SSE 够用且运维友好，经过 Nginx/Kong 不需要额外配置。第二，时间预算管理——LLM 单次调用可能 30 秒以上，HTTP 超时需要拉到 60 秒，同时 SSE 通道发 heartbeat 防止网关误杀。第三，中断传播——SSE 断开时要通知 Agent 停止推理，不然白白烧 Token。这跟 Spring WebFlux 的取消信号（`onCancel`）是一个道理。"
