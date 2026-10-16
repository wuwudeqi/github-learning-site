"""Synthetic, local demonstration: denial tests need an allowed-operation control.

No model, network, external files, or production sandbox is involved.
Python >= 3.10, standard library only.
"""
import json
import platform
import tempfile
from pathlib import Path


def read_file(root, relative, strategy):
    if strategy == "deny_all":
        raise PermissionError("denied")
    target = (root / relative).resolve()
    if strategy == "bounded" and not target.is_relative_to(root.resolve()):
        raise PermissionError("outside toy workspace")
    return target.read_text(encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory(prefix="frontiers-positive-control-") as tmp:
        base = Path(tmp)
        root = base / "workspace"
        root.mkdir()
        (root / "allowed.txt").write_text("synthetic allowed content", encoding="utf-8")
        (base / "outside.txt").write_text("synthetic outside content", encoding="utf-8")
        (root / "outside-link.txt").symlink_to(base / "outside.txt")
        cases = [
            ("allowed", "allowed.txt", "synthetic allowed content"),
            ("parent_traversal", "../outside.txt", None),
            ("symlink_escape", "outside-link.txt", None),
        ]
        results = []
        for strategy in ["deny_all", "bounded", "allow_all"]:
            observations = []
            for name, relative, expected in cases:
                try:
                    value = read_file(root, relative, strategy)
                    passed = expected is not None and value == expected
                    outcome = "read"
                except PermissionError:
                    passed = expected is None
                    outcome = "denied"
                observations.append({"case": name, "outcome": outcome, "passed": passed})
            positive = observations[0]["passed"]
            negative_passes = sum(x["passed"] for x in observations[1:])
            results.append({"strategy": strategy, "allowed_control_passed": positive,
                            "negative_passed": negative_passes, "negative_total": 2,
                            "joint_pass": positive and negative_passes == 2,
                            "observations": observations})
        return {"python": platform.python_version(), "platform": platform.system(),
                "synthetic": True, "model_calls": 0, "results": results}


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
