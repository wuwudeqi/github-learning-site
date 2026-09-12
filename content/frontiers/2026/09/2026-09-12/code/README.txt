2026-09-12 前沿日报配套材料

event_loop_probe.py：Python 标准库实验。每种模式各做五次相同计算；只比较协作式调度，不是并行计算实验。
results.json.txt：本机实际运行环境、每轮计算校验值、耗时与所有心跳时间点。后缀保留 .txt，以便作为网站附件分发。
render-figures.mjs：无外部依赖的 JavaScript 制图脚本，读取上述数据，生成三幅 SVG 和可切换的 figures.html。
imagegen-prompts.json.txt：场景创作概念图的最终提示词、来源候选取舍、采用路径和检查记录。

复现实验（Python 3.11+）：
python3 event_loop_probe.py --output my-results.json.txt

重绘本期图（Node.js 18+）：
node render-figures.mjs

原始 results.json.txt 保留本期结果。若需要绘制自己的结果，请复制整个目录后，将新结果保存为 results.json.txt，再重绘。
figures.html 已嵌入绘制结果，可直接打开。以 HTTP 服务打开时还能访问同目录源码与数据。

为何使用 HTML / JS：
Kimi 官方模型规格主要为表格，DeepSeek 更新日志和价格页主要为文字；两图需要准确保持别名、条件分支和日期，生成式绘图没有增加解释价值。
技术实践展示本期实际运行时间点，来源中不存在本次实验的原图；不适合让生成式工具绘制数值。图形由原始时间戳直接计算。

原始来源：
https://www.kimi.com/code/docs/kimi-code/models.html
https://www.kimi.com/code/docs/kimi-code/whats-new.html
https://api-docs.deepseek.com/updates/
https://api-docs.deepseek.com/quick_start/pricing
https://docs.python.org/3/library/asyncio-task.html#sleeping
