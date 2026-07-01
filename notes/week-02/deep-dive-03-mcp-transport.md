# MCP 协议深度：Transport 层对比

> MCP 的 Transport 层决定了生产部署的形态——stdio 适合开发，SSE 适合服务端推送，Streamable HTTP 是 2025 年新增的工业级方案。

## 关键对比 / 架构认知

| 维度 | stdio | SSE | Streamable HTTP |
|------|-------|-----|-----------------|
| 通信模型 | 子进程 stdin/stdout | HTTP 长连接（单向推送） | HTTP 双向流（Bidirectional） |
| 部署模式 | 同机进程 | 独立服务（可跨机） | 独立服务（可跨机） |
| 客户端要求 | 需能启动子进程 | 标准 HTTP 客户端 | HTTP/2 或支持 streaming |
| 安全性 | 进程隔离（天然安全） | 需额外认证层 | 可复用 HTTP 安全体系（OAuth/API Key） |
| 性能 | 无网络开销，最快 | 中等（单向流） | 最优（双向流，支持 multiplexing） |
| 生产就绪 | 否（调试工具用） | 较成熟 | 2025 新增，逐步替代 SSE |

**演进逻辑**：
- stdio：协议设计初期，演示 MCP Server 概念
- SSE：解决远程部署需求，但单向推送限制大
- Streamable HTTP：统一同步+异步请求，支持 session 管理和断线重连，逐步成为推荐方案

**选择建议**：
- 本地开发/IDE 插件 → stdio（零配置，安全隔离）
- 内部服务间调用 → Streamable HTTP（性能+安全）
- 兼容旧版本客户端 → SSE（过渡方案）

## Java 映射 + 面试话术

**Java 类比**：
- stdio ≈ `ProcessBuilder` 启动子进程，通过 stdin/stdout 管道通信——同机部署但进程隔离，Go/Node 编写的 MCP Server 崩溃不会拖垮 Java 主进程
- SSE ≈ **WebFlux Server-Sent Events**——服务端单向推送，适合流式响应
- Streamable HTTP ≈ **gRPC bidirectional streaming**——双向流，支持请求复用和全双工通信

**面试这么说**：
> "MCP Transport 选型核心看两个维度：部署拓扑和通信模式。开发阶段 stdio 最简单，Claude Desktop 就是用 stdio 启动 MCP Server 子进程。上生产我推荐 Streamable HTTP，它在架构上类似 gRPC 的双向流——支持 session 管理、请求 multiplexing，而且能直接复用现有的 API Gateway 认证体系。SSE 是过渡方案，因为只能服务端推客户端，客户端想发消息还得另起一个 POST 请求，不够优雅。"
