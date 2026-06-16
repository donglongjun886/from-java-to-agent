"""
Agent 网关平台 (Project A) — 多工具 Agent 网关

架构:
  Client (HTTP/SSE) → FastAPI Gateway → LangGraph Agent → MCP Tools
                                              ↓
                                         Evaluator (质量门禁)
                                              ↓
                                         Feedback Loop (重试)

目录结构:
  server.py        — 网关入口
  agent_graph.py   — LangGraph 编排（LLM + Tool 路由）
  tools/           — MCP 工具 Server（可独立部署）
  evaluator.py     — LLM-as-a-Judge 评估
"""

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI(title="Agent Gateway", version="0.1.0")


@app.get("/")
def root():
    return {
        "service": "Agent Gateway",
        "layers": ["Route", "Agent Graph", "Tools", "Evaluator", "Feedback Loop"],
    }


@app.get("/chat")
def chat(msg: str = Query(..., description="用户消息")):
    """对话入口"""
    return {"reply": f"[Agent Gateway] 收到: {msg}"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("Agent Gateway → http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
