package com.example.smartreport.model;

import jakarta.validation.constraints.NotBlank;

/**
 * 权限感知查询请求 — 携带用户上下文（租户 + 角色）。
 * 生产环境替换为 JWT 解析，当前用请求参数模拟。
 * 对应 Python 版 MOCK_SESSIONS 的三元组 (user_id, tenant, role)。
 */
public class QueryRequest {

    @NotBlank(message = "query is required")
    private String query;
    private String tenant;    // "research" | "trading" | "compliance"
    private String role;      // "intern" | "engineer" | "manager"
    private int topK = 5;

    public QueryRequest() {
    }

    public QueryRequest(String query, String tenant, String role) {
        this.query = query;
        this.tenant = tenant;
        this.role = role;
    }

    public String getQuery() { return query; }
    public void setQuery(String query) { this.query = query; }

    public String getTenant() { return tenant; }
    public void setTenant(String tenant) { this.tenant = tenant; }

    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }

    public int getTopK() { return topK; }
    public void setTopK(int topK) { this.topK = topK; }
}
