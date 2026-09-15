"""Deterministic MMR demo. Synthetic vectors, no model/API or third-party package."""
import json
import math
import platform
from datetime import datetime
from pathlib import Path

QUERY = [1.0, 0.0, 0.0]
DOCS = [
    {"id": "A", "label": "检索概览", "vector": [1.0, 0.0, 0.0]},
    {"id": "B", "label": "概览近似段落 1", "vector": [0.99, 0.1, 0.0]},
    {"id": "C", "label": "概览近似段落 2", "vector": [0.98, 0.15, 0.0]},
    {"id": "D", "label": "检索评测角度", "vector": [0.8, 0.6, 0.0]},
    {"id": "E", "label": "检索部署角度", "vector": [0.8, 0.0, 0.6]},
    {"id": "F", "label": "偏题材料", "vector": [0.1, 1.0, 1.0]},
]


def cosine(a, b):
    if len(a) != len(b) or not a:
        raise ValueError("equal non-empty vector dimensions required")
    if not all(math.isfinite(x) for x in a + b):
        raise ValueError("finite vectors required")
    denominator = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    if not denominator:
        raise ValueError("zero vectors have no cosine direction")
    return sum(x*y for x, y in zip(a, b)) / denominator


def rerank(query, docs, k=3, relevance_weight=0.35, threshold=0.7):
    if not 0 <= relevance_weight <= 1 or k < 0:
        raise ValueError("weight must be in [0, 1], k nonnegative")
    if len({d["id"] for d in docs}) != len(docs):
        raise ValueError("duplicate document ids")
    pool = [dict(d, relevance=cosine(query, d["vector"])) for d in docs]
    pool = sorted((d for d in pool if d["relevance"] >= threshold),
                  key=lambda d: (-d["relevance"], d["id"]))
    selected, trace = [], []
    while pool and len(selected) < k:
        scored = []
        for d in pool:
            redundancy = max((cosine(d["vector"], s["vector"]) for s in selected), default=0)
            score = relevance_weight*d["relevance"] - (1-relevance_weight)*redundancy
            scored.append(dict(d, redundancy=redundancy, mmr=score))
        # Explicit convention: first pick is the most relevant item, including weight=0.
        chosen = scored[0] if not selected else min(scored, key=lambda d: (-d["mmr"], d["id"]))
        trace.append({"step": len(selected)+1, "chosen": chosen["id"], "candidates": scored})
        selected.append(chosen)
        pool = [d for d in pool if d["id"] != chosen["id"]]
    return selected, trace


def summary(rows):
    pairs = [cosine(a["vector"], b["vector"]) for i, a in enumerate(rows) for b in rows[i+1:]]
    return {"ids": [d["id"] for d in rows],
            "meanRelevance": sum(d["relevance"] for d in rows)/len(rows) if rows else None,
            "meanPairwiseSimilarity": sum(pairs)/len(pairs) if pairs else None}


if __name__ == "__main__":
    chosen, trace = rerank(QUERY, DOCS)
    top, _ = rerank(QUERY, DOCS, relevance_weight=1)
    unfiltered, _ = rerank(QUERY, DOCS, threshold=-1)
    assert summary(top)["ids"] == ["A", "B", "C"]
    assert summary(chosen)["ids"] == ["A", "D", "E"]
    assert "F" in summary(unfiltered)["ids"]
    assert rerank(QUERY, [], 3)[0] == []
    assert rerank(QUERY, DOCS, 0)[0] == []
    assert len(rerank(QUERY, DOCS, 99)[0]) == 5
    assert cosine([1, 0], [0, 1]) == 0
    assert abs(cosine([2, 0], [7, 0])-1) < 1e-12
    try:
        cosine([0, 0], [1, 1])
    except ValueError:
        pass
    else:
        raise AssertionError("zero vector must be rejected")
    result = {"runAt": datetime.now().astimezone().isoformat(), "python": platform.python_version(),
              "dataType": "hand-designed synthetic vectors; labels are illustrative, not model embeddings",
              "query": QUERY, "documents": DOCS, "k": 3, "lambda": 0.35, "threshold": 0.7,
              "topK": summary(top), "mmr": summary(chosen), "withoutThreshold": summary(unfiltered),
              "trace": trace, "checks": "9 assertions passed: known ranking, off-topic counterexample, empty/k bounds, cosine and invalid zero vector"}
    dest = Path(__file__).with_name("mmr-results.json.txt")
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["runAt","python","topK","mmr","withoutThreshold","checks"]}, ensure_ascii=False, indent=2))
