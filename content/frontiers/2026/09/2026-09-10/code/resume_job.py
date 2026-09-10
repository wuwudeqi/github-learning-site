"""Single-worker checkpoint demo. No network, model calls, or publishing."""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

FILES = ("draft.md", "sources.txt")


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=".pending-", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def save(path, state):
    state["updatedAt"] = datetime.now(timezone.utc).isoformat()
    atomic_write(path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def hashes(folder):
    return {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
            for name in FILES}


def verify(folder, issue_date, expected):
    if not all((folder / name).is_file() for name in FILES):
        raise ValueError("目标日期材料不完整")
    if not (folder / "draft.md").read_text(encoding="utf-8").startswith(
        f"# 演示任务 {issue_date}\n"
    ):
        raise ValueError("稿件日期不匹配")
    if hashes(folder) != expected:
        raise ValueError("内容已改变，不能沿用旧核验结果")


def run(root, issue_date, stop_after_draft=False):
    if date.fromisoformat(issue_date).isoformat() != issue_date:
        raise ValueError("日期必须为 YYYY-MM-DD")
    folder = root / issue_date
    state_path = folder / "state.json"
    state = (json.loads(state_path.read_text(encoding="utf-8"))
             if state_path.exists() else
             {"issueDate": issue_date, "stage": "preparing"})
    if state.get("issueDate") != issue_date:
        raise ValueError("进度日期不匹配")
    if state.get("stage") not in {"preparing", "drafted", "complete"}:
        raise ValueError("无法识别的阶段；请检查已有进度")

    if state["stage"] == "preparing":
        save(state_path, state)
        atomic_write(folder / "draft.md",
                     f"# 演示任务 {issue_date}\n\n这是固定演示材料，不是真实日报。\n")
        atomic_write(folder / "sources.txt",
                     f"issueDate={issue_date}\n来源：本地固定样例，无外部事实。\n")
        state.update(stage="drafted", artifactHashes=hashes(folder))
        save(state_path, state)

    if stop_after_draft and state["stage"] == "drafted":
        print("已保存 drafted；模拟中断，退出码 75")
        return 75

    # Even a completed state must pass verification again.
    try:
        verify(folder, issue_date, state.get("artifactHashes", {}))
    except (OSError, ValueError) as error:
        state["stage"] = "drafted"
        state.pop("receipt", None)
        (folder / "receipt.json").unlink(missing_ok=True)
        state["lastError"] = str(error)
        save(state_path, state)
        raise
    was_complete = state["stage"] == "complete"
    receipt = {"issueDate": issue_date, "artifactHashes": state["artifactHashes"],
               "verifiedAt": datetime.now(timezone.utc).isoformat(),
               "scope": "local-demo-only"}
    save(folder / "receipt.json", receipt)
    state.update(stage="complete", receipt="receipt.json")
    state.pop("lastError", None)
    save(state_path, state)
    print("已核验，跳过生成" if was_complete else "已恢复并完成本地核验")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--root", type=Path, default=Path("checkpoint-demo"))
    parser.add_argument("--stop-after-draft", action="store_true")
    args = parser.parse_args()
    try:
        return run(args.root, args.date, args.stop_after_draft)
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
