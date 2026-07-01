package com.example.smartreport.model;

import java.util.Map;

/**
 * 索引统计信息 — 对应 Python 版 ingest.py 输出的统计报告。
 */
public class StatsResponse {

    private int totalDocuments;
    private Map<String, Integer> byTenant;
    private Map<String, Integer> bySource;
    private Map<String, Integer> byAccessLevel;

    public int getTotalDocuments() { return totalDocuments; }
    public void setTotalDocuments(int totalDocuments) { this.totalDocuments = totalDocuments; }

    public Map<String, Integer> getByTenant() { return byTenant; }
    public void setByTenant(Map<String, Integer> byTenant) { this.byTenant = byTenant; }

    public Map<String, Integer> getBySource() { return bySource; }
    public void setBySource(Map<String, Integer> bySource) { this.bySource = bySource; }

    public Map<String, Integer> getByAccessLevel() { return byAccessLevel; }
    public void setByAccessLevel(Map<String, Integer> byAccessLevel) { this.byAccessLevel = byAccessLevel; }
}
