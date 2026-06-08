# Python for Java Developers

> 面向有多年 Java 经验的工程师，用对比方式快速上手 Python。

## 类型系统

> **核心认知**：Python 类型注解是给 IDE 和 mypy 看的文档，运行时完全不管。传错了类型不会报错，只有运行到不兼容的操作时才炸。

```python
def get_length(s: str) -> int:
    return len(s)

result = get_length(42)  # 不报错！但 len(42) 会炸：TypeError: object of type 'int' has no len()
```

Java 的 `javac` 在编译期就能拦住类型错误，Python 等价工具是 **mypy**（需要另外跑，不是内置的）。

### Union / Optional（可选类型）

```python
# Python 3.10+ 推荐写法
email: str | None = None       # 可以是 str，也可以是 None
value: int | str = 5           # Union[int, str] — 两种类型都行

# 老写法（看到知道意思）
from typing import Optional, Union
email: Optional[str] = None    # 等价 str | None
value: Union[int, str] = 5     # 等价 int | str
```

### 泛型容器

```python
# Python 3.9+ 内置写法
users: list[str] = ["a", "b"]              # ≈ List<String>
scores: dict[str, int] = {"a": 90}         # ≈ Map<String, Integer>
tags: set[str] = {"python", "java"}        # ≈ Set<String>
data: tuple[int, str] = (1, "hello")       # ≈ Pair<Integer, String>

# 老写法
from typing import List, Dict, Set, Tuple
users: List[str] = ["a", "b"]
scores: Dict[str, int] = {"a": 90}
```

### Any — 放弃类型检查

```python
from typing import Any

def parse(data: str) -> Any:    # ≈ Java Object / Jackson JsonNode
    return json.loads(data)
```

| Java | Python | 说明 |
|------|--------|------|
| `String name = "hello"` | `name: str = "hello"` | Python 使用类型注解（PEP 484），非强制 |
| `int count = 1` | `count: int = 1` | Python int 无限精度（无 long） |
| `List<String> list = new ArrayList<>()` | `items: list[str] = ["a", "b"]` | list 是内置类型，支持切片 `items[1:3]` |
| `Map<String, Object> map = new HashMap<>()` | `data: dict[str, Any] = {"key": "value"}` | dict 是内置类型 |
| `Optional<String> opt = Optional.of("x")` | `value: str \| None = "x"` | `None` 替代 null，`\| None` 替代 Optional |
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

### 必填字段：`Field(...)`

`...`（Ellipsis，省略号字面量）表示「无默认值，必填」。

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(...)        # 必填
    age: int = 30                 # 可选，默认 30
    email: str | None = None      # 可选，默认 None

User(name="Alice")        # ✓
User()                    # ❌ ValidationError: missing field 'name'
```

**Java 类比** ≈ Lombok `@NonNull` / `@Builder.Default`。

### 字段约束：Bean Validation 风味

Pydantic V2 把所有约束都收到 `Field()` 里：

| Pydantic Field 参数 | Java Bean Validation | 说明 |
|---------------------|---------------------|------|
| `ge=0, le=150` | `@Min(0) @Max(150)` | 数值范围（含端点） |
| `gt=0, lt=100` | `@Positive` / 严格大于 | 数值范围（不含端点） |
| `min_length=1, max_length=50` | `@Size(min=1, max=50)` | 字符串长度 |
| `pattern=r"^[\w\.-]+@[\w\.-]+$"` | `@Pattern(regexp="...")` | 正则 |
| `default=None` | `= null` | 默认值 |

```python
class SearchQuery(BaseModel):
    keyword: str = Field(min_length=1, max_length=200, description="搜索关键词")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页条数")
    temperature: float = Field(ge=0.0, le=2.0, description="LLM 温度参数")
```

### description：LLM 场景的命脉

`description` 是 Pydantic 字段的「自然语言描述」，**会出现在 JSON Schema 中**——LLM 工具调用时靠它理解每个字段含义。

```python
class ToolCall(BaseModel):
    name: str = Field(description="工具名称，如 'search'、'calculator'")
    args: dict = Field(description="工具参数，键值对")
    confidence: float = Field(ge=0, le=1, description="置信度，0~1")
```

**Java 类比** ≈ Swagger 的 `@Schema(description = "...")`。

> **经验**：description 写得越清楚，LLM 输出的准确率越高。这是 Day4 写 Agent 时的**第一杠杆**。

### 字段别名：`Field(alias=...)`

外部 JSON 字段名跟 Python 命名规范不一致时，用 alias 接住：

```python
from pydantic import ConfigDict

class User(BaseModel):
    user_name: str = Field(alias="userName")
    model_config = ConfigDict(populate_by_name=True)   # 两种名字都能传

# 都 OK：
User(userName="alice")
User(user_name="alice")
```

**Java 类比** ≈ Jackson 的 `@JsonProperty("userName")`。

LLM 经常输出驼峰或全大写字段名，alias 是接住的关键。

### frozen：软约束 vs final 硬约束

`frozen=True` 让字段构造后**不可重新赋值**：

```python
class Point(BaseModel):
    x: float = Field(frozen=True)
    y: float = Field(frozen=True)

p = Point(x=1, y=2)
p.x = 99     # ❌ ValidationError: Instance is frozen
```

**但这跟 Java `final` 完全不同**：

| 维度 | Java `final` | Pydantic `frozen=True` |
|------|-------------|----------------------|
| 强制时机 | **编译期** | **运行期**（仅赋值时拦截） |
| 强制主体 | JVM 编译器 | Pydantic 框架的 `__setattr__` |
| 强度 | 硬约束 | 软约束（可绕过） |

**绕过的方法**：

```python
p.__dict__['x'] = 99                    # ✓ 直接改 __dict__
object.__setattr__(p, 'x', 99)         # ✓ 绕过 Pydantic 钩子
```

> **本质**：`final` 是**语言契约**（编译器背书），`frozen` 是**框架契约**（Pydantic 背书）。Python 哲学：「我们都是成年人，约定即可」。

**工程建议**：把 `frozen` 当**防御性编程的提示**，别当**安全边界**。LLM 输出场景下**别用**（要中间修补），配置 / 枚举 / 值对象里**可以用**。

### ⚠️ 陷阱：字段名别用 Python builtin

Pydantic 字段名如果和 Python builtin 同名（如 `int` / `str` / `list`），会触发「注解解析时 builtin 被遮蔽」的坑：

```python
from typing import Optional

class Boo(BaseModel):
    int: Optional[int] = None   # ❌ Pydantic 解析注解时把 int 当成 None，不是 builtin
```

**机制**：类体执行 `int: Optional[int] = None` 时，先求注解（此时 `int` 还是 builtin），再执行赋值 `int = None`，**builtin `int` 被遮蔽**。Pydantic 后续解析注解时找 `int` 拿到 `None`，认为字段类型是 `Optional[None]`，校验时只接受 `None`。

**修复**：

```python
# 方式 1：重命名（推荐）
class Boo(BaseModel):
    value: Optional[int] = None

# 方式 2：用 alias 保留外部字段名
class Boo(BaseModel):
    int_: Optional[int] = Field(default=None, alias='int')
    model_config = ConfigDict(populate_by_name=True)
```

**避坑清单**：`int` / `str` / `list` / `dict` / `set` / `tuple` / `bool` / `bytes` / `float` —— 这些 builtin 都不能直接做字段名。类比 Java 避开 `Object` / `String` / `Class` 等类名作字段名。

### 严格模式：`ConfigDict(strict=True)`

Pydantic V2 **默认是 lax 模式**（宽松），会自动强转类型。这跟 Java 强类型直觉相反：

```python
import json
from pydantic import ConfigDict

class Order(BaseModel):
    order_id: int
    amount: float
    currency: str = "CNY"

raw = '{"order_id": "12345", "amount": "99.5", "currency": 100}'

# 默认 lax 模式：✅ 不报错，全部强转
order = Order.model_validate(json.loads(raw))
# order_id=12345, amount=99.5, currency='100'

# 严格模式：❌ 3 个字段都报错
class StrictOrder(BaseModel):
    model_config = ConfigDict(strict=True)
    order_id: int
    amount: float
    currency: str

StrictOrder.model_validate(json.loads(raw))
# ValidationError: 3 validation errors
```

**单字段也能局部开 strict**：

```python
class Order(BaseModel):
    order_id: int = Field(strict=True)   # 只这个字段严格
    amount: float
    currency: str = "CNY"
```

**Java 类比**：

| Pydantic | Jackson |
|---------|---------|
| 默认 lax（会强转） | Jackson 默认会失败类型不匹配 |
| `ConfigDict(strict=True)` | Jackson 默认行为 |

**LLM 场景建议**：
- 接收 LLM 输出时**用 lax**（容忍 `"123"` → `123` 的转换）
- 自己代码内部传递时**用 strict**（早爆早修）

---

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

*最后更新：2026-06-08（Day 2，+Pydantic 进阶章节）*  
*已完成：[Real Python: Async IO in Python](https://realpython.com/async-io-python/) ✅ | [Python typing 官方文档](https://docs.python.org/3/library/typing.html) ✅ | [mypy Getting Started](https://mypy.readthedocs.io/en/stable/getting_started.html) ✅ | [Python 控制流教程](https://docs.python.org/3/tutorial/controlflow.html) ✅*