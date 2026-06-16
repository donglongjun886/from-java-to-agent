import json
import os
import sys
from openai import OpenAI

# ── 配置 ──
API_KEY = os.getenv("DASHSCOPE_API_KEY", "your-api-key-here")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen3.7-max"

# ── 读取 server.py ──
CODE_PATH = os.path.join(os.path.dirname(__file__), "server.py")
with open(CODE_PATH, "r", encoding="utf-8") as f:
    code_content = f.read()

# ── System Prompt ──
SYSTEM_PROMPT = "你是一个资深 AI Agent 技术专家和 Python 代码审查专家。你的职责是审查 MCP Server 代码。审查直击要害，不写废话。每条改进建议用「当前问题 → 建议改为 → 为什么这样更好」的三段式反馈。用中文输出。"

# ── User Prompt ──
USER_PROMPT = f"""请审查以下 MCP Server 代码。这是一个基于 mcp.server 库和 Qwen 3.7 Max 模型构建的文档审查 MCP Server。

审查维度：
1. 代码质量 — 结构是否清晰、type hints 是否完整、异常处理是否充分
2. MCP 协议使用 — Server/Tool 注册是否符合最佳实践
3. API 调用 — OpenAI SDK 使用是否正确，参数配置是否合理
4. 安全性 — API Key 处理、文件读取、路径遍历等安全问题
5. 生产就绪度 — 是否可以直接用于生产环境，还缺什么

请输出完整的审查报告，改进建议必须可操作、可执行。

--- 代码内容 ---
{code_content}
---"""

# ── 调用 API ──
try:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    result = response.choices[0].message.content
    print("=" * 70)
    print("  MCP Server 代码审查报告（审查模型：Qwen 3.7 Max）")
    print("=" * 70)
    print()
    print(result)
    print()
    print("=" * 70)
    print("  审查完成")
    print("=" * 70)

except Exception as e:
    print("=" * 70)
    print("  ERROR: API 调用失败")
    print("=" * 70)
    print(f"  异常类型: {type(e).__name__}")
    print(f"  异常信息: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 70)
    sys.exit(1)
