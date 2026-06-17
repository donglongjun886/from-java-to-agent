"""
代码沙箱 — 轻量级 Python 代码执行器
使用 subprocess 在受限命名空间中执行用户代码
"""

import subprocess
import sys
import tempfile
import os


class SandboxExecutor:
    """受限 Python 代码执行器

    在子进程中执行用户提交的代码，仅暴露安全的 builtins。
    支持超时控制和结构化结果返回。
    """

    ALLOWED_BUILTINS = {
        "print", "len", "range", "int", "float", "str",
        "list", "dict", "sum", "min", "max", "abs",
        "round", "sorted", "enumerate", "zip", "map", "filter",
    }

    def _validate_code(self, code: str) -> dict | None:
        """验证代码安全性，返回 None 表示通过，否则返回错误 dict"""
        dangerous = [
            ("__", "dunder 属性访问"),
            ("import ", "import 语句"),
            ("exec(", "exec() 调用"),
            ("eval(", "eval() 调用"),
            ("compile(", "compile() 调用"),
            ("open(", "open() 调用"),
            ("__import__(", "__import__() 调用"),
        ]
        for pattern, desc in dangerous:
            if pattern in code:
                return {
                    "output": "",
                    "error": f"代码包含禁止模式: {desc}",
                    "exit_code": -1,
                }
        return None

    def execute(self, code: str, timeout: int = 5) -> dict:
        """在受限沙箱中执行 Python 代码

        Args:
            code: 要执行的 Python 代码字符串
            timeout: 最大执行时间（秒），默认 5

        Returns:
            {"output": str, "error": str, "exit_code": int}
        """
        # ① 静态安全扫描
        error = self._validate_code(code)
        if error:
            return error

        script = self._build_script(code)
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as f:
                f.write(script)
                tmp_path = f.name

            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                timeout=timeout,
                text=True,
            )
            return {
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"output": "", "error": f"执行超时 ({timeout}s)", "exit_code": -1}
        except Exception as e:
            return {"output": "", "error": str(e), "exit_code": -1}
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except FileNotFoundError:
                    pass

    def _build_script(self, code: str) -> str:
        """构建带受限 builtins 的执行脚本"""
        allowed = sorted(self.ALLOWED_BUILTINS)
        return f'''
import builtins
_safe = {allowed!r}
_globals = {{k: getattr(builtins, k) for k in _safe}}
_globals["__builtins__"] = _globals
exec({code!r}, _globals)
'''
