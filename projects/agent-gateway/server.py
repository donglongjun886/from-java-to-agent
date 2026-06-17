"""
Agent 网关平台 — FastAPI 入口

端点:
  GET  /                 服务信息
  POST /chat             同步对话
  POST /chat/stream      SSE 流式对话
  GET  /stats            可观测统计
  GET  /health           健康检查

启动:
  python server.py
  然后打开 http://localhost:9090/docs 看 Swagger
"""

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import uvicorn

from agent_graph import run_chat, run_chat_stream, stats, close_mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：关闭时清理 MCP 子进程"""
    yield
    await close_mcp()


app = FastAPI(title="Agent Gateway", version="0.2.0", lifespan=lifespan)

# ============================================================
# Pydantic 模型
# ============================================================

class ChatRequest(BaseModel):
    msg: str = Field(..., description="用户消息", min_length=1, max_length=4096)
    temperature: float = Field(default=0.3, ge=0, le=2)


class ChatResponse(BaseModel):
    reply: str
    evaluation: str | None = None
    time_ms: float
    stats: dict


class HealthResponse(BaseModel):
    status: str
    layers: list[str]


# ============================================================
# 端点
# ============================================================

@app.get("/")
def root() -> HealthResponse:
    return HealthResponse(
        status="ok",
        layers=["Route", "Security Guard", "Agent Graph", "MCP Client", "Evaluator"],
    )


@app.post("/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    """同步对话 — 等 Agent 完整回复后返回"""
    result = await run_chat(req.msg, temperature=req.temperature)
    return ChatResponse(**result)


@app.post("/chat/stream", response_class=EventSourceResponse)
async def chat_stream(req: ChatRequest):
    """SSE 流式对话 — 逐 token 推送"""
    async for chunk in run_chat_stream(req.msg, temperature=req.temperature):
        yield ServerSentEvent(data=chunk, event="reply")
    yield ServerSentEvent(data="[DONE]", event="done")


@app.get("/stats")
def get_stats():
    return stats.snapshot()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("Agent Gateway → http://localhost:9090/docs")
    uvicorn.run(app, host="0.0.0.0", port=9090)
