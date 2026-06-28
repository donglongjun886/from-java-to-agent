"""
MCP Server: 学习方案 Reviewer
使用 qwen3.7-max 对学习计划/方案进行评审（覆盖度/优先级/深度/冗余四维度）
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
    app = Server("learning-review-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="review_learning_plan",
                description="对学习计划、复习方案或知识体系进行评审，从覆盖度、优先级、深度、冗余四个维度给出改进建议。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "需要评审的学习计划或方案完整内容",
                        },
                        "context": {
                            "type": "string",
                            "description": "可选：补充背景信息（目标岗位、时间约束、当前阶段等）",
                        },
                    },
                    "required": ["content"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "review_learning_plan":
            content = arguments["content"]
            context = arguments.get("context", "")

            prompt = f"""你是一位资深技术面试官和技术培训专家。请严格评审以下学习计划，按四个维度输出：

**1. 覆盖度** — 是否遗漏了高频考点？与目标岗位 JD 的匹配度如何？
**2. 优先级** — 时间分配是否合理？高频话题是否给了足够篇幅？
**3. 深度** — 每个模块的深度是否匹配目标级别（架构师/P7）？
**4. 冗余** — 有没有不必要的或优先级过低的内容？哪些可以砍掉或降级？

评审结束后，给出一个「按优先级排序的行动清单」。

{'背景信息：' + context if context else ''}

学习计划内容：
{content}

请用中文输出，结构清晰，直接给结论不客套。"""

            try:
                response = client.chat.completions.create(
                    model="qwen3.7-max",
                    messages=[
                        {"role": "system", "content": "你是一位资深技术面试官，擅长评估学习计划和面试准备方案的合理性。输出直接、务实，不废话。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                )
                result = response.choices[0].message.content
                return [types.TextContent(type="text", text=result)]
            except Exception as e:
                logger.error(f"API 调用失败: {e}")
                return [types.TextContent(type="text", text=f"评审失败: {e}")]

        return [types.TextContent(type="text", text=f"未知工具: {name}")]

    return app


async def main():
    app = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="learning-review-server",
                server_version="1.0.0",
                capabilities=ServerCapabilities(tools={}),
            ),
        )


if __name__ == "__main__":
    logger.info("Learning Review MCP Server 启动 (stdio)")
    asyncio.run(main())