"""Deterministic teaching example, not an LLM benchmark or paper replication."""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import platform

@dataclass(frozen=True)
class Answer:
    label: str
    kind: str
    value: int | None
    known_subtotal: int | None
    citations: tuple[str, ...]
    decisive: bool


def style_score(answer: Answer) -> int:
    # A deliberately inadequate proxy: numbers, citations, and assertive form.
    return (40 if answer.value is not None or answer.known_subtotal is not None else 0) + (30 if answer.citations else 0) + (30 if answer.decisive else 0)


def evidence_score(rows: dict[str, int | None], answer: Answer) -> int:
    known = {key: value for key, value in rows.items() if value is not None}
    if any(key not in known for key in answer.citations):
        return 0
    if set(answer.citations) != set(known):
        return 0
    subtotal = sum(known.values())
    if len(known) < len(rows):
        valid = answer.kind == "insufficient" and answer.value is None and answer.known_subtotal == subtotal
    else:
        valid = answer.kind == "total" and answer.value == subtotal
    return 100 if valid else 0


def main():
    cases = [
        ("缺一项数据", {"A": 10, "B": 20, "C": None}, [
            Answer("断言总计 60", "total", 60, None, ("A", "B"), True),
            Answer("已知小计 30，总计待定", "insufficient", None, 30, ("A", "B"), False),
        ]),
        ("数据齐全的对照", {"A": 10, "B": 20, "C": 30}, [
            Answer("正确总计 60", "total", 60, None, ("A", "B", "C"), True),
            Answer("仍声称无法计算", "insufficient", None, 60, ("A", "B", "C"), False),
        ]),
    ]
    results = []
    for label, rows, answers in cases:
        scores = [{"answer": a.label, "styleScore": style_score(a), "evidenceScore": evidence_score(rows, a)} for a in answers]
        results.append({"case": label, "rows": rows, "scores": scores})
    assert [x["evidenceScore"] for x in results[0]["scores"]] == [0, 100]
    assert [x["evidenceScore"] for x in results[1]["scores"]] == [100, 0]
    assert results[0]["scores"][0]["styleScore"] > results[0]["scores"][1]["styleScore"]
    assert evidence_score(cases[0][1], Answer("错误小计", "insufficient", None, 31, ("A", "B"), False)) == 0
    assert evidence_score(cases[0][1], Answer("引用缺失行", "insufficient", None, 30, ("A", "B", "C"), False)) == 0
    out = {"executedAt": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(), "platform": platform.platform(), "assertionsPassed": 5, "cases": results, "scope": "Handwritten structured answers and deterministic rules; no model call; no paper replication."}
    Path(__file__).with_name("evidence-results.json.txt").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
