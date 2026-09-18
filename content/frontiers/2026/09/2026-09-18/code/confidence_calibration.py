"""Synthetic, deterministic illustration of retrospective calibration; no LLM calls."""
import datetime
import json
import platform
from pathlib import Path

GROUPS = ["字段抽取", "代码判断", "多步问题"]


def dataset(prefix, successes):
    return [dict(id=f"{prefix}-{g}-{i}", group=g, stated=0.9, correct=int(i < n))
            for g, n in zip(GROUPS, successes) for i in range(20)]


def scores(rows, probabilities):
    n = len(rows)
    brier = sum((p - r["correct"]) ** 2 for r, p in zip(rows, probabilities)) / n
    ece = 0.0
    for b in range(10):
        idx = [i for i, p in enumerate(probabilities) if min(9, int(p * 10)) == b]
        if idx:
            gap = abs(sum(probabilities[i] for i in idx) / len(idx)
                      - sum(rows[i]["correct"] for i in idx) / len(idx))
            ece += len(idx) / n * gap
    selected = [i for i, p in enumerate(probabilities) if p >= 0.8]
    return dict(brier=brier, ece10=ece, coverage=len(selected) / n,
                acceptedAccuracy=(sum(rows[i]["correct"] for i in selected) / len(selected)
                                  if selected else None), accepted=len(selected), count=n)


def run():
    bank = dataset("past", [18, 12, 6])
    heldout = dataset("future", [17, 13, 7])
    drift = dataset("shifted", [6, 12, 18])
    assert not ({r["id"] for r in bank} & {r["id"] for r in heldout + drift})
    # Fit from the past bank only. Future outcomes are read only for evaluation.
    fitted = {}
    for group in GROUPS:
        rows = [r for r in bank if r["group"] == group]
        fitted[group] = (sum(r["correct"] for r in rows) + 1) / (len(rows) + 2)
    global_prior = (sum(r["correct"] for r in bank) + 1) / (len(bank) + 2)
    assert all(0 < p < 1 for p in fitted.values())
    results = {}
    for name, rows in [("heldout", heldout), ("drift", drift)]:
        results[name] = {
            "stated": scores(rows, [r["stated"] for r in rows]),
            "globalPrior": scores(rows, [global_prior] * len(rows)),
            "groupCalibrated": scores(rows, [fitted[r["group"]] for r in rows]),
        }
    output = dict(kind="synthetic-illustration-not-paper-reproduction",
                  executedAt=datetime.datetime.now().astimezone().isoformat(),
                  python=platform.python_version(), platform=platform.platform(),
                  calibration="Laplace-smoothed historical success by manually specified group",
                  validation="Disjoint example IDs; probabilities fitted only on bank; 10 fixed ECE bins; decision threshold 0.8",
                  groups=[dict(name=g, bankSuccess=sum(r["correct"] for r in bank if r["group"] == g),
                               bankCount=20, probability=fitted[g],
                               heldoutAccuracy=sum(r["correct"] for r in heldout if r["group"] == g)/20,
                               driftAccuracy=sum(r["correct"] for r in drift if r["group"] == g)/20)
                          for g in GROUPS],
                  datasets=dict(bank=bank, heldout=heldout, drift=drift), results=results)
    path = Path(__file__).with_name("confidence-results.json.txt")
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"executedAt": output["executedAt"], "python": output["python"],
                      "groups": output["groups"], "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
