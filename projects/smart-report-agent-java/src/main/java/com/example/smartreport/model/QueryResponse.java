package com.example.smartreport.model;

import java.util.List;

/**
 * 查询响应 — 包含 LLM 回答、引用列表、统计信息。
 * 对应 Python 版 acl_query() 的返回字典结构。
 */
public class QueryResponse {

    private String answer;
    private List<Citation> citations;
    private int retrievedCount;
    private String filteredBy;

    public QueryResponse() {
    }

    public QueryResponse(String answer, List<Citation> citations, int retrievedCount, String filteredBy) {
        this.answer = answer;
        this.citations = citations;
        this.retrievedCount = retrievedCount;
        this.filteredBy = filteredBy;
    }

    public String getAnswer() { return answer; }
    public void setAnswer(String answer) { this.answer = answer; }

    public List<Citation> getCitations() { return citations; }
    public void setCitations(List<Citation> citations) { this.citations = citations; }

    public int getRetrievedCount() { return retrievedCount; }
    public void setRetrievedCount(int retrievedCount) { this.retrievedCount = retrievedCount; }

    public String getFilteredBy() { return filteredBy; }
    public void setFilteredBy(String filteredBy) { this.filteredBy = filteredBy; }

    /**
     * 引用记录 — 可审计的来源追踪。
     * 对应 Python 版 citations 列表中的 dict。
     */
    public static class Citation {
        private int index;
        private String sourceType;
        private String docId;
        private String tenant;
        private String accessLevel;

        public Citation() {}

        public Citation(int index, String sourceType, String docId, String tenant, String accessLevel) {
            this.index = index;
            this.sourceType = sourceType;
            this.docId = docId;
            this.tenant = tenant;
            this.accessLevel = accessLevel;
        }

        public int getIndex() { return index; }
        public void setIndex(int index) { this.index = index; }

        public String getSourceType() { return sourceType; }
        public void setSourceType(String sourceType) { this.sourceType = sourceType; }

        public String getDocId() { return docId; }
        public void setDocId(String docId) { this.docId = docId; }

        public String getTenant() { return tenant; }
        public void setTenant(String tenant) { this.tenant = tenant; }

        public String getAccessLevel() { return accessLevel; }
        public void setAccessLevel(String accessLevel) { this.accessLevel = accessLevel; }
    }
}
