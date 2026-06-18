"""
评估层 — LLM-as-a-Judge 四维质量评分

独立于 Agent 编排层：评估器用独立的 LLM 调用，不和 Agent 共享模型实例，
避免「自己写的代码通过自己写的测试」。

面试可讲：外部验证 > 自评，评估器独立性是 Agent 工程质量的关键。
"""

import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

EVAL_SYSTEM = """你是一个严格的技术评审专家。对 AI 助手的回答按四维度打分 (1-5):

- accuracy: 事实是否正确
- relevance: 是否直接回答了用户问题
- completeness: 是否覆盖了关键要点
- format_quality: 格式是否清晰易读

严格输出 JSON（不要额外文字）:
{"accuracy":{"score":int,"reason":"..."},"relevance":{"score":int,"reason":"..."},"completeness":{"score":int,"reason":"..."},"format_quality":{"score":int,"reason":"..."},"overall":{"score":int,"summary":"..."}}"""

_eval_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)


def evaluate(question: str, answer: str) -> dict:
    """LLM-as-a-Judge 四维评估（用原始 OpenAI SDK，不走 LangChain 回调，避免污染流式输出）"""
    try:
        resp = _eval_client.chat.completions.create(
            model="deepseek-chat",
            temperature=0.1,
            timeout=15,
            messages=[
                {"role": "system", "content": EVAL_SYSTEM},
                {"role": "user", "content": f"用户问题: {question}\n\nAI 回答: {answer}"},
            ],
        )
        content = resp.choices[0].message.content.strip()
        content = re.sub(r'^```(?:json)?\s*\n', '', content)
        content = re.sub(r'\n```\s*$', '', content)
        content = content.strip()
        return json.loads(content)
    except Exception:
        return {"overall": {"score": 3, "summary": "评估失败，默认 3 分"}}
