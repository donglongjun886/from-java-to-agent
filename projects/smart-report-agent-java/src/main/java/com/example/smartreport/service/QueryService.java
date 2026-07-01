package com.example.smartreport.service;

import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingMatch;
import dev.langchain4j.store.embedding.EmbeddingSearchRequest;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.filter.Filter;
import dev.langchain4j.store.embedding.filter.MetadataFilterBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 权限感知查询服务 — 租户隔离 + 角色 ACL + LLM 生成 + 引用溯源。
 * 对应 Python 版 query_engine.py 的 acl_query() 函数。
 * <p>
 * 核心流程（和 Python 版完全一致）:
 * 1. 接收查询 + 用户上下文 (tenant, role)
 * 2. 构建 metadata filter (where clause)
 * 3. 向量检索 top-k（带过滤）
 * 4. 组装 prompt（context + query）
 * 5. LLM 生成回答 + 引用列表
 * <p>
 * 面试要点: "权限在检索层做 metadata 预过滤，敏感文档不进入 context window。
 * 既防 prompt 注入泄露，又省 token（只送有权文档给 LLM）。"
 */
@Service
public class QueryService {

    private static final Logger log = LoggerFactory.getLogger(QueryService.class);

    // 合法的角色值（对应 Python 版 ALLOWED_ROLES）
    private static final Set<String> VALID_ROLES = Set.of("intern", "engineer", "manager");
    private static final double MIN_SCORE = 0.01;

    private final EmbeddingModel embeddingModel;
    private final EmbeddingStore<TextSegment> embeddingStore;
    private final ChatModel chatModel;

    public QueryService(EmbeddingModel embeddingModel,
                        EmbeddingStore<TextSegment> embeddingStore,
                        ChatModel chatModel) {
        this.embeddingModel = embeddingModel;
        this.embeddingStore = embeddingStore;
        this.chatModel = chatModel;
    }

    /**
     * 权限感知查询。
     *
     * @param query  用户查询文本
     * @param tenant 租户标识 ("research" | "trading" | "compliance")
     * @param role   角色 ("intern" | "engineer" | "manager")
     * @param topK   检索返回的最大文档数
     * @return 查询结果（answer + citations + 统计信息）
     */
    public QueryResult query(String query, String tenant, String role, int topK) {
        // Step 1: 参数校验
        if (query == null || query.isBlank()) {
            throw new IllegalArgumentException("query is required");
        }
        if (topK <= 0 || topK > 100) {
            throw new IllegalArgumentException("topK must be 1-100, got: " + topK);
        }
        if (tenant == null || tenant.isBlank()) {
            throw new IllegalArgumentException("tenant is required");
        }
        if (!tenant.matches("^[a-zA-Z0-9_-]+$")) {
            throw new IllegalArgumentException("Invalid tenant format: " + tenant);
        }
        if (role == null || !VALID_ROLES.contains(role)) {
            throw new IllegalArgumentException("Invalid role: " + role + ". Must be one of " + VALID_ROLES);
        }

        // Step 2: 构建 ACL where clause
        // 对应 Python 版 build_acl_where(): {"$and": [{"tenant": tenant}, {"role_XXX": true}]}
        // LangChain4j 用 Filter DSL 实现同样的效果
        Filter tenantFilter = MetadataFilterBuilder.metadataKey("tenant").isEqualTo(tenant);
        // isEqualTo 不支持 boolean，用 String "true" 匹配（Metadata 中存的是字符串）
        Filter roleFilter = MetadataFilterBuilder.metadataKey("role_" + role).isEqualTo("true");
        Filter aclFilter = tenantFilter.and(roleFilter);

        log.debug("ACL filter: tenant={}, role={}", tenant, role);

        // Step 3: 向量检索（带 metadata 过滤）
        // 对应 Python 版: collection.query(query_embeddings, where=where_clause, ...)
        Embedding queryEmbedding = embeddingModel.embed(query).content();
        EmbeddingSearchRequest searchRequest = EmbeddingSearchRequest.builder()
                .queryEmbedding(queryEmbedding)
                .maxResults(topK)
                .minScore(MIN_SCORE)     // 最低相似度阈值，过滤完全不相关的文档
                .filter(aclFilter)  // 权限过滤 — 最关键的一步
                .build();

        List<EmbeddingMatch<TextSegment>> matches = embeddingStore.search(searchRequest).matches();

        // Step 4: 无匹配文档 — 权限拒绝
        String filterLabel = "tenant=%s, role=%s".formatted(tenant, role);
        if (matches.isEmpty()) {
            log.info("No documents found for query with filter: {}", filterLabel);
            return QueryResult.empty(filterLabel);
        }

        // Step 5: 构建 context 和 citations
        // 对应 Python 版 context_parts 和 citations 列表
        StringBuilder context = new StringBuilder(topK * 512);
        List<Citation> citations = new ArrayList<>();

        for (int i = 0; i < matches.size(); i++) {
            EmbeddingMatch<TextSegment> match = matches.get(i);
            TextSegment segment = match.embedded();

            context.append("[").append(i + 1).append("] ").append(segment.text()).append("\n\n");

            Map<String, Object> meta = segment.metadata().toMap();
            citations.add(new Citation(
                    i + 1,
                    String.valueOf(meta.getOrDefault("source_type", "unknown")),
                    String.valueOf(meta.getOrDefault("doc_id", "unknown")),
                    String.valueOf(meta.getOrDefault("tenant", "unknown")),
                    String.valueOf(meta.getOrDefault("access_level", "unknown"))
            ));
        }

        // Step 6: 组装 prompt + LLM 生成
        // 和 Python 版 prompt 结构一致
        String prompt = """
                You are a financial assistant. Answer using ONLY the context provided in <context> tags.
                Cite source labels like [1], [2].

                <context>
                %s
                </context>

                <user_query>
                %s
                </user_query>
                """.formatted(context.toString().strip(), query);

        String answer;
        try {
            // ChatModel.chat(String) — LangChain4j 1.x 中 generate() 改名为 chat()
            answer = chatModel.chat(prompt);
        } catch (Exception e) {
            log.error("LLM generation failed, returning fallback message. tenant={}, role={}", tenant, role, e);
            answer = "(Oops, the system is temporarily unavailable. Please try again later.)";
        }

        log.info("Query result: {} docs retrieved, {} chars generated", matches.size(), answer.length());

        return new QueryResult(answer, citations, matches.size(), filterLabel);
    }

    // ---- 内部类型 ----

    public record QueryResult(String answer, List<Citation> citations, int retrievedCount, String filteredBy) {
        static QueryResult empty(String filterLabel) {
            return new QueryResult(
                    "No documents found in your access scope.",
                    List.of(),
                    0,
                    filterLabel
            );
        }
    }

    public record Citation(int index, String sourceType, String docId, String tenant, String accessLevel) {}
}
