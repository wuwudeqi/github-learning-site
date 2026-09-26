"""Recalculate published conditional rates; this does not rerun the agent evaluation."""
import json
import platform
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = 'https://commandline.microsoft.com/run-assert-eval-responsible-ai-agent-risk-discovery-at-runtime/'
rows = [
    dict(label='基线', violations=12, applicable=40),
    dict(label='加入运行时策略', violations=2, applicable=34),
]
for row in rows:
    k, n = row['violations'], row['applicable']
    if n <= 0 or not 0 <= k <= n:
        raise ValueError('Invalid applicable-conversation counts')
    row['rate'] = k / n
result = dict(
    python=platform.python_version(), source=SOURCE, rows=rows,
    percentage_point_drop=100 * (rows[0]['rate'] - rows[1]['rate']),
    relative_rate_drop=1 - rows[1]['rate'] / rows[0]['rate'],
    relative_count_drop=1 - rows[1]['violations'] / rows[0]['violations'],
    limitation='Different applicable subsets; no causal estimate or paired test from aggregate counts.',
)
(HERE/'recount-results.txt').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
output = '\n'.join(f"{r['label']}: {r['violations']}/{r['applicable']} = {100*r['rate']:.4f}%" for r in rows)
output += f"\n占比差: {result['percentage_point_drop']:.4f} 个百分点\n占比相对降幅: {100*result['relative_rate_drop']:.4f}%\n次数相对降幅: {100*result['relative_count_drop']:.4f}%\n"
(HERE/'recount-output.txt').write_text(output)
print(output)
