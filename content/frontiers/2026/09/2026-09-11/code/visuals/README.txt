# 2026-09-11 配图来源与复现

配图按“对应来源原图 → imagegen → HTML/JS”的顺序选择。23 幅最终图片中，14 幅来自对应来源，2 幅为 AI 概念图，7 幅用于需要精确对应的时序、组件与合成数据结果。没有按固定数量补图；本轮替换原有解释效果较弱的图，并保留仍有用的精确图。

## 来源原图

下表仅引用对应材料中直接帮助解读的一幅图，不再分发整篇论文。原图未重绘、未改数字；完整保留图例和必要条件。SWE-2 为官方网页中整张结果表的截图；推理片段论文为 PDF 第 5 页图 3 的区域截取，保留三面板、坐标、图例及原图注。其余直接保存来源图片字节。

| 图片 | 作者或机构 / 来源 | 引用内容 |
| --- | --- | --- |
| [news-agents-original.webp](../../images/news-agents-original.webp) | [OpenAI](https://openai.com/index/introducing-the-agents-api/) | 应用、Agents API、Sandbox 三列及双向任务和工具消息，虚线标出应用对自有计算环境的控制 |
| [news-swe2-original.png](../../images/news-swe2-original.png) | [Cognition](https://cognition.com/blog/swe-2) | Cognition 官方四项编码基准表，SWE-2 的 Terminal-Bench 2.1 为 92.8%，Terminal-Bench 4 为 27.3% |
| [model-yue-original.png](../../images/model-yue-original.png) | [Multimodal Art Projection / YuE 团队](https://huggingface.co/m-a-p/YuE2-3B) | YuE 原始架构图展示乐谱、语义 token、声学潜表示与 VAE，并区分 AR 和 NAR 分支 |
| [model-llada-original.jpg](../../images/model-llada-original.jpg) | [inclusionAI / LLaDA-Image 团队](https://github.com/inclusionAI/LLaDA-Image) | LLaDA 官方四组编辑前后示例：人物动作、甜品替换、线稿上色和海报单词修改 |
| [paper-agentgrad-original.png](../../images/paper-agentgrad-original.png) | [Jaewon Chu 等](https://arxiv.org/html/2609.08572v1#S1.F1) | AgentGrad 原图四面板对照目标定位、Agent 级监督，以及随机分组和语义聚类 |
| [paper-parser-original.svg](../../images/paper-parser-original.svg) | [Kun Li 等](https://arxiv.org/html/2609.06702v1#S3.F1) | PARSER 原始方法图对比顺序记忆链与按轮并行读取全部文档块 |
| [paper-swe-verified-original.png](../../images/paper-swe-verified-original.png) | [Pujun Zheng 等](https://arxiv.org/html/2609.08149v1#S3.F2) | SWE-Bench Pro Verified 原图分别展示对 731 题的反泄漏处理，以及 102 道题的修订流程 |
| [paper-phi-original.png](../../images/paper-phi-original.png) | [Leilei Ding 等](https://arxiv.org/html/2609.10226v1#Sx2.F2) | Φ-Bench 原始流程从资料筛选和三类任务构造，进入正确性检查与最终奖励 |
| [paper-traces-original.png](../../images/paper-traces-original.png) | [Jaehui Hwang 等](https://arxiv.org/pdf/2609.07103) | 推理片段原始消融曲线：相同删除比例下，删中间段后答案相似度高于删开头或结尾 |
| [paper-datpo-original.png](../../images/paper-datpo-original.png) | [Youngjun Yu 等](https://arxiv.org/html/2609.08650v1#S3.F3) | DATPO 原图展示难度自适应分支、句子熵分叉点，以及只给正优势块的多样性奖励 |
| [project-paperless-original.png](../../images/project-paperless-original.png) | [Paperless-ngx 维护者](https://github.com/paperless-ngx/paperless-ngx) | Paperless 维护者原始界面：文档缩略图、标签、文档类型和日期筛选 |
| [project-lightrag-original.png](../../images/project-lightrag-original.png) | [LightRAG 作者 / HKUDS](https://github.com/HKUDS/LightRAG) | LightRAG 原图展示图索引建立、双层关键词检索，以及带原文块编号的实体关系 |
| [project-comfy-original.jpg](../../images/project-comfy-original.jpg) | [Comfy Org](https://docs.comfy.org/tutorials/basic/text-to-image) | ComfyUI 官方 A 至 F 工作流截图，完整保留模型加载、提示编码、采样、VAE 解码与保存的连线 |
| [project-opik-original.png](../../images/project-opik-original.png) | [Comet / Opik 维护者](https://www.comet.com/docs/opik/tracing/log_traces) | Opik 官方追踪界面显示 SQL 任务的嵌套 spans、输入输出，以及加入数据集的入口 |

SWE-Bench Pro Verified 与 DATPO 原文使用 CC BY 4.0。其他论文的 arXiv 非独占分发许可不等于允许任意转载；这里只为逐图方法或实验解读引用一幅原图，并保留作者、图号与原始阅读入口。YuE 的 CC BY-NC 权重许可、项目代码许可和图像素材的权利范围分别记录，不将前者自动套用到所有图像。原始材料中第三方内容仍归相应权利人。

## AI 概念图

- [局部音乐编辑](../../images/news-suno-edit-concept.png)：Suno v6 公告配图为海报，帮助页为 Logo，不能解释选段与接缝，因此用内置 imagegen 生成音乐段落示意。波形为虚构，前后段一致表示编辑意图，仍需实际回听。
- [同一空间的两个视点](../../images/news-spatial-viewpoints.png)：对应 ABot-Earth 0.7 公告没有可用的双视点图，其他 ABot-Recon 图片属于不同事件。沿用本期已经校正的 AI 空间概念图，不表示高德产品实际效果。

完整提示词、采用的工具输出路径和项目路径见 [imagegen-prompts.json.txt](imagegen-prompts.json.txt)。

## HTML/JS 精确图

保留七幅本站原创图的构图，将几何、文字和样式存入 [diagrams.json.txt](diagrams.json.txt)，由 [render.js](render.js) 确定性生成 SVG；没有把来源原图转换成本站原创图。逐图跳过前两层的原因保存在该场景数据和来源审计中。

用浏览器打开 [复现页面](index.html) 可预览和下载；也可从仓库根目录运行：

```bash
node content/frontiers/2026/09/2026-09-11/code/visuals/render-diagrams.mjs
```

配对矩阵的四格计数、通过率和差值来自本轮实际运行 `compare_runs.py` 保存的 [practice-result.json.txt](practice-result.json.txt)。这是六条人工合成样本的计算结果，不是模型性能实验。若要更新结果，先重新运行该脚本并保存 JSON，再执行导出。

- **overview-map**：本站当期阅读路线，没有对应外部原图；图中栏目和数量需要精确对应站内文档，采用 HTML/JS。
- **news-deepseek-routing**：官方公告与定价页没有 API 别名迁移图；日期、别名与目标必须逐项准确，AI 场景图无法提供可复核的路由，采用 HTML/JS。
- **news-live-duplex**：官方页面提供音频和基准结果，未提供前后台调用时序图；需要明确谁向谁发消息及用户插话的位置，采用 HTML/JS，无延迟测量。
- **model-lingbot-assets**：模型卡的 teaser 展示生成效果，未标出 1.3B 包和共享 assets_dir 的依赖；准确组件连线比 AI 场景更适合此处，采用 HTML/JS。
- **model-north-parameters**：模型卡文字列出总参数与激活参数，没有权重存储比例图；数值比例与容量计算不能交给生成式图像，采用 HTML/JS。
- **practice-match-ids**：本期原创合成样本没有外部原图；必须按真实 id 连线，AI 图不能冒充实际配对，采用 HTML/JS。
- **practice-paired**：本期实际运行的合成数据结果没有外部原图，不能用 AI 图伪造结果；HTML/JS 从 practice-result.json.txt 计算四格数量和通过率。
