package com.example.smartreport.model;

/**
 * 摄入请求 — 可选参数。
 * 当前实现自动扫描 resources/data/ 目录，此 DTO 为未来扩展预留（通过 API 上传文件等）。
 */
public class IngestRequest {

    private String directory;   // 自定义目录路径，不传则用默认 resources/data/

    public String getDirectory() {
        return directory;
    }

    public void setDirectory(String directory) {
        this.directory = directory;
    }
}
