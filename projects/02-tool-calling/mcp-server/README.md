# Review MCP Server

基于 **Qwen 3.7 Max**（DashScope API）的文档审查 MCP Server，用于审查学习计划、技术方案等文档。

## 功能

提供两个 MCP Tool：

| Tool | 功能 | 参数 |
|------|------|------|
| `review_document` | 审查任意文档（技术方案、架构设计等） | `file_path: str` — 文档路径 |
| `review_learning_plan` | 专门审查学习计划（learning-plan.md） | 无 |

审查维度包括：内容完整性、结构合理性、技术准确性、改进建议。

## 环境要求

- Python >= 3.12
- DashScope API Key（阿里云百炼）

## 配置

在项目根目录 `.env` 文件中配置：

```
DASHSCOPE_API_KEY=your-api-key
```

## 安装与运行

```bash
# 安装依赖
pip install mcp openai python-dotenv

# 启动 MCP Server（stdio 模式）
python server.py
```

## 在 Claude Code 中配置

在 Claude Code 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "review": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "DASHSCOPE_API_KEY": "your-api-key"
      }
    }
  }
}
```
