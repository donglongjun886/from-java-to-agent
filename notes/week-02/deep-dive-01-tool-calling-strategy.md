# Agent Tool Calling 选型：Function Calling vs MCP vs REST

> 一句话：Function Calling 是内置工具箱，MCP 是通用接口协议，REST 是胶水层——选型取决于"工具谁来维护、被谁发现、怎么演进"。

## 关键对比 / 架构认知

| 维度 | Function Calling | MCP 协议 | REST API |
|------|-----------------|----------|----------|
| 发现机制 | 调用时注册（tools 参数随每次请求传入） | 运行时动态发现（`tools/list`） | 无标准发现（靠文档/API网关） |
| 耦合度 | 强（Tool 定义在 Agent 代码内） | 弱（Agent 只依赖协议，不依赖实现） | 中（依赖 URL + 契约） |
| 适合场景 | 固定工具集（计算器/天气） | 可插拔工具生态（企业系统集成） | 外部系统对接（已有 REST 服务） |
| 调用链路 | LLM → 函数直调 | LLM → MCP Client → MCP Server → 函数 | LLM → HTTP Client → REST 服务 |
| 版本演进 | 随 Agent 代码一起发布 | Server 独立升级，Client 无感知 | 需维护 API 版本兼容 |

**决策逻辑**：
- 工具不多、不变 → Function Calling 够用
- 工具来自多个团队、需独立部署 → MCP
- 对接遗留系统、已有 REST 接口 → REST 封装

## Java 映射 + 面试话术

**Java 类比**：
- Function Calling ≈ `@Service` 本地注入——编译期绑定，直接调用
- MCP ≈ **SPI 机制**（`META-INF/services`）——运行时发现实现类，调用方只依赖接口
- REST ≈ 跨系统 RPC 调用——独立部署，需要序列化/反序列化

**面试这么说**：
> "Tool Calling 选型我分成三个层次看。第一层是 Function Calling，跟 Spring 的依赖注入一样，工具在代码里注册，适合固定工具集。第二层是 MCP 协议，对标 Java 的 SPI 机制——MCP Server 可以独立部署、独立升级，Agent 通过协议动态发现工具，解耦最彻底。第三层是 REST 封装，对接已有的外部系统。实际项目中，我通常内部工具走 MCP，外部系统走 REST，简单场景直接用 Function Calling 降本。"
