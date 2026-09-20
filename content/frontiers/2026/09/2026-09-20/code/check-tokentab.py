"""Run the upstream Claude parser on a synthetic fixture, never on personal logs.
Usage: python3 check-tokentab.py /path/to/tokentab-checkout
"""
import dataclasses
import datetime
import json
import pathlib
import subprocess
import sys
import tempfile

checkout = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(checkout))
from tokentab.providers import claude

with tempfile.TemporaryDirectory(prefix="frontiers-tokentab-fixture-") as directory:
    config = pathlib.Path(directory)
    folder = config / "projects" / "synthetic-project"
    folder.mkdir(parents=True)
    first = {"timestamp": "2026-09-19T10:00:00Z", "message": {
        "role": "assistant", "id": "synthetic-1", "model": "test-model",
        "content": [], "usage": {"input_tokens": 100, "output_tokens": 20,
        "cache_read_input_tokens": 50, "cache_creation_input_tokens": 10}}}
    second = {"timestamp": "2026-09-19T10:01:00Z", "message": {
        "role": "assistant", "id": "synthetic-2", "model": "test-model",
        "content": [], "usage": {"input_tokens": 40, "output_tokens": 5}}}
    (folder / "session.jsonl").write_text("\n".join(json.dumps(x) for x in [first, first, second]))
    claude._config_dir = lambda: config
    records = claude.collect()
    totals = {key: sum(getattr(record.tokens, key) for record in records)
              for key in ["input", "output", "cache_read", "cache_write"]}
    assert len(records) == 2, "duplicate message must not be billed twice"
    assert totals == dict(input=140, output=25, cache_read=50, cache_write=10)
    print(json.dumps({
        "kind": "synthetic parser fixture; not real account usage or billing",
        "checkedAt": datetime.datetime.now().astimezone().isoformat(),
        "python": sys.version.split()[0],
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip(),
        "inputRows": 3, "uniqueRecords": len(records), "totals": totals,
        "result": "passed", "scope": "Claude parser only; no price or GUI check",
    }, ensure_ascii=False, indent=2))
