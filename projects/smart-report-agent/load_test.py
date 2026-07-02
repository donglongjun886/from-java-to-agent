"""四Agent系统负载压测: QPS / P99延迟 / Token成本。

测量维度:
  - 单次请求的端到端延迟 (Planner → Retriever → Generator → Evaluator)
  - 各阶段耗时拆解 (哪个Agent最慢)
  - 不同并发下的 QPS 和 P99 衰减
  - Token 消耗和单次调用成本估算

面试要点: "我用生产系统的标准 — QPS/P99/成本 — 度量了四Agent系统，
  这体现了 Java 工程师的高并发治理经验迁移到 Agent 系统上。"
"""
import math
import os
import sys
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from four_agent_system import (
    ask_llm, run_planner, run_retriever, run_generator, run_evaluator,
)
from retrieval_compare import static_retrieve, QA_PAIRS

# DEEPSEEK 定价: 输入 ¥1/百万token, 输出 ¥2/百万token (近似)
COST_PER_1M_INPUT = 1.0   # RMB
COST_PER_1M_OUTPUT = 2.0  # RMB

TEST_QUERIES = [qa["question"] for qa in QA_PAIRS]

# 压测采样数常量
PROFILING_SAMPLE_SIZE = 3      # 阶段拆解采样数（避免API调用过多）
COMPARISON_SAMPLE_SIZE = 3     # 静态 vs Agentic 对比采样数


def time_stage(func, *args):
    """计录单个阶段的耗时, 返回 (结果, 耗时_ms)。"""
    t0 = time.perf_counter()
    result = func(*args)
    elapsed = (time.perf_counter() - t0) * 1000
    return result, elapsed


def run_full_pipeline(query: str) -> dict:
    """运行完整四Agent Pipeline, 记录各阶段耗时和token估算。"""
    stages = {}
    total_tokens = {"input": 0, "output": 0}

    # Stage 1: Planner (1次LLM调用)
    plan, t_plan = time_stage(run_planner, query)
    stages["planner_ms"] = t_plan
    # 粗略token估算: planner输入~300 tokens, 输出~150 tokens
    total_tokens["input"] += 300
    total_tokens["output"] += 150

    # Stage 2: Retriever (最多4路检索, 实际看plan里的任务数)
    t_retrieve_start = time.perf_counter()
    retrieved = run_retriever(plan)
    t_retrieve = (time.perf_counter() - t_retrieve_start) * 1000
    stages["retriever_ms"] = t_retrieve

    # Stage 3: Generator (1次LLM调用, context较大)
    t_gen_start = time.perf_counter()
    answer = run_generator(query, retrieved)
    t_gen = (time.perf_counter() - t_gen_start) * 1000
    stages["generator_ms"] = t_gen
    # Generator: context ~800 tokens + query ~100 tokens → input ~900, output ~300
    total_tokens["input"] += 900
    total_tokens["output"] += 300

    # Stage 4: Evaluator (1次LLM调用)
    eval_result, t_eval = time_stage(run_evaluator, query, answer, retrieved)
    stages["evaluator_ms"] = t_eval
    total_tokens["input"] += 500
    total_tokens["output"] += 200

    stages["total_ms"] = t_plan + t_retrieve + t_gen + t_eval
    # 成本 = 输入token/百万 * 1元 + 输出token/百万 * 2元
    token_cost = (total_tokens["input"] / 1_000_000) * COST_PER_1M_INPUT + \
                 (total_tokens["output"] / 1_000_000) * COST_PER_1M_OUTPUT
    stages["estimated_tokens"] = total_tokens
    stages["estimated_cost_rmb"] = round(token_cost, 6)
    return stages


def run_static_pipeline(query: str) -> dict:
    """运行静态RAG pipeline, 无LLM调用, 纯关键词规则。"""
    t0 = time.perf_counter()
    _ = static_retrieve(query)
    elapsed = (time.perf_counter() - t0) * 1000
    return {"total_ms": elapsed, "planner_ms": 0, "retriever_ms": elapsed,
            "generator_ms": 0, "evaluator_ms": 0,
            "estimated_tokens": {"input": 0, "output": 0}, "estimated_cost_rmb": 0.0}


def run_concurrency_test(pipeline_fn, queries: list[str], concurrency: int,
                         label: str) -> dict:
    """以指定并发数执行pipeline, 统计QPS和延迟分布。"""
    latencies = []
    failed_count = 0
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(pipeline_fn, q): q for q in queries}
        for future in as_completed(futures):
            try:
                result = future.result()
                latencies.append(result["total_ms"])
            except Exception as e:
                failed_count += 1
                print(f"  [ERROR] 并发请求失败 ({label}): {e}")

    wall_time = time.perf_counter() - start
    qps = len(queries) / wall_time if wall_time > 0 else 0
    latencies.sort()

    if not latencies:
        return {
            "label": label,
            "concurrency": concurrency,
            "total_queries": len(queries),
            "failed_count": failed_count,
            "wall_time_s": round(wall_time, 2),
            "qps": round(qps, 2),
            "latency_p50_ms": 0,
            "latency_p99_ms": 0,
            "latency_max_ms": 0,
            "latency_min_ms": 0,
        }

    # P99: 使用 math.ceil 确保取到 >=99% 位置的元素 (0-indexed)
    p99_idx = max(0, math.ceil(len(latencies) * 0.99) - 1)

    return {
        "label": label,
        "concurrency": concurrency,
        "total_queries": len(queries),
        "failed_count": failed_count,
        "wall_time_s": round(wall_time, 2),
        "qps": round(qps, 2),
        "latency_p50_ms": round(statistics.median(latencies), 0),
        "latency_p99_ms": round(latencies[p99_idx], 0),
        "latency_max_ms": round(latencies[-1], 0),
        "latency_min_ms": round(latencies[0], 0),
    }


def run_single_query_breakdown(queries: list[str]) -> list[dict]:
    """单查询逐阶段耗时拆解, 找出瓶颈。"""
    breakdowns = []
    for q in queries[:PROFILING_SAMPLE_SIZE]:
        print(f"  profiling: {q[:30]}...")
        stages = run_full_pipeline(q)
        breakdowns.append({"query": q[:40], **stages})
    return breakdowns


# ═══ 主入口 ═══
def main():
    sep = "=" * 70

    print(f"{sep}")
    print("四Agent系统负载压测报告: QPS / 延迟 / 成本")
    print(f"{sep}\n")

    # ── 1. 单查询阶段耗时拆解 ──
    print("1. 单查询逐阶段耗时拆解 (前3题)")
    print("-" * 70)
    breakdowns = run_single_query_breakdown(TEST_QUERIES)

    stage_names = ["planner_ms", "retriever_ms", "generator_ms", "evaluator_ms"]
    print(f"\n{'Query':<30s} {'Plan':>7s} {'Retr':>7s} {'Gen':>7s} {'Eval':>7s} {'Total':>8s} {'Cost(RMB)':>10s}")
    print("-" * 85)
    for bd in breakdowns:
        display = bd["query"][:27] + ("…" if len(bd["query"]) > 27 else "")
        print(f"{display:<30s} {bd['planner_ms']:>6.0f}ms {bd['retriever_ms']:>5.0f}ms "
              f"{bd['generator_ms']:>5.0f}ms {bd['evaluator_ms']:>5.0f}ms "
              f"{bd['total_ms']:>7.0f}ms {bd['estimated_cost_rmb']:>10.6f}")

    if breakdowns:
        avg = {s: sum(b[s] for b in breakdowns) / len(breakdowns) for s in stage_names}
        avg_total = sum(avg.values())
        avg_cost = sum(b["estimated_cost_rmb"] for b in breakdowns) / len(breakdowns)
        print("-" * 85)
        print(f"{'平均':<30s} {avg['planner_ms']:>6.0f}ms {avg['retriever_ms']:>5.0f}ms "
              f"{avg['generator_ms']:>5.0f}ms {avg['evaluator_ms']:>5.0f}ms "
              f"{avg_total:>7.0f}ms {avg_cost:>10.6f}")
        # 找出瓶颈
        worst = max(stage_names, key=lambda s: avg[s])
        print(f"\n→ 瓶颈在 {worst.replace('_ms','')}，占总耗时 {avg[worst]/avg_total*100:.0f}%")

    # ── 2. 静态 vs Agentic 延迟对比 ──
    print(f"\n\n2. 静态RAG vs Agentic Retrieval 延迟对比 ({len(TEST_QUERIES)}题串行)")
    print("-" * 70)
    # 静态
    static_query_count = len(TEST_QUERIES)
    t0 = time.perf_counter()
    for q in TEST_QUERIES:
        static_retrieve(q)
    static_total = (time.perf_counter() - t0) * 1000

    # Agentic (只跑前N题避免API开销过大)
    agentic_queries = TEST_QUERIES[:COMPARISON_SAMPLE_SIZE]
    agentic_failed = 0
    t0 = time.perf_counter()
    for q in agentic_queries:
        try:
            plan = run_planner(q)
            run_retriever(plan)
        except Exception as e:
            agentic_failed += 1
            print(f"  [WARN] 静态vsAgentic对比失败 ({q[:20]}...): {e}")
    agentic_total = (time.perf_counter() - t0) * 1000
    agentic_success = len(agentic_queries) - agentic_failed

    print(f"  静态RAG:      {static_total:.0f}ms / {static_query_count}题 = {static_total/static_query_count:.0f}ms/题 (纯规则, 0 LLM调用)")
    agentic_label = "Agentic (Planner+Retriever)"
    if agentic_success > 0:
        print(f"  {agentic_label}: {agentic_total:.0f}ms / {agentic_success}题 = {agentic_total/agentic_success:.0f}ms/题 (含LLM)")
        if agentic_failed > 0:
            print(f"                  失败: {agentic_failed}/{len(agentic_queries)} 题")
        ratio = agentic_total / agentic_success / (static_total / static_query_count)
        print(f"  延迟倍数:     Agentic ≈ 静态 × {ratio:.0f}x "
              f"(但Agentic能处理静态规则覆盖不了的查询)")
    else:
        print(f"  {agentic_label}: 全部失败 ({agentic_failed}/{len(agentic_queries)})")

    # ── 3. 并发压测 ──
    print(f"\n\n3. 并发压测 (静态RAG级, Agentic级只做单并发因API延迟占主导)")
    print("-" * 70)

    levels = [("静态RAG", run_static_pipeline, [1, 5, 10]),
              ("Agentic", run_full_pipeline, [1])]  # Agentic只测单并发,多并发用静态RAG模拟

    for label, fn, concurrency_levels in levels:
        for c in concurrency_levels:
            result = run_concurrency_test(fn, TEST_QUERIES, c, f"{label} x{c}")
            print(f"  {result['label']:<20s} "
                  f"QPS={result['qps']:>6.1f}  "
                  f"P50={result['latency_p50_ms']:>8.0f}ms  "
                  f"P99={result['latency_p99_ms']:>8.0f}ms  "
                  f"Wall={result['wall_time_s']}s")

    # 成本估算
    print(f"\n\n4. 单次调用成本估算")
    print("-" * 70)
    print(f"  ⚠️ 成本为静态估算（基于固定Token预估值，非API返回的实时usage统计）")
    if breakdowns:
        print(f"  每次完整四Agent调用: ¥{avg_cost:.6f} (~{avg_cost*1000:.4f}分/次)")
        print(f"  100次/天: ¥{avg_cost*100:.2f}/天")
        print(f"  月均(22工作日): ¥{avg_cost*100*22:.2f}/月")
        print(f"  Token消耗/次: 输入~{breakdowns[0]['estimated_tokens']['input']} + "
              f"输出~{breakdowns[0]['estimated_tokens']['output']}")
        print(f"  模型: DeepSeek V4 Pro (输入¥1/百万token, 输出¥2/百万token)")

    print(f"\n{sep}")
    print("面试话术:")
    print("  「四Agent系统的P99延迟约Xms，瓶颈在Generator(单次LLM生成~Xms)。")
    print("    成本约¥X.X/次，月均¥XX。静态RAG零LLM成本但覆盖率受限于规则。")
    print("    生产环境建议: 高频简单查询走静态RAG兜底，复杂多步推理才进Agentic Pipeline。」")
    print(f"{sep}")


if __name__ == "__main__":
    main()
