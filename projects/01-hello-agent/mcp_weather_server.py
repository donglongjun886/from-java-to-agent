"""
Day 7 Part 2 — MCP 协议实战：将 get_weather + calculate 抽成独立 MCP Server

核心认知：
  之前的 tool_calling_demo.py：工具定义硬编码在 Agent 代码里
  MCP 方式：工具由独立 Server 进程暴露，Agent 通过 MCP Client 动态发现

对比：
  手写:   Agent 代码里写死 TOOLS = [get_weather, calculate]
  MCP:    Agent 连到这个 Server，自动获得 get_weather + calculate

运行方式:
  python mcp_weather_server.py          # 启动 Server（stdio transport）
  python mcp_weather_server.py --http   # 或 HTTP+SSE 模式（端口 8000）
"""

import sys
import asyncio
import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.server.stdio import stdio_server
import mcp.types as types

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

_sandbox = None

# ============================================================
# 工具函数 — 和之前完全一样
# ============================================================

def get_weather(city: str) -> str:
    """获取指定城市当前的天气信息"""
    db = {"杭州": "晴，28°C，湿度 65%", "北京": "多云，22°C，湿度 40%", "深圳": "雷阵雨，31°C，湿度 85%"}
    return db.get(city, f"{city}：暂无数据")


def calculate(expression: str) -> str:
    """执行数学计算，支持 + - * / ** 和括号"""
    import ast
    import operator as op

    allowed_ops = {
        ast.Add: op.add, ast.Sub: op.sub,
        ast.Mult: op.mul, ast.Div: op.truediv,
        ast.Pow: op.pow, ast.USub: op.neg,
    }

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            return allowed_ops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return allowed_ops[type(node.op)](_eval(node.operand))
        raise ValueError(f"不支持的操作: {type(node).__name__}")

    try:
        tree = ast.parse(expression, mode='eval')
        result = _eval(tree)
        return f"{expression} = {result}"
    except (ValueError, SyntaxError):
        return f"复杂表达式 '{expression}' 请使用 execute_code 工具执行"
    except Exception as e:
        return f"计算错误: {e}"

# ============================================================
# MCP Server 定义
# ============================================================

app = Server("weather-tool-server")

# ① 注册工具列表 — 等价于 tool_calling_demo.py 的 TOOLS = [...] 数组
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """MCP Client 连上来时，Server 告诉它'我有这些工具'"""
    return [
        types.Tool(
            name="get_weather",
            description="获取指定城市当前的天气信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如 杭州、北京、深圳"},
                },
                "required": ["city"],
            },
        ),
        types.Tool(
            name="calculate",
            description="执行数学计算，如加减乘除",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 '3.14 * 2 + 100'"},
                },
                "required": ["expression"],
            },
        ),
        types.Tool(
            name="execute_code",
            description="在受限沙箱中执行 Python 代码。仅支持安全内置函数（print, len, range, int, float, str, list, dict, sum, min, max, abs, round, sorted, enumerate, zip, map, filter）",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                    "timeout": {"type": "integer", "description": "最大执行时间（秒），默认 5", "default": 5},
                },
                "required": ["code"],
            },
        ),
    ]

# ② 注册工具执行逻辑 — 等价于 tool_calling_demo.py 的 TOOL_MAP
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """MCP Client 请求执行工具时，Server 在这里调对应的函数"""
    if name == "get_weather":
        result = get_weather(arguments["city"])
    elif name == "calculate":
        result = calculate(arguments["expression"])
    elif name == "execute_code":
        global _sandbox
        if _sandbox is None:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent-gateway"))
            from sandbox import SandboxExecutor
            _sandbox = SandboxExecutor()
        import json
        code = arguments.get("code", "")
        timeout_val = arguments.get("timeout", 5)
        result = json.dumps(_sandbox.execute(code, timeout_val), ensure_ascii=False)
    else:
        result = f"未知工具: {name}"

    return [types.TextContent(type="text", text=str(result))]

# ============================================================
# 启动入口
# ============================================================

async def run_stdio():
    """标准 MCP 模式：stdio transport，供 IDE（如 Claude Code）直接调用"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="weather-tool-server",
                server_version="1.0.0",
                capabilities=ServerCapabilities(tools={}),
            ),
        )


async def run_http():
    """HTTP+SSE 模式：供 Agent 应用通过 HTTP 调用（为 Week 2 项目A服务化做准备）"""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    import uvicorn

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())

    web_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ]
    )
    print("MCP Server 启动 → http://localhost:8000/sse")
    print("工具: get_weather, calculate")
    config = uvicorn.Config(web_app, host="0.0.0.0", port=8000, log_level="info")
    await uvicorn.Server(config).serve()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        asyncio.run(run_http())
    else:
        logger.info("MCP Server 启动 (stdio transport)")
        logger.info("工具: get_weather, calculate")
        asyncio.run(run_stdio())
