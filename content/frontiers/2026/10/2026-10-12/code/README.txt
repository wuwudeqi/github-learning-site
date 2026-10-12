# 本期附件复现

- `candidate_walk.py` 需要 Python 3.10+ 标准库。运行 `python3 candidate_walk.py > candidate-results.json` 生成四组合成结果。
- `grok-cost-data.json` 保存每秒价格、币种、10秒时长与官方来源；`grok-cost.html` 内嵌相同数据用于离线绘图。
- `candidate-results.html` 内嵌当次 JSON；若重跑更新数据，须同步 HTML 的 `DATA` 对象。
- `maia-paths.html` 是基于官方网络跳数事实的原创解释图，来源与条件写在页面。
- 用浏览器打开三个 HTML，在宽 600 CSS px、设备倍率1的视口完整截图，可复现 `images/` 中对应 PNG。原始运行和截图时间在当期来源审计记录。
