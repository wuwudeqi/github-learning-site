"""Reproduce shares from the original weekly rows archived in ramp-weekly.json."""
from pathlib import Path
import json
from collections import defaultdict
j=json.loads(Path(__file__).with_name('ramp-weekly.json').read_text())
s=defaultdict(float)
for r in j['rows']: s[r['model_maker']]+=r['metric_value']
for maker,spend in sorted(s.items(),key=lambda x:-x[1]): print(maker, round(100*spend/sum(s.values()),3))
