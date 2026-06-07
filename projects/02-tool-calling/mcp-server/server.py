"""
MCP Server: Document Review Agent

基于 Qwen（DashScope API）的文档审查 MCP Server。
提供两个 Tool：
  - review_document: 审查任意文档文件
  - review_learning_plan: 专门审查学习计划文件
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from openai import AsyncOpenAI

logger = logging.getLogger("review-mcp-server")

# ── 路径与配置 ──────────────────────────────────────────────

PROJECT_ROOT = Path(os.environ.get("MCP_PROJECT_ROOT", Path.cwd()))
load_dotenv(PROJECT_ROOT / ".env")

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise RuntimeError("DASHSCOPE_API_KEY 未配置，请检查项目根目录的 .env 文件")

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen-max"

ALLOWED_SUFFIXES = {".md", ".txt", ".py", ".toml", ".yaml", ".yml", ".json", ".xml"}

# ── AsyncOpenAI Client ───────────────────────────────────────

client = AsyncOpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL,
    timeout=120.0,
)

# ── MCP Server ───────────────────────────────────────────────

server = Server("review-mcp-server")

SYSTEM_PROMPT = """你是一个资深 AI Agent 技术专家，拥有多年大模型应用开发和技术方案评审经验。

你的职责是审查技术文档、学习计划和技术方案，要求：
- 审查直击要害，不写废话，不写套话
- 每条改进建议必须是具体的、可操作的、可执行的
- 指出问题时给出「当前问题 → 建议改为 → 为什么这样更好」的三段式反馈
- 用中文输出，保持专业、简洁、犀利的风格"""


# ── Tool 注册 ────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="review_document",
            description="审查指定路径的文档（学习计划、技术方案、架构设计等），仅支持 .md/.txt/.py/.toml/.yaml/.json 等文本文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要审查的文档的绝对路径（仅支持纯文本文件，如 .md .txt .py 等）",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="review_learning_plan",
            description="专门审查学习计划文件（learning-plan.md），从知识点覆盖度、时间分配合理性、学习顺序科学性和项目产出竞争力四个维度进行评估",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """工具调用分发器"""
    if name == "review_document":
        return await _review_document(arguments["file_path"])
    elif name == "review_learning_plan":
        return await _review_learning_plan()
    else:
        raise ValueError(f"Unknown tool: {name}")


# ── Tool 实现 ────────────────────────────────────────────────

async def _review_document(file_path: str) -> list[TextContent]:
    """审查任意文档文件"""
    doc_path = Path(file_path).resolve()

    # 安全检查：路径必须在项目根目录或当前目录下
    allowed_root = PROJECT_ROOT.resolve()
    try:
        doc_path.relative_to(allowed_root)
    except ValueError:
        raise ValueError(
            f"❌ 路径越界：{file_path}\n"
            f"仅允许读取项目目录 ({allowed_root}) 内的文件。"
        )

    # 安全检查：仅允许文本文件
    if doc_path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError(
            f"❌ 不支持的文件类型：{doc_path.suffix}\n"
            f"仅支持：{', '.join(sorted(ALLOWED_SUFFIXES))}"
        )

    # 安全检查：禁止读取敏感文件
    forbidden_names = {".env", ".gitconfig", ".git-credentials", "credentials.json"}
    if doc_path.name in forbidden_names or ".git/" in str(doc_path):
        raise ValueError(f"❌ 安全限制：禁止读取敏感文件 {doc_path.name}")

    file_content = doc_path.read_text(encoding="utf-8")
    logger.info("review_document: %s (%d chars)", doc_path.name, len(file_content))

    # 截断过长内容（留足审查空间）
    max_chars = 20000
    if len(file_content) > max_chars:
        file_content = file_content[:max_chars] + "\n\n---\n⚠️ 文档过长，已截断至前 20000 字符。"

    # 构建审查 Prompt
    user_prompt = f"""请审查以下文档，按要求输出结构化的审查报告。

文档路径：{file_path}

审查维度：
1. **内容完整性** — 是否覆盖了该领域的关键知识点，有无重要遗漏
2. **结构合理性** — 文档结构/方案架构/学习路径是否合理，逻辑是否连贯
3. **技术准确性** — 是否有明显错误、过时信息或不准确的表述
4. **改进建议** — 具体的可操作的改进方案（每条用「当前问题 → 建议改为 → 为什么」格式）

--- 文档内容 ---
{file_content}
---

请输出完整的审查报告。"""

    return await _call_model(user_prompt)


async def _review_learning_plan() -> list[TextContent]:
    """专门审查 learning-plan.md"""
    plan_path = PROJECT_ROOT / "learning-plan.md"
    if not plan_path.exists():
        raise FileNotFoundError(f"❌ 学习计划文件不存在：{plan_path}")

    file_content = plan_path.read_text(encoding="utf-8")
    logger.info("review_learning_plan: %d chars", len(file_content))

    user_prompt = f"""请审查以下 AI Agent 转型学习计划。这是一个资深 Java 工程师用一个月时间转型 AI Agent 开发的学习计划。

审查维度：
1. **知识点覆盖度** — 对比 2026 年 AI Agent 面试市场的要求，是否有遗漏的关键知识点或技能
2. **时间分配合理性** — 四周的时间安排、每日学习时长是否科学，是否存在某些部分时间过紧或过松
3. **学习顺序是否科学** — 各模块的前置依赖关系是否正确，顺序是否需要调整
4. **项目产出是否足够支撑求职** — 4 个项目能否在简历中体现足够的竞争力，是否需要增加或调整

--- 学习计划内容 ---
{file_content}
---

请输出完整的审查报告。改进建议必须可操作、可执行，用「当前问题 → 建议改为 → 为什么」的格式。"""

    return await _call_model(user_prompt)


# ── LLM 调用 ─────────────────────────────────────────────────

async def _call_model(user_prompt: str) -> list[TextContent]:
    """调用 Qwen 模型，使用 AsyncOpenAI + 超时 + 日志"""
    logger.info("calling %s (%d chars prompt)", MODEL_NAME, len(user_prompt))
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=8192,
    )
    usage = response.usage
    logger.info(
        "model done — prompt: %d, completion: %d, total: %d tokens",
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens,
    )
    result = response.choices[0].message.content
    return [TextContent(type="text", text=result)]


# ── 入口 ─────────────────────────────────────────────────────

async def main():
    """启动 MCP Server（stdio 传输）"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
