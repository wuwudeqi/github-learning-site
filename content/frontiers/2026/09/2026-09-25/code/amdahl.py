"""Amdahl illustration. Synthetic stage durations, not model measurements."""
import json
import platform
from pathlib import Path
from datetime import datetime, timezone

BASE_MS = 100
DECODE_SPEEDUP = 3
rows = []
for share in (0.2, 0.5, 0.8):
    fixed_ms = BASE_MS * (1 - share)
    decode_before_ms = BASE_MS * share
    decode_after_ms = decode_before_ms / DECODE_SPEEDUP
    total_after_ms = fixed_ms + decode_after_ms
    rows.append({"decode_share": share, "fixed_ms": round(fixed_ms, 6),
                 "decode_before_ms": decode_before_ms,
                 "decode_after_ms": round(decode_after_ms, 6),
                 "total_before_ms": BASE_MS,
                 "total_after_ms": round(total_after_ms, 6),
                 "overall_speedup": round(BASE_MS / total_after_ms, 6),
                 "infinite_decode_limit": round(1 / (1 - share), 6)})
result = {"kind": "synthetic-stage-duration-calculation", "measured_model_latency": False,
          "python": platform.python_version(), "ran_at": datetime.now(timezone.utc).isoformat(),
          "decode_speedup": DECODE_SPEEDUP, "rows": rows,
          "assumptions": ["serial stages", "fixed work unchanged", "no added draft overhead", "same input/output task"]}
Path(__file__).with_name("amdahl-results.txt").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
for r in rows:
    print(f"decode {r['decode_share']:.0%}: 100ms -> {r['total_after_ms']:.3f}ms; overall {r['overall_speedup']:.3f}x; limit {r['infinite_decode_limit']:.2f}x")
