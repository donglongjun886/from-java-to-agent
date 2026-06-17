"""
调用熔断器 — 连续失败超过阈值时自动熔断，冷却后恢复

用于 MCP 工具调用场景：某个工具连续失败 3 次后跳过直接返回降级结果，
冷却期内不再尝试调用，成功后自动复位。
"""

import time
import asyncio


class CircuitBreaker:
    """调用熔断器：基于滑动窗口的失败计数。

    threshold 次连续失败 → 熔断（open），cooldown 秒后恢复（half-open）。
    """

    def __init__(self, threshold: int = 3, cooldown: int = 30):
        self._failures: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()
        self.threshold = threshold
        self.cooldown = cooldown

    async def is_open(self, name: str) -> bool:
        """Return True if circuit is open (should skip)."""
        now = time.time()
        async with self._lock:
            recent = [t for t in self._failures.get(name, []) if now - t < self.cooldown]
            self._failures[name] = recent
        return len(recent) >= self.threshold

    async def record_failure(self, name: str):
        """Record a failure, potentially opening the circuit."""
        now = time.time()
        async with self._lock:
            self._failures.setdefault(name, []).append(now)
            self._failures[name] = [t for t in self._failures[name] if now - t < self.cooldown]

    async def record_success(self, name: str):
        """Reset on success (close circuit)."""
        async with self._lock:
            if name in self._failures:
                del self._failures[name]
