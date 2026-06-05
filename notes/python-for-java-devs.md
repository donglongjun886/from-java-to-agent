# Python for Java Developers

> 面向有多年 Java 经验的工程师，用对比方式快速上手 Python。

## 类型系统

| Java | Python | 说明 |
|------|--------|------|
| `String name = "hello"` | `name: str = "hello"` | Python 使用类型注解（PEP 484），非强制 |
| `int count = 1` | `count: int = 1` | Python int 无限精度（无 long） |
| `List<String> list = new ArrayList<>()` | `items: list[str] = ["a", "b"]` | list 是内置类型，支持切片 `items[1:3]` |
| `Map<String, Object> map = new HashMap<>()` | `data: dict[str, Any] = {"key": "value"}` | dict 是内置类型 |
| `Optional<String> opt = Optional.of("x")` | `value: str | None = "x"` | `None` 替代 null，`\| None` 替代 Optional |
| `boolean flag = true` | `flag: bool = True` | 注意大写 `True`/`False` |
| `void method() {}` | `def func() -> None: pass` | `pass` ≈ 空语句块 `{}` |

## 控制流

```python
# if-elif-else（注意冒号和缩进）
if score >= 90:
    grade = "A"
elif score >= 60:
    grade = "B"
else:
    grade = "C"

# for 循环（没有传统 for-i）
for item in items:        # 增强 for 循环
    print(item)

for i, item in enumerate(items):  # 带索引
    print(i, item)

# 列表推导式 ≈ Stream.map().filter().collect()
names = [user.name for user in users if user.active]

# try-except ≈ try-catch
try:
    result = risky_call()
except ValueError as e:
    print(f"Error: {e}")
finally:
    cleanup()
```

## 异步 IO

| Java | Python | 说明 |
|------|--------|------|
| `CompletableFuture<T>` | `Coroutine[Any, Any, T]` | 协程是 Python 的异步原语 |
| `async/await`（Java 21+ 虚拟线程） | `async def / await` | 语法几乎相同 |
| `ExecutorService` | `asyncio.gather()` | 并发执行多个协程 |
| `Thread.sleep()` | `await asyncio.sleep()` | 非阻塞等待 |

```python
import asyncio

async def fetch_data(url: str) -> dict:
    # 模拟 API 调用
    await asyncio.sleep(1)
    return {"url": url, "data": "..."}

async def main():
    # 并发执行 ≈ CompletableFuture.allOf()
    results = await asyncio.gather(
        fetch_data("https://api1.example.com"),
        fetch_data("https://api2.example.com"),
    )
    print(results)

asyncio.run(main())
```

## 数据模型 (Pydantic)

Pydantic ≈ Lombok + Bean Validation + Jackson（三位一体）

```python
from pydantic import BaseModel, Field

class User(BaseModel):        # ≈ @Data + @Validated
    name: str
    age: int = Field(ge=0, le=150)
    email: str | None = None  # 可选字段

# JSON → Object（≈ Jackson ObjectMapper）
user = User.model_validate_json('{"name": "Alice", "age": 30}')

# Object → JSON
print(user.model_dump_json())  # {"name":"Alice","age":30,"email":null}
```

## 依赖管理

```bash
# pip（传统，类似 Maven Central 直接下载 jar）
pip install requests

# uv（推荐，类似 Gradle/Maven 的依赖解析）
uv pip install requests

# 项目依赖文件
# pyproject.toml ≈ pom.xml / build.gradle
# requirements.txt ≈ gradle.lockfile（锁定版本）
```

## 核心差异总结

1. **动态类型**：变量没有编译期类型约束，类型注解只是给 IDE 和人看的，运行时不做类型检查
2. **缩进即语法**：用缩进代替 `{}`，用换行代替 `;`
3. **万物皆对象**：函数、类、模块可随意传递（类似 Java 的反射 + Lambda）
4. **没有 private/protected**：约定 `_name` 表示私有，`__name` 触发 name mangling
5. **包管理**：推荐用 `uv`，体验接近 Gradle/Maven
6. **异步优先**：AI Agent 开发中大量使用 `async/await`，比 Java 的虚拟线程生态更成熟

---

## 速通建议

- **前 3 天**：覆盖上面所有内容，边看边写代码
- **不需要学**：多线程（Agent 开发用 asyncio 足够）、Swing/GUI、JNI 等价物
- **重点掌握**：Pydantic + asyncio + fastapi（这三个是 Agent 开发最常用的 Python 能力）
- **遇到不会的**：直接用 Claude Code 问「Java 的 XX 在 Python 里怎么写？」

*最后更新：2026-06-05*