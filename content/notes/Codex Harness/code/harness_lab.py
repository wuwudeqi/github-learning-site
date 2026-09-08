"""Teaching lab only: no model calls and no claim of Codex equivalence."""

import json
import sqlite3
import tempfile
from pathlib import Path


def normalize(items):
    """Small call/output subset; not the full Codex protocol."""
    calls = {item["id"] for item in items if item["type"] == "call"}
    outputs = {item["id"] for item in items if item["type"] == "output"}
    result = []
    for item in items:
        if item["type"] == "output" and item["id"] not in calls:
            continue
        result.append(item)
        if item["type"] == "call" and item["id"] not in outputs:
            result.append({"type": "output", "id": item["id"], "status": "missing"})
    return result


def export(db, operation_id, params, lose_response=False):
    fingerprint = json.dumps(params, sort_keys=True, ensure_ascii=False)
    db.execute("BEGIN IMMEDIATE")
    try:
        existing = db.execute(
            "SELECT params, artifact_id FROM operations WHERE id = ?", (operation_id,)
        ).fetchone()
        if existing:
            if existing[0] != fingerprint:
                raise ValueError("operation ID reused with different parameters")
            artifact_id = existing[1]
        else:
            artifact_id = db.execute(
                "INSERT INTO artifacts(payload) VALUES (?)", (fingerprint,)
            ).lastrowid
            db.execute(
                "INSERT INTO operations VALUES (?, ?, ?)",
                (operation_id, fingerprint, artifact_id),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    if lose_response:
        raise TimeoutError("injected after commit, before response")
    return artifact_id


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS:", message)


def main():
    marker = "ERROR: invalid empty input"
    log = "info: healthy\n" * 80 + marker + "\n" + "info: healthy\n" * 80
    budget = 160
    prefix = log[:budget]
    position = log.index(marker)
    focused = log[max(0, position - 30):max(0, position - 30) + budget]
    check(len(prefix) <= budget and len(focused) <= budget, "equal character budget respected")
    check(marker not in prefix and marker in focused, "middle evidence lost by prefix, retained by targeted excerpt")

    history = normalize([
        {"type": "call", "id": "a"},
        {"type": "call", "id": "b"},
        {"type": "output", "id": "b", "status": "ok"},
        {"type": "output", "id": "orphan", "status": "ok"},
    ])
    check(history == [
        {"type": "call", "id": "a"},
        {"type": "output", "id": "a", "status": "missing"},
        {"type": "call", "id": "b"},
        {"type": "output", "id": "b", "status": "ok"},
    ], "history paired; missing result is never fabricated as success")
    check(normalize(history) == history, "normalization is idempotent for this protocol subset")

    with tempfile.TemporaryDirectory(prefix="harness-lab-") as directory:
        path = Path(directory) / "lab.sqlite"
        db = sqlite3.connect(path)
        db.executescript("""
            CREATE TABLE artifacts(id INTEGER PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE operations(id TEXT PRIMARY KEY, params TEXT NOT NULL,
                                    artifact_id INTEGER NOT NULL);
        """)
        params = {"department": "demo", "snapshot": "v1"}
        timed_out = False
        try:
            export(db, "op-1", params, lose_response=True)
        except TimeoutError:
            timed_out = True
        check(timed_out, "response failure injected after transaction commit")
        db.close()
        db = sqlite3.connect(path)
        original = db.execute("SELECT artifact_id FROM operations WHERE id='op-1'").fetchone()[0]
        retried = export(db, "op-1", params)
        check(original == retried and db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 1,
              "retry after reconnect reuses the committed artifact")
        rejected = False
        try:
            export(db, "op-1", {"department": "demo", "snapshot": "v2"})
        except ValueError:
            rejected = True
        check(rejected and db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 1,
              "same operation ID with changed parameters is rejected without side effects")
        second = export(db, "op-2", params)
        check(second != original and db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 2,
              "explicit new operation can create another artifact with identical parameters")
        db.close()
    print("Scope: teaching subset, same-database transaction; no LLM, no external file export.")


if __name__ == "__main__":
    main()
