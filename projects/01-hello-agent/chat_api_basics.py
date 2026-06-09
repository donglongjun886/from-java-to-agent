"""
Day 3 — Chat Completions API 基础实验

三个实验逐层递进，理解协议层的工作方式：
  实验1: 非流式调用 → 拆解完整 response JSON 结构
  实验2: stream=True → 观察 SSE 流的 chunk 形态 (delta vs message)
  实验3: temperature 对比 → 同一个 prompt 在两个温度下的输出差异
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"


def sep(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


# ============================================================
# 实验1: 非流式调用 — 拆解 response 结构
# ============================================================
sep("实验1: 非流式调用 + response 结构拆解")

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "用中文回答，回复控制在两句话以内。"},
        {"role": "user", "content": "用一句话解释什么是 API"},
    ],
    temperature=0.3,
    max_tokens=200,
)

# 1.1 顶层字段
print("【response 顶层字段】")
print(f"  id:                {response.id}")
print(f"  object:            {response.object}")          # 固定值 "chat.completion"
print(f"  created:           {response.created}")         # Unix 时间戳
print(f"  model:             {response.model}")           # 实际使用的模型
print(f"  system_fingerprint: {response.system_fingerprint}")  # 后端配置指纹
print(f"  choices 数量:       {len(response.choices)}")       # 通常=1 (n参数控制)

# 1.2 choice 内部结构
choice = response.choices[0]
print(f"\n【choice 内部结构】")
print(f"  index:              {choice.index}")
print(f"  finish_reason:      {choice.finish_reason}")    # stop / length / content_filter
print(f"  message.role:       {choice.message.role}")     # "assistant"
print(f"  message.content:    {choice.message.content}")

# 1.3 usage (token 用量) — 这是算钱的关键字段
usage = response.usage
print(f"\n【usage — Token 用量】")
print(f"  prompt_tokens:      {usage.prompt_tokens}")       # 输入消耗
print(f"  completion_tokens:  {usage.completion_tokens}")    # 输出消耗
print(f"  total_tokens:       {usage.total_tokens}")
# DeepSeek V4 定价 (每百万 token): 输入 ¥2 / 输出 ¥8
cost_input = usage.prompt_tokens / 1_000_000 * 0.27
cost_output = usage.completion_tokens / 1_000_000 * 1.10
print(f"  预估费用:            ${cost_input + cost_output:.6f}")

# 1.4 完整 JSON (方便对照文档字段)
print(f"\n【完整 response JSON (前 500 字符)】")
print(json.dumps(response.model_dump(), indent=2, ensure_ascii=False)[:500])
print("  ...")


# ============================================================
# 实验2: 流式调用 — 观察 SSE chunk 结构
# ============================================================
sep("实验2: stream=True — SSE 流式 chunk 拆解")

stream = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "user", "content": "用三句话介绍杭州"}
    ],
    max_tokens=200,
    stream=True,
)

chunk_count = 0
full_content = ""

for chunk in stream:
    chunk_count += 1
    delta = chunk.choices[0].delta

    # 前 3 个 chunk 打印完整结构，用来观察
    if chunk_count <= 3:
        print(f"\n--- chunk #{chunk_count} 完整结构 ---")
        print(json.dumps(chunk.model_dump(), indent=2, ensure_ascii=False)[:400])
        print("  ...")

    # 逐 token 打印内容 (打字机效果)
    if delta.content:
        print(delta.content, end="", flush=True)
        full_content += delta.content

    # 最后一个 chunk 的 finish_reason
    if chunk.choices[0].finish_reason:
        print(f"\n\n【第 {chunk_count} 个 chunk (最后一个)】")
        print(f"  finish_reason: {chunk.choices[0].finish_reason}")
        if hasattr(chunk, "usage") and chunk.usage:
            print(f"  usage: prompt={chunk.usage.prompt_tokens}, "
                  f"completion={chunk.usage.completion_tokens}")

print(f"\n\n总 chunk 数: {chunk_count}")
print(f"完整回复长度: {len(full_content)} 字符")

# 关键认知: 流式时每个 chunk 的 delta.content 是增量文本片段
#           非流式时 choice.message.content 是一次性返回的完整文本
#           流式回复的 token 用量通常只在最后一个 chunk 返回 (DeepSeek 行为)


# ============================================================
# 实验3: temperature 对比 — 确定性 vs 随机性
# ============================================================
sep("实验3: temperature=0 vs temperature=1.5 输出对比")

prompt = "用一句话形容'春天'，要有画面感。"

for temp in [0.0, 1.5]:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        max_tokens=100,
    )
    print(f"  temperature={temp}: {response.choices[0].message.content}")

# 预期现象:
#   temp=0:   输出稳定、直白、每次几乎一样  (贪婪解码, 适合代码/分类/事实问答)
#   temp=1.5: 输出更发散、用词更丰富/跳跃     (适合创意写作/头脑风暴)
# 生产建议: 代码生成用 0~0.2, 对话用 0.5~0.7, 创意用 0.8+
#           通常调 temperature 就够了, top_p 作为备选

print("\n" + "="*60)
print("三个实验完成。核心收获:")
print("  1. response 是一个结构体, 你关心的是 choices[0].message.content + usage")
print("  2. stream=True 时 delta.content 逐片到达, 非流式是 message.content 一次性给")
print("  3. temperature 控制随机性: 0=确定 / 1.5=发散, 不同场景选不同值")
print("="*60)
