# Day 1：环境搭建 + Python 速通（2026-06-05）

## 今日目标

- 搭建 Python 3.12 开发环境
- 用 Java 类比快速掌握 Python 核心语法
- 阅读完 4 份关键资料

## 已完成

### 资料阅读

| 资料 | 状态 |
|------|------|
| [Real Python: Async IO in Python](https://realpython.com/async-io-python/) | ✅ |
| [Python typing 官方文档](https://docs.python.org/3/library/typing.html) | ✅ |
| [mypy Getting Started](https://mypy.readthedocs.io/en/stable/getting_started.html) | ✅ |
| [Python 控制流教程](https://docs.python.org/3/tutorial/controlflow.html) | ✅ |

### 概念掌握

- **类型系统**：Python 类型注解是纯装饰，运行时不做检查。`str | None` 替代 Optional，`list[str]` / `dict[str, int]` 替代泛型。mypy ≈ Python 的 javac。
- **控制流**：列表推导式 `[expr for x in iterable if cond]` ≈ Stream.map().filter().collect()
- **asyncio**：`async def` 定义协程，`asyncio.gather()` ≈ `CompletableFuture.allOf()`。哨兵模式（Poison Pill）用 None 通知消费者退出。

### 代码理解

- 完整吃透了 `projects/01-hello-agent/main.py` 中 `HelloAgent` 类的实现
- 理解了 OpenAI 兼容 API 的调用方式（`client.chat.completions.create`）
- 掌握了流式响应的处理流程（`stream=True` + 逐 chunk 拼接）

## 关键认知

- Python 和 Java 在底层思维模型上高度相通，差异主要在语法层面
- Agent 开发重度依赖 asyncio，单线程并发模型比 Java 多线程更轻量
- 类型注解 + mypy 的组合 ≈ Java 的编译期类型检查，但是可选的

---

*记录日期：2026-06-05*
