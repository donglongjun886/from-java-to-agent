# 代码沙箱

> Day 7 学习笔记（2026-06-15）。核心认知：**Agent 生成的代码不能在宿主机裸跑，沙箱就是给 Agent 的 Docker 容器——隔离执行，炸了也不影响宿主机。**

---

## 1. 为什么 Agent 需要沙箱

### 1.1 三层风险

| 风险层 | 场景 | 后果 |
|--------|------|------|
| **安全性** | Agent 生成 `os.system("rm -rf /")` | 宿主机被破坏 |
| **资源** | Agent 生成死循环 `while True: pass` | CPU 100%，影响其他服务 |
| **数据泄露** | Agent 处理用户上传的含敏感信息的文件 | 合规风险 |

### 1.2 类比

| Java 概念 | 沙箱概念 |
|-----------|---------|
| JVM SecurityManager | 沙箱执行权限控制 |
| Docker Container | 沙箱隔离环境 |
| `try-catch` 异常处理 | 执行超时/异常的兜底 |
| `@Transactional` 回滚 | 沙箱销毁后环境恢复干净 |

---

## 2. 主流方案对比

### 2.1 五个方案

| 方案 | 隔离级别 | 启动速度 | 成本 | 适用场景 |
|------|---------|---------|------|---------|
| **subprocess** | 无隔离 | 毫秒 | 免费 | 仅限可信代码 |
| **Docker** | 强隔离 | 秒级 | 自建服务器成本 | 开发/测试/自建生产 |
| **E2B** | 强隔离 | ~1秒 | API 按调用付费 | 生产环境（免运维） |
| **Firecracker** | 极强（microVM） | ~125ms | 自建集群 | 高安全要求 / 多租户 |
| **WebAssembly** | 强隔离 | 毫秒 | 免费 | 轻量级代码执行 |

### 2.2 决策树

```
需要多租户 / 最高安全？→ Firecracker
需要免运维 / 快速集成？→ E2B
需要自建 / 完全控制？  → Docker
只是本地调试 Demo？   → subprocess（够用）
```

学习阶段用 Docker，生产环境考虑 E2B。

---

## 3. E2B 基础用法

### 3.1 核心 API

```python
from e2b import Sandbox

# 创建沙箱
sandbox = Sandbox.create(template="python3")

# 执行代码
result = sandbox.run_code("print('hello')")
print(result.logs)  # "hello"

# 文件操作
sandbox.filesystem.write("/tmp/data.csv", csv_content)
content = sandbox.filesystem.read("/tmp/result.txt")

# 清理
sandbox.close()
```

### 3.2 生命周期管理

```
创建 → 执行代码 → 提取结果 → 销毁
       ↑ 可多次执行 ↓
       设置超时（默认 5min）
```

```
创建 → 执行代码 → 超时/异常 → 强制销毁
```

**超时是必须的**。不给沙箱设置超时 ≈ 不给 HTTP 请求设超时——会被拖死。

---

## 4. Docker 自建方案

### 4.1 典型封装

```python
import docker

class DockerSandbox:
    def __init__(self, image="python:3.12-slim", timeout=30, memory="256m"):
        self.client = docker.from_env()
        self.image = image
        self.timeout = timeout
        self.memory = memory

    def run(self, code: str) -> str:
        container = self.client.containers.run(
            image=self.image,
            command=["python", "-c", code],
            detach=True,
            mem_limit=self.memory,
            network_disabled=True,       # 禁止网络
            read_only=True,              # 只读文件系统
            remove=True,                 # 执行完自动删除
        )
        try:
            result = container.wait(timeout=self.timeout)
            return container.logs().decode()
        except Exception:
            container.kill()
            raise
```

### 4.2 关键限制参数

| 参数 | 推荐值 | 原因 |
|------|--------|------|
| `mem_limit` | 256m-512m | 防内存耗尽 |
| `timeout` | 30s | 防死循环 |
| `network_disabled` | True | 防访问内网 |
| `read_only` | True | 防写文件逃逸 |

---

## 5. 安全最佳实践

### 5.1 五层防御

```
① 代码静态扫描   → 执行前检查危险模式（import os / subprocess / eval）
② 资源限制       → CPU/内存/时间上限
③ 网络隔离       → 禁止沙箱访问内外网
④ 文件系统隔离   → 只挂载必要目录，其余只读
⑤ 进程隔离       → 独立容器/VM，执行完销毁
```

### 5.2 代码静态扫描（低成本第一道防线）

```python
DANGEROUS_PATTERNS = [
    "import os", "import subprocess", "import shutil",
    "os.system", "eval(", "exec(", "__import__",
    "open(",  # 需要 review，可能合法
]

def scan_code(code: str) -> list[str]:
    """返回检测到的危险模式列表"""
    return [p for p in DANGEROUS_PATTERNS if p in code]
```

这不是完美的安全方案，但是低成本的「第一道防线」——能拦截 90% 的明显恶意代码。

---

## 6. 在 Agent 中的集成位置

### 6.1 架构位置

```
Agent Graph
  ├── llm_node         → 决策是否要执行代码
  ├── sandbox_node     → 沙箱执行（本笔记的重点）
  ├── eval_node        → 评估执行结果
  └── feedback_node    → 失败时重试
```

沙箱是 Tool 层的一种特殊工具——`execute_code` 工具。

### 6.2 完整执行链路

```
1. LLM 输出 tool_call: execute_code(code="...")
2. router() → "tool" 分支
3. sandbox_node: scan_code(code) → 通过？→ sandbox.run(code) → 返回结果
                                  → 拦截？→ 返回错误信息
4. 结果回传 LLM，LLM 决定下一步（调整代码重试 / 给出最终回复）
```

### 6.3 容错策略

| 异常类型 | 处理方式 |
|---------|---------|
| 超时 | 返回「执行超时，请优化代码」→ LLM 重试 |
| 内存溢出 | 返回「内存不足」→ 不重试（资源问题非代码问题） |
| 危险代码 | 返回「检测到危险模式: xxx」→ 不重试 |
| 沙箱不可用 | Fallback：返回「暂不支持代码执行」 |

---

## 7. 核心 Takeaway

1. **沙箱不是可选项，是必选项** — Agent 会生成代码，代码不可信，必须隔离执行
2. **安全是纵深防御** — 静态扫描 + 资源限制 + 网络隔离 + 文件隔离 + 进程隔离，层层设防
3. **超时是底线** — 不给沙箱设超时 = 允许 Agent 无限占用资源
4. **学习阶段用 Docker，生产环境评估 E2B** — 自建够灵活，托管够省心

---

## 延伸

- [E2B 代码沙箱文档](https://e2b.dev/docs)
- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [Firecracker microVM](https://firecracker-microvm.github.io/)