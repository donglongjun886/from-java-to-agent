package com.example.smartreport.controller;

import com.example.smartreport.model.IngestRequest;
import com.example.smartreport.model.QueryRequest;
import com.example.smartreport.model.QueryResponse;
import com.example.smartreport.model.StatsResponse;
import com.example.smartreport.service.IngestService;
import com.example.smartreport.service.QueryService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * REST Controller — 暴露企业 RAG 查询接口。
 * 对应 Python 版 query_engine.py 的 __main__ 演示逻辑，
 * 但不 hardcode 6 个场景，改为 HTTP 接口供外部调用。
 */
@RestController
@RequestMapping("/api/rag")
public class RagController {

    private static final Logger log = LoggerFactory.getLogger(RagController.class);

    private final IngestService ingestService;
    private final QueryService queryService;

    public RagController(IngestService ingestService, QueryService queryService) {
        this.ingestService = ingestService;
        this.queryService = queryService;
    }

    /**
     * POST /api/rag/ingest — 触发文档摄入。
     * 对应 Python: python ingest.py
     */
    @PostMapping("/ingest")
    public Map<String, Object> ingest(@RequestBody(required = false) IngestRequest request) {
        log.info("Ingest triggered");
        Map<String, Object> stats = ingestService.ingestAll();
        Map<String, Object> result = new LinkedHashMap<>(stats);
        result.put("status", "ok");
        return result;
    }

    /**
     * POST /api/rag/query — 权限感知查询。
     * 请求体携带 query + tenant + role，返回 answer + citations。
     * 对应 Python: acl_query(collection, query_text, user_id)
     *
     * 注意：生产环境中 tenant/role 应从认证上下文（SecurityContext/JWT）获取，
     * 不可直接信任客户端传入。当前学习项目为简化演示，直接使用请求参数。
     */
    @PostMapping("/query")
    public QueryResponse query(@Valid @RequestBody QueryRequest request) {
        // 输入校验：query 必填
        if (request.getQuery() == null || request.getQuery().isBlank()) {
            throw new IllegalArgumentException("query is required");
        }

        log.info("Query: tenant={}, role={}, topK={}, query='{}'",
                request.getTenant(), request.getRole(), request.getTopK(),
                request.getQuery().length() > 50 ? request.getQuery().substring(0, 50) + "..." : request.getQuery());

        QueryService.QueryResult result = queryService.query(
                request.getQuery(), request.getTenant(), request.getRole(), request.getTopK());

        // 转换内部类型到 DTO
        List<QueryResponse.Citation> citations = result.citations().stream()
                .map(c -> new QueryResponse.Citation(
                        c.index(), c.sourceType(), c.docId(), c.tenant(), c.accessLevel()))
                .toList();

        return new QueryResponse(
                result.answer(), citations, result.retrievedCount(), result.filteredBy());
    }

    /**
     * GET /api/rag/stats — 索引统计。
     * 对应 Python 版 ingest.py 输出的统计信息。
     */
    @GetMapping("/stats")
    @SuppressWarnings("unchecked")
    public StatsResponse stats() {
        Map<String, Object> raw = ingestService.getStats();

        StatsResponse response = new StatsResponse();
        Object totalObj = raw.getOrDefault("totalSegments", 0);
        response.setTotalDocuments(totalObj instanceof Number n ? n.intValue() : 0);

        Object tenantObj = raw.getOrDefault("byTenant", Map.of());
        response.setByTenant(tenantObj instanceof Map<?, ?> m
                ? (Map<String, Integer>) m : Map.of());

        Object sourceObj = raw.getOrDefault("bySource", Map.of());
        response.setBySource(sourceObj instanceof Map<?, ?> m
                ? (Map<String, Integer>) m : Map.of());

        Object aclObj = raw.getOrDefault("byAccessLevel", Map.of());
        response.setByAccessLevel(aclObj instanceof Map<?, ?> m
                ? (Map<String, Integer>) m : Map.of());
        return response;
    }
}
