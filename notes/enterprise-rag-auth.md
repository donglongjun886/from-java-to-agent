# 企业级 RAG 权限与多租户

## 1. 为什么权限是 RAG 的第一道防线

在企业场景中，RAG 系统的权限控制不是"锦上添花"的安全功能，而是直接影响系统能否上线的硬约束。三重压力叠加：

| 约束维度 | 典型场景 | 失败的代价 |
|----------|---------|-----------|
| **安全合规** | 医疗数据受HIPAA约束、金融数据受PCI-DSS管制 | 数据泄露 = 法律诉讼 + 吊销牌照 |
| **成本控制** | 每次检索把无关文档喂给LLM，token消耗随文档量线性增长 | 100万文档不加过滤，每次查询多花$0.5-2 |
| **业务正确性** | 客服Agent查到其他租户的定价策略，给客户报了对手的价格 | 客户信任崩塌，合同解约 |

一句话：**RAG没有权限，就不是企业级系统，只是demo**。

## 2. 三层权限模型

```
查询请求
  │
  ├─ 第一层：租户级（tenant_id）
  │   作用：多租户SaaS数据隔离
  │   实现：检索时 where={"tenant_id": request.tenant_id}
  │   粒度：整个租户的数据边界
  │
  └─ 第二层：文档级（access_level + allowed_roles）
      作用：同一租户内不同角色看到不同文档
      实现：检索时 where={"allowed_roles": {"$in": user.roles}}
      粒度：单篇文档的可见性

  一条执行原则：所有权限条件必须在检索阶段通过 metadata filter 执行，不得延后到生成阶段
```

### 租户级隔离的实现

```python
# ChromaDB 写入时注入 tenant_id
collection.add(
    documents=[doc_text],
    metadatas=[{
        "tenant_id": "tenant_001",
        "doc_id": "doc_abc",
        "access_level": 3,
        "allowed_roles": ["admin", "analyst", "viewer"],
    }],
    ids=[doc_uid],
)

# 检索时强制带上租户过滤
def search(user_query: str, tenant_id: str, user_roles: list[str]):
    return collection.query(
        query_texts=[user_query],
        n_results=10,
        where={
            "$and": [
                {"tenant_id": tenant_id},                    # 第一层
                {"allowed_roles": {"$in": user_roles}},      # 第二层
            ]
        },
    )
```

### 文档级权限的常见模型

| 模型 | 适用场景 | metadata 字段设计 |
|------|---------|------------------|
| **角色映射** | B2B SaaS（每个租户角色固定） | `allowed_roles: ["admin", "editor"]` |
| **ACL列表** | 文档协作（Google Docs） | `allowed_user_ids: ["u1", "u2"]` |
| **密级标签** | 军工/政务 | `classification: "top_secret"` + `clearance_level` 数值比较 |
| **部门+岗位** | 大型企业OA | `dept_id: "dept_101"` + `position_level: "P6+"` |

## 3. 权限校验的位置决策

**核心原则：检索阶段过滤，不在生成阶段补救。**

```
❌ 错误做法（生成后校验）：
  检索全部文档 → LLM 生成回答 → 检查回答是否含越权内容 → 拦截

✅ 正确做法（检索前过滤）：
  带权限条件检索 → 仅有权文档进入向量计算 → LLM基于合规文档生成
```

### 为什么生成阶段校验不可行

| 问题 | 说明 |
|------|------|
| **token浪费** | 越权文档已经消耗了上下文窗口，钱已经花出去了 |
| **信息泄漏** | LLM生成的内容可能隐式包含了越权文档的信息，无法可靠检测 |
| **幻觉放大** | 给LLM喂了它本不该看到的信息，即使用正则过滤回答，LLM已经"学到了"不该学的内容 |
| **不可审计** | 生成阶段的校验是事后补救，审计日志无法证明"LLM在生成时没有参考越权文档" |

攻击视角：如果你能用精心构造的查询（prompt injection）让LLM回答越权内容，生成阶段的简单正则过滤是拦不住的。唯一安全的方式是让LLM根本看不到不该看的文档。

## 4. 实现方案对比

| 方案 | 实现方式 | 隔离强度 | 检索性能 | 灵活性 | 运维成本 |
|------|---------|---------|---------|--------|---------|
| **ChromaDB where clause** | metadata过滤，单Collection | ★★★ 逻辑隔离 | ★★★★★ 无额外开销 | ★★★★ 条件组合灵活，但操作符有限 | ★★★★★ 最低 |
| **独立Collection** | 每租户一个Collection | ★★★★★ 物理隔离 | ★★★★ 单租户查询优秀，跨租户需聚合 | ★★ 跨租户查询困难 | ★★ 管理N个Collection |
| **应用层代理过滤** | 检索后人工过滤 | ★ 仅依赖代码逻辑 | ★ 检索大量无用文档 | ★★★★★ 任意规则 | ★★★ 需维护过滤层 |

**推荐方案：ChromaDB where clause 作为默认选择。**

- 物理隔离（独立Collection）留给极端合规场景（金融/医疗），ChromaDB的metadata过滤在生产环境已足够可靠
- 应用层代理过滤仅作为兜底审计（记录"如果不过滤会查到什么"用于安全审计），不作为主要防线
- metadata过滤结合**请求级拦截器**：在API入口就注入tenant_id，确保业务代码不可能"忘记"带过滤条件

```python
# 请求级拦截器：在检索入口强制注入，杜绝遗漏
class RAGQueryContext:
    """每次检索请求的上下文，由中间件注入，业务代码不允许手动构造"""
    tenant_id: str
    user_id: str
    user_roles: list[str]
    clearance_level: int = 0

    def build_where_clause(self) -> dict:
        # 注意：access_level 保留为扩展点，当前未在查询中强制生效。
        # 启用在 build_where_clause() 中追加如下条件即可：
        #   {"access_level": {"$lte": self.clearance_level}}
        return {
            "$and": [
                {"tenant_id": self.tenant_id},
                {"allowed_roles": {"$in": self.user_roles}},
            ]
        }
```

## 5. 与 Tool 级 RBAC 的区别

这是两条独立的权限维度，常被混淆：

| 维度 | 检索权限（数据层） | Tool权限（功能层） |
|------|-------------------|-------------------|
| **控制什么** | 能看到哪些文档/数据 | 能调用哪些Agent工具 |
| **判断时机** | 检索阶段（向量查询where条件） | Agent编排阶段（Tool注册时） |
| **典型场景** | 销售A不能看销售B的客户合同 | 普通客服不能调用"退款审批"Tool |
| **错误后果** | 数据泄露 | 越权操作 |
| **Java类比** | `@RowLevelSecurity` / 行级安全 | `@PreAuthorize("hasRole('ADMIN')")` |
| **粒度** | 单条chunk/文档 | 单个Tool/API |

两者必须独立设计、独立校验。一个用户可能：
- 有权限调用"合同查询"Tool（功能层通过），但只能查自己部门的合同（数据层过滤）
- 没有权限调用"系统配置"Tool（功能层拒绝），即使他有admin角色能看到配置文档（数据层有权限也没用）

## 6. Java 类比

| Java 后端概念 | RAG 权限对应 | 相似点 |
|-------------|------------|--------|
| **Spring AbstractRoutingDataSource** | 租户级 metadata 过滤 | 根据请求上下文动态路由到不同数据源/过滤条件 |
| **`@PreAuthorize` + SpEL** | 文档级 `allowed_roles` 过滤 | 方法执行前基于表达式做权限判断 |
| **Hibernate `@Filter`** | ChromaDB where clause | ORM层面自动追加过滤条件，业务代码无感知 |
| **MyBatis 多租户插件** | 请求级拦截器注入 `tenant_id` | 拦截SQL/查询，自动追加租户条件 |
| **Spring Security Filter Chain** | RAG请求上下文中间件 | 在请求入口处完成身份提取和权限上下文构建 |
| **SaaS平台的Schema/Tenant隔离** | 物理vs逻辑隔离选择 | 独立数据库 vs 共享表+字段过滤的权衡完全一致 |

多租户数据隔离在Java生态中已经有成熟的模式。RAG系统的权限设计本质上是在向量数据库上复现这些模式——只是把SQL的WHERE子句换成了向量数据库的metadata filter。

## 7. 面试要点

你需要能够清晰回答以下三个核心问题：

**Q1: 为什么不直接在LLM生成回答后再做权限校验？**

三个致命缺陷：（1）越权文档已经消耗了token预算，钱花了；（2）LLM可能已经在生成中隐式使用了越权信息，事后过滤不可靠；（3）从安全审计角度，你无法证明"生成时没有参考越权文档"。正确的架构是检索前就切断越权路径。

**Q2: 三层权限模型可以合并成一层吗？**

不能。租户级、文档级、检索级解决的是不同层次的问题——租户级是数据边界（SaaS隔离），文档级是业务规则（同一租户内的权限差异），检索级是实现手段（确保前两层在向量检索时生效）。如果合并，要么隔离不充分（租户间可能串数据），要么粒度过粗（租户内无法做角色区分）。

**Q3: metadata过滤和独立Collection怎么选？**

默认用metadata过滤。独立Collection只在以下情况才需要：法规要求物理隔离（金融、医疗）；租户数据量极大，混在一起会导致检索性能下降。绝大多数B2B SaaS场景下，metadata过滤的隔离强度已经足够，且运维成本远低于管理成百上千个Collection。这和Java中选择"共享数据库+tenant_id字段"而非"每租户独立数据库"的权衡逻辑完全一致。
