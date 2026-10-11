#!/usr/bin/env python3
"""Synthetic teaching example inspired by TestPrism; not a paper reproduction.
Contract: list[str] -> list[str], retain first-occurrence order, keep empty strings,
leave input unchanged. All implementations and examples are authored locally.
"""
import inspect
import json
import platform
from pathlib import Path


def loop_unique(values):
    result = []
    for item in values:
        if item not in result:
            result.append(item)
    return result


def dict_unique(values):
    return list(dict.fromkeys(values))


def sorted_unique(values):
    return sorted(set(values))


def identity(values):
    return list(values)


def drop_empty(values):
    result = []
    for item in values:
        if item and item not in result:
            result.append(item)
    return result


def keep_last(values):
    return list(reversed(list(dict.fromkeys(reversed(values)))))


CASES = [
    (["b", "a", "b", "", "a"], ["b", "a", ""]),
    ([], []),
    (["", ""], [""]),
    (["b", "a"], ["b", "a"]),
    (["x"], ["x"]),
]


def weak_example(fn):
    return fn(["a", "b", "a"]) == ["a", "b"]


def source_style(fn):
    # Intentionally poor test: a valid dict implementation fails this style gate.
    return weak_example(fn) and "for item in values:" in inspect.getsource(fn)


def contract_examples(fn):
    for values, expected in CASES:
        before = values.copy()
        result = fn(values)
        if not isinstance(result, list) or result != expected or values != before:
            return False
    return True


IMPLEMENTATIONS = [
    (loop_unique, "循环去重", True),
    (dict_unique, "字典去重", True),
    (sorted_unique, "排序后去重", False),
    (identity, "保留全部元素", False),
    (drop_empty, "错误丢弃空串", False),
    (keep_last, "保留末次顺序", False),
]
SUITES = [(weak_example, "单一样例"), (source_style, "样例＋源码样式"),
          (contract_examples, "五组合同行为样例")]


def main():
    rows = []
    for fn, label, valid in IMPLEMENTATIONS:
        results = {}
        for suite, _ in SUITES:
            try:
                results[suite.__name__] = bool(suite(fn))
            except Exception as exc:
                raise RuntimeError(f"Unexpected harness error: {fn.__name__}/{suite.__name__}") from exc
        rows.append({"id": fn.__name__, "label": label, "validByContract": valid,
                     "passes": results})
    totals = []
    for suite, label in SUITES:
        totals.append({"id": suite.__name__, "label": label,
                       "validAccepted": sum(r["validByContract"] and r["passes"][suite.__name__] for r in rows),
                       "validTotal": 2,
                       "invalidRejected": sum(not r["validByContract"] and not r["passes"][suite.__name__] for r in rows),
                       "invalidTotal": 4})
    report = {"scope": "One synthetic task; not TestPrism reproduction or LLM evaluation",
              "python": platform.python_version(), "system": platform.system(),
              "machine": platform.machine(), "cases": CASES, "rows": rows, "suites": totals}
    target = Path(__file__).with_name("test-diversity-results.json")
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    temp.replace(target)
    for s in totals:
        print(f'{s["label"]}: 接受正确实现 {s["validAccepted"]}/2；拦下错误实现 {s["invalidRejected"]}/4')
    print(f'Python {report["python"]}; {report["system"]} {report["machine"]}; synthetic task')


if __name__ == "__main__":
    main()
