"""Embedding Explorer — 第二部分：向量化 + 相似度直觉验证"""

from itertools import combinations

from sentence_transformers import SentenceTransformer
import numpy as np

print("Loading model...", flush=True)
model = SentenceTransformer("all-MiniLM-L6-v2")

texts = {
    "java-01": "Spring Boot dependency injection with @Autowired annotation",
    "java-02": "Java virtual threads improve concurrent throughput for microservices",
    "java-03": "MySQL connection pool HikariCP max pool size tuning",
    "ai-01": "LangGraph state graph for multi-agent orchestration pipeline",
    "ai-02": "LLM function calling with tool use for autonomous agents",
    "ai-03": "Retrieval augmented generation with vector embeddings and reranking",
    "misc-01": "Best hiking trails near Lake Tahoe in autumn season",
    "misc-02": "How to bake sourdough bread with crispy crust at home",
}

names = list(texts.keys())
contents = list(texts.values())
name_to_idx = {n: i for i, n in enumerate(names)}

embeddings = model.encode(contents, normalize_embeddings=True)

# ── 相似度矩阵 ──
print("\n" + "=" * 70)
print("Embedding 维度:", embeddings.shape[1])
print("=" * 70)

groups = {
    "Java ↔ Java": ["java-01", "java-02", "java-03"],
    "AI   ↔ AI": ["ai-01", "ai-02", "ai-03"],
    "Java ↔ AI": ["java-01", "java-02", "ai-01", "ai-02"],
    "Tech ↔ Misc": ["java-01", "ai-01", "misc-01", "misc-02"],
}

max_len = max(len(n) for n in names)

invalid_keys = {k for sub in groups.values() for k in sub if k not in name_to_idx}
if invalid_keys:
    raise ValueError(f"groups 中包含未知的 text key: {invalid_keys}")

for label, subset in groups.items():
    print(f"\n── {label} ──")
    for a, b in combinations(subset, 2):
        sim = np.dot(embeddings[name_to_idx[a]], embeddings[name_to_idx[b]])
        print(f"  {a:{max_len}s} ↔ {b:{max_len}s}  sim = {sim:.4f}")

# ── 检索演示 ──
print("\n" + "=" * 70)
print("检索演示: 查询 = 'How to build an AI agent with Java Spring'")
print("=" * 70)
query = model.encode(["How to build an AI agent with Java Spring"], normalize_embeddings=True)
query = query.flatten()  # (1,384) → (384,)，兼容单条/批量两种写法
sims = query @ embeddings.T
ranked = sorted(zip(names, sims), key=lambda x: x[1], reverse=True)
for name, score in ranked:
    bar = "█" * max(0, int(score * 40))
    print(f"  {name:{max_len}s} [{score:.4f}] {bar}")
