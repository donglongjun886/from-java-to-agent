# LLM 可观测性：Langfuse vs 传统 APM

> 传统 APM 看延迟/错误/吞吐，Agent 可观测性要在此基础上增加三个新维度：Token 经济学、Tool 调用链、Prompt 版本管理。

## 关键认知：Agent 的观测维度比微服务多一倍

**传统 APM（SkyWalking/Prometheus/Grafana）观测什么**：
- RED 指标：Rate（QPS）、Errors（错误率）、Duration（P99 延迟）
- 分布式链路追踪（Trace）：请求在微服务间的调用链

**Agent 系统还需要观测什么**：

| 新维度 | 为什么重要 | 典型指标 |
|--------|-----------|---------|
| Token 经济学 | Token 是最大的可变成本，LLM 调用比服务器贵得多 | 单次请求 Token 消耗、缓存命中率、token/元 成本 |
| Tool 调用链 | Tool 调用成功/失败直接影响 Agent 输出质量 | Tool 调用次数、成功率、耗时分布、fallback 触发率 |
| Prompt 版本 | Prompt 是 Agent 的"源代码"，改了效果要能追溯 | Prompt 版本 → 成功率 → 对话质量评分 |
| LLM 行为 | 模型不报错 ≠ 行为正确（幻觉、拒答、格式异常） | 幻觉率、拒答率、输出格式合规率 |

**Langfuse Trace vs OpenTelemetry Trace**：
- OpenTelemetry Span 是用 `operation_name` 描述功能，Langfuse Span 是用 prompt/response/tokens 描述 LLM 交互
- OTel 关注"调用耗时"，Langfuse 关注"这次生成的 Token 是上一次的 3 倍，为什么？"
- 两者可以集成：Langfuse 的 trace 导出到 OTel Collector，统一在 Grafana 展示

## Java 映射 + 面试话术

**Java 类比**：
- Langfuse Trace ≈ **SkyWalking Agent 探针**——自动埋点，无侵入采集
- Token 成本监控 ≈ **数据库连接池的慢 SQL 监控**——最贵的资源需要最细粒度的追踪
- Prompt 版本管理 ≈ **配置中心（Nacos/Apollo）的配置版本追溯**——改了哪版、效果怎样、谁改的

**面试这么说**：
> "Agent 可观测性不能只靠传统 APM。除了 QPS/P99/错误率这些基础指标，我还需要三个新维度。第一是 Token 经济学，类比数据库的慢 SQL 监控——LLM 调用是 Agent 系统最贵的开销，需要按请求级别追踪 Token 消耗和成本。第二是 Tool 调用链，Tool 调用的成功率直接影响 Agent 输出质量，需要跟 APM span 一样有完整的调用拓扑。第三是 Prompt 版本管理，Prompt 改了效果要能追溯，跟配置中心做版本回滚一个道理。技术选型上我倾向 Langfuse，它跟 OpenTelemetry 能互通，不是替代关系是互补关系。"
