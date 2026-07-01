# 检索权限控制：Pre-filtering为什么是唯一正确答案

> 权限控制必须前置到检索层——任何让敏感文档先进入再过滤的方案，本质上都是安全事件在前端掩耳盗铃。

## 关键对比 / 架构认知

RAG系统的权限控制有两种实现路径：Post-filtering（检索后过滤）和Pre-filtering（检索时过滤）。从工程角度，Pre-filtering是唯一可被安全审计接受的方案。

**Post-filtering的三个致命缺陷**。Post-filtering的真正风险是：①应用层代码bug可能绕过过滤导致敏感文档进入Prompt；②Top-K截断造成的召回衰减（排在前面的无权限文档被丢弃后，排在后面有权限的高相关文档被截断丢失）；③敏感文档残留于日志/请求体中。

**Pre-filtering的实现原理**：在向量检索的查询阶段，将ACL条件拼入检索DSL。以Milvus为例，检索语句大致为：`search(vector, filter="tenant_id==X AND (access_level>=2 OR role_editor==true)")`。向量数据库在执行ANN搜索时，实际采用In-filtering（搜索中过滤）：在HNSW图遍历过程中动态检查标量条件并跳过不满足的节点。结果集中只有授权文档，后续的LLM生成和上下文拼接都是安全的。

**权限模型设计**：metadata需要扁平化存储权限信息，避免复杂的关联查询。典型设计是每条文档metadata中携带布尔字段——`access_level: 2`（数字可做范围查询）、`role_admin: true`、`role_dept_finance: true`。检索时根据用户上下文组装Filter DSL，支持AND/OR逻辑组合。更优方案是存储文档所属的group_ids，检索时从外部IAM获取当前用户的归属组，用Filter DSL做 in 匹配，实现权限与文档元数据解耦。

**性能代价与安全审计要求**。权限过滤会引入10-20%的额外检索延迟，因为标量过滤需要在向量计算前做候选集裁剪。但这是必要的安全成本——SOC2和ISO27001审计明确要求：数据访问控制必须在数据访问层实现，不能依赖上层应用逻辑或LLM的输出过滤。Post-filtering在安全评估报告里是直接的不合格项。

## Java 映射 + 面试话术

**Java类比**：Pre-filtering就是数据库的Row-Level Security（RLS）——在SQL执行层面根据用户属性自动加WHERE条件，应用层无感知。Post-filtering就是`SELECT * FROM documents`加载到应用内存再按权限过滤——任何一个DBA和架构师都会告诉你这是安全灾难，代码里等于直接无视数据库的访问控制模型。

**面试话术**：「我早期在Spring Boot项目里做过数据权限，用的是MyBatis拦截器自动拼tenant_id条件，其实就是Pre-filtering的思路。在RAG系统里这个问题的答案更明确——权限过滤必须前置到向量检索的SQL/Filter层。原因很简单：Post-filtering的结果会进LLM的上下文，你过滤掉了文档但LLM已经'看到'了。SOC2审计时，评估师只看一个问题：你的权限控制是在数据访问层实现的，还是在应用层？回答后者直接pass。我们在metadata里存access_level和role_xxx布尔字段，检索时根据用户上下文拼Filter DSL，Milvus在扫描阶段就做候选集裁剪，结果集中没有一篇无权限文档。性能代价10%左右，但这是安全成本，不能省。」
