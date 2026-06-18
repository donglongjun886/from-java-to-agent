"""
Day 10 — Agent Gateway 压测脚本 (Locust)

运行方式:
  1. 启动服务: python server.py
  2. 启动压测: locust -f load_test.py --host=http://localhost:9090
  3. 打开 http://localhost:8089 配置并发数和速率
  4. 或命令行模式: locust -f load_test.py --host=http://localhost:9090 --headless -u 5 -r 1 -t 60s

注意: /chat 端点会调用 LLM API，产生费用。
      建议用低并发、短时间跑，或只压测 /health 看框架吞吐上限。
"""

from locust import HttpUser, task, between


class AgentGatewayUser(HttpUser):
    """模拟客户端请求 Agent 网关"""
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        """健康检查 — 无 LLM 调用，压框架吞吐上限"""
        with self.client.get("/health", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"health failed: {r.status_code}")

    @task(1)
    def chat_simple(self):
        """轻量对话 — 无需工具调用的简单问题，测 Agent 基础链路"""
        payload = {"msg": "你好", "temperature": 0.3}
        with self.client.post("/chat", json=payload, catch_response=True, timeout=60) as r:
            if r.status_code != 200:
                r.failure(f"chat failed: {r.status_code}")
            elif r.elapsed.total_seconds() > 30:
                r.failure(f"chat timeout: {r.elapsed.total_seconds():.1f}s")


class HealthOnlyUser(HttpUser):
    """仅压 /health — 测试 FastAPI 框架本身吞吐上限"""
    wait_time = between(0.1, 0.5)

    @task
    def health(self):
        self.client.get("/health")
