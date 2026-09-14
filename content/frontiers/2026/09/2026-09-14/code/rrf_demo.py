"""Synthetic rank-fusion example; standard library only; no network or models."""
from collections import defaultdict
from datetime import datetime
from math import isclose
from pathlib import Path
import json
import platform


def rrf(rankings, k=60):
    if k < 0:
        raise ValueError("k must be non-negative")
    scores = defaultdict(float)
    contributions = defaultdict(dict)
    for source, docs in rankings.items():
        # Repeated IDs within one source get one vote; keep the first position.
        unique = list(dict.fromkeys(docs))
        for rank, doc in enumerate(unique, start=1):
            value = 1.0 / (k + rank)
            scores[doc] += value
            contributions[doc][source] = {"rank": rank, "value": value}
    return [
        {"doc": doc, "score": score, "contributions": contributions[doc]}
        for doc, score in sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    ]


def ranked(scored):
    return {name: [doc for doc, _ in sorted(rows, key=lambda x: (-x[1], x[0]))]
            for name, rows in scored.items()}


def main():
    # Deliberately invented scores, not a real corpus or retrieval benchmark.
    raw = {"lexical": [("A", 14.0), ("B", 11.0), ("D", 8.0)],
           "dense": [("C", 0.91), ("B", 0.86), ("D", 0.82)]}
    rankings = ranked(raw)
    rows = rrf(rankings)
    checks = []
    assert [r["doc"] for r in rows] == ["B", "D", "A", "C"]
    assert isclose(rows[0]["score"], 2 / 62)
    checks.append("hand-calculated consensus winner and B score")
    duplicate = {"lexical": ["A", "A", "B", "D"], "dense": ["C", "B", "D", "D"]}
    assert rrf(duplicate) == rows
    checks.append("duplicate IDs do not get additional votes or shift unique ranks")
    assert rrf({**rankings, "empty": []}) == rows and rrf({"empty": []}) == []
    checks.append("empty source and all-empty input")
    rescaled = {name: [(doc, value * 1000 + 73) for doc, value in vals]
                for name, vals in raw.items()}
    assert rrf(ranked(rescaled)) == rows
    checks.append("monotone score rescaling preserves fusion")
    result = {"runAt": datetime.now().astimezone().isoformat(),
              "python": platform.python_version(), "platform": platform.platform(),
              "scope": "Synthetic four-document example; no model, corpus, or latency benchmark",
              "k": 60, "rawScores": raw, "rankings": rankings, "rows": rows,
              "passed": True, "checks": checks,
              "tieRule": "ascending document ID for equal total scores"}
    target = Path(__file__).with_name("rrf-results.json.txt")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
