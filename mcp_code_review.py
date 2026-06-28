"""
MCP Server: Code Reviewer
使用 qwen3.7-max 对代码进行审查（正确性/安全性/性能/可读性/最佳实践五维度）
"""

import sys
import asyncio
import logging
from os import getenv
from pathlib import Path
from dotenv import load_dotenv

from openai import OpenAI
from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.server.stdio import stdio_server
import mcp.types as types

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

DASHSCOPE_API_KEY = getenv("DASHSCOPE_API_KEY")


def create_server() -> Server:
    client = OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    app = Server("code-review-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="review_code",
                description="对代码进行审查，检查正确性、安全性、性能、可读性、最佳实践，每个发现标注严重程度。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "需要审查的代码全文",
                        },
                        "language": {
                            "type": "string",
                            "description": "编程语言，如 python, java, javascript, go 等",
                        },
                        "focus": {
                            "type": "string",
                            "description": "可选：重点关注方向（安全、性能、可读性、架构），不填则全面审查",
                        },
                    },
                    "required": ["code", "language"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "review_code":
            code = arguments["code"]
            language = arguments.get("language", "")
            focus = arguments.get("focus", "")

            focus_section = (
                f"\n**重点关注**：{focus}，请在这个方向上深入分析。"
                if focus
                else ""
            )

            prompt = f"""你是一位资深代码审查专家。请审查以下 {language} 代码。

## 审查维度

1. **正确性** — 逻辑是否有缺陷？边界条件是否覆盖？是否有潜在 bug？
2. **安全性** — 是否有注入风险、敏感信息泄露、权限问题？
3. **性能** — 是否有不必要的计算、内存浪费、IO 瓶颈？
4. **可读性** — 命名是否准确、结构是否清晰、注释是否必要？
5. **最佳实践** — 是否符合 {language} 的惯用写法和业界共识？
{focus_section}

## 输出格式

对每个发现标注严重程度，并给出改进建议：

- 🔴 **严重** — 必须修复，会导致 bug 或安全事故
- 🟡 **建议** — 应该改进，影响代码质量或可维护性
- 🟢 **优化** — 锦上添花，让代码更好但非必须

最后给出一个「修复优先级排序」的总结。

代码：
```{language}
{code}
```

用中文输出，直接给结论。"""

            try:
                response = client.chat.completions.create(
                    model="qwen3.7-max",
                    messages=[
                        {"role": "system", "content": "你是一位资深代码审查专家，擅长发现代码中的正确性、安全性、性能和可读性问题。输出直接、务实，按严重程度分类。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                )
                result = response.choices[0].message.content
                return [types.TextContent(type="text", text=result)]
            except Exception as e:
                logger.error(f"API 调用失败: {e}")
                return [types.TextContent(type="text", text=f"审查失败: {e}")]

        return [types.TextContent(type="text", text=f"未知工具: {name}")]

    return app


async def main():
    app = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="code-review-server",
                server_version="1.0.0",
                capabilities=ServerCapabilities(tools={}),
            ),
        )


if __name__ == "__main__":
    logger.info("Code Review MCP Server 启动 (stdio)")
    asyncio.run(main())