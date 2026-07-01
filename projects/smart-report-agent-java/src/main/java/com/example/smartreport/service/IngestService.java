package com.example.smartreport.service;

import dev.langchain4j.data.document.Metadata;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.stream.Collectors;

/**
 * 文档摄入服务 — 读取 resources/data/ 下的 .txt 研报，向量化后存入 EmbeddingStore。
 * 对应 Python 版 ingest.py：Document → Embedding → ChromaDB。
 * <p>
 * 关键设计决策：
 * - 文件名编码 metadata: {tenant}_{topic}.txt（如 research_q3-report.txt → tenant=research）
 * - 文本中以 "CONFIDENTIAL" 开头的行为 confidential，其他为 public
 * - 角色权限默认: public 文档所有人可见，confidential 仅 engineer/manager 可见
 */
@Service
public class IngestService {

    private static final Logger log = LoggerFactory.getLogger(IngestService.class);

    // 文件名前缀 → tenant 映射
    // 对应 Python 版 _DOCS 元组列表的 tenant 字段
    private static final Set<String> TENANTS = Set.of("research", "trading", "compliance");
    private static final String ACCESS_CONFIDENTIAL = "confidential";
    private static final String ACCESS_PUBLIC = "public";
    private static final String SOURCE_TYPE = "txt_report";

    private final EmbeddingModel embeddingModel;
    private final EmbeddingStore<TextSegment> embeddingStore;

    // 缓存最近一次摄入的统计，供 GET /stats 使用
    // InMemoryEmbeddingStore 没有 count() API，这里用内存缓存
    private volatile Map<String, Object> lastStats;
    private final AtomicBoolean ingested = new AtomicBoolean(false);

    // Spring 构造器注入，不需要 @Autowired（单构造器自动装配）
    public IngestService(EmbeddingModel embeddingModel, EmbeddingStore<TextSegment> embeddingStore) {
        this.embeddingModel = embeddingModel;
        this.embeddingStore = embeddingStore;
        this.lastStats = Map.of("totalSegments", 0, "byTenant", Map.of(), "byAccessLevel", Map.of());
    }

    /**
     * 扫描 resources/data/ 目录，摄入所有 .txt 文档。
     * 返回摄入统计（文档数 + 分段统计）。
     */
    public Map<String, Object> ingestAll() {
        // 一次性摄入标记：避免重复摄入
        if (!ingested.compareAndSet(false, true)) {
            log.info("Documents already ingested, skipping.");
            return lastStats;
        }

        PathMatchingResourcePatternResolver resolver = new PathMatchingResourcePatternResolver();
        int totalSegments = 0;
        Map<String, Integer> byTenant = new HashMap<>();
        Map<String, Integer> byAccessLevel = new HashMap<>();

        // 先收集所有 TextSegment，再批量向量化
        List<TextSegment> allSegments = new ArrayList<>();

        try {
            Resource[] resources = resolver.getResources("classpath:data/*.txt");
            log.info("Found {} documents in resources/data/", resources.length);

            for (Resource resource : resources) {
                String filename = resource.getFilename();
                if (filename == null) continue;

                DocMeta meta = parseFilename(filename);
                if (meta == null) {
                    log.warn("Skipping file with unrecognized tenant prefix: {}", filename);
                    continue;
                }

                String content = readResource(resource);
                if (content == null || content.isBlank()) continue;

                // 用 \R 匹配任意换行符 (CRLF/CR/LF)，兼容 Windows/Linux/macOS
                String[] paragraphs = content.split("\\R\\s*\\R");
                for (String paragraph : paragraphs) {
                    String trimmed = paragraph.trim();
                    if (trimmed.isEmpty()) continue;

                    boolean isConfidential = trimmed.toUpperCase().startsWith("CONFIDENTIAL");
                    String accessLevel = isConfidential ? ACCESS_CONFIDENTIAL : ACCESS_PUBLIC;

                    Metadata docMeta = new Metadata();
                    docMeta.put("tenant", meta.tenant);
                    docMeta.put("access_level", accessLevel);
                    docMeta.put("role_intern", String.valueOf(!isConfidential));
                    docMeta.put("role_engineer", "true");
                    docMeta.put("role_manager", "true");
                    docMeta.put("source_type", SOURCE_TYPE);
                    docMeta.put("doc_id", meta.docId);
                    docMeta.put("timestamp", Instant.now().toString());

                    TextSegment segment = TextSegment.from(trimmed, docMeta);
                    allSegments.add(segment);

                    totalSegments++;
                    byTenant.merge(meta.tenant, 1, Integer::sum);
                    byAccessLevel.merge(accessLevel, 1, Integer::sum);
                }
            }

            // 批量向量化 + 批量写入
            if (!allSegments.isEmpty()) {
                List<Embedding> embeddings = embeddingModel.embedAll(allSegments).content();
                embeddingStore.addAll(embeddings, allSegments);
            }
        } catch (Exception e) {
            ingested.set(false); // 失败时重置标记，允许重试
            log.error("Ingestion failed", e);
            throw new RuntimeException("Document ingestion failed: " + e.getMessage(), e);
        }

        log.info("Ingestion complete: {} segments indexed", totalSegments);

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("totalSegments", totalSegments);
        stats.put("byTenant", byTenant);
        stats.put("byAccessLevel", byAccessLevel);
        this.lastStats = stats;
        return stats;
    }

    /**
     * 返回最近一次摄入的统计信息。
     * InMemoryEmbeddingStore 没有 count() 方法，用缓存替代。
     */
    public Map<String, Object> getStats() {
        return lastStats;
    }

    // ---- 内部方法 ----

    /**
     * 从文件名解析租户和文档 ID。
     * 例: "research-q3-report.txt" → tenant=research, docId=RESEARCH_RESEARCH_Q3_REPORT
     */
    private DocMeta parseFilename(String filename) {
        String baseName = filename.replaceAll("\\.txt$", "").toLowerCase();
        for (String tenant : TENANTS) {
            if (baseName.startsWith(tenant)) {
                String docId = tenant.toUpperCase() + "_" + baseName.replace("-", "_");
                return new DocMeta(tenant, docId);
            }
        }
        return null;
    }

    /**
     * 读取 classpath 资源为字符串。
     */
    private String readResource(Resource resource) {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(resource.getInputStream(), StandardCharsets.UTF_8))) {
            return reader.lines().collect(Collectors.joining("\n"));
        } catch (Exception e) {
            log.error("Failed to read resource: {}", resource.getFilename(), e);
            return null;
        }
    }

    // 内部 record: 文件名解析结果
    private record DocMeta(String tenant, String docId) {}
}
