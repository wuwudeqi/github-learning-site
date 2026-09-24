"""Small synthetic order-bias demonstration, not an LLM benchmark."""
import json, random, platform
from pathlib import Path
from datetime import datetime, timezone

rng = random.Random(42)
n = 10000
truth = [i % 2 for i in range(n)]  # correct semantic option: 0 or 1
rng.shuffle(truth)
rows = []
strategies = ["每次独立猜", "总选第一个位置", "稳定但仅七成题正确", "总选正确内容"]
for name in strategies:
    first = []
    second = []
    for i, answer in enumerate(truth):
        if name == "每次独立猜":
            a, b = rng.randrange(2), rng.randrange(2)
        elif name == "总选第一个位置":
            a, b = 0, 0
        else:
            semantic = answer if name == "总选正确内容" or i % 10 < 7 else 1-answer
            a, b = semantic, 1-semantic
        first.append(a)
        second.append(b)
    correct1 = sum(a == t for a, t in zip(first, truth))
    correct2 = sum(b == 1-t for b, t in zip(second, truth))
    both = sum(a == t and b == 1-t for a, b, t in zip(first, second, truth))
    same = sum(a == 1-b for a, b in zip(first, second))
    rows.append(dict(strategy=name,meanAccuracy=(correct1+correct2)/(2*n),
                     bothCorrect=both/n,semanticConsistency=same/n,
                     correctFirst=correct1,correctSwapped=correct2,bothCount=both,consistentCount=same))
result = dict(kind="本机运行的合成教学示例；没有调用任何模型或真实基准",
              seed=42,n=n,python=platform.python_version(),platform=platform.system()+" "+platform.machine(),
              executedAt=datetime.now(timezone.utc).isoformat(),rows=rows)
out = Path(__file__).with_name("order-results.json")
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
for r in rows:
    print(r["strategy"],"平均单次",f'{r["meanAccuracy"]:.2%}',"两序都对",f'{r["bothCorrect"]:.2%}',"内容一致",f'{r["semanticConsistency"]:.2%}')
