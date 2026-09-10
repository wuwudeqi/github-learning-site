研发平台 RAG：核心代码

这套代码面向内部 CI/CD 与代码托管平台的知识问答。资料是编纂的企业 Wiki，平台名、审批规则、地址与错误码均为模拟内容。它们不代表任何真实公司的制度。

先看清代码做到了哪里

1. 真正执行：HTML 正文解析、章节切分、BGE 中文模型编码、Qdrant local 向量查询、BM25、RRF 融合、LangGraph StateGraph。
2. CrossEncoderReranker 包含真实 bge-reranker-base 调用，可用 --rerank 开启。本次已完成开发集与保留集四路对照，见 dev-rerank.metrics.txt、test-retrieval.metrics.txt 和 verification.txt。它没有稳定优于 BM25，默认不启用。
3. 默认 judge 是规则替身，默认 answerer 只抽取原文。这两部分用于检查路由和引用接线，不能用来报告问答正确率。
4. model_api.py 提供显式开启的 HTTP 模型适配。此次交付未使用生成模型凭据，未验证模型判断与答案生成效果。接口需支持 chat/completions 格式和 JSON 输出；不同服务商可能需要调整参数。
5. 没有管理后台、在线抓取登录态、分布式部署和增量索引服务。主实验索引 HTML，PDF 提供按页文本解析接口；同一文档的 PDF 副本不会再次进入索引。

文件怎么读

ingest.py：从本地 HTML 快照中提取 main/article 的 h2 章节。移除导航、页脚、脚本；保留正文链接地址、列表序号、表格行列分隔和代码换行。复杂合并表格、嵌套版式与扫描 PDF 需要另行处理。
chunking.py：先按章节分组，再按模型 tokenizer 控制窗口；384 token 包括标题前缀及特殊 token，长段落重叠 48 token。FastTokenizer 的字符偏移用于回切原文，避免 decode 改写 URL、大小写、中文空格。不是完整的按段落/表格语义切分器。
retrieval.py：BGEEncoder、HybridRetriever、rrf、CrossEncoderReranker。中文 BM25 使用双字切分，英文标识符尽量保留整体。这是容易解释的基线，不是成熟领域分词器。
graph.py：问题整理、版本范围解析、检索、重排/上下文选择、证据判断、一次补检索与终止。候选每轮覆盖，只有 trace 追加。
model_api.py：把 judge 与 answerer 换成真实模型的接入位置。
evaluate.py：读取问题集及 gold_evidence；唯一读取评测答案标注的运行模块。索引器不会读取评测题或参考答案。
demo.py：串起代码的命令行入口。
test_core.py：机制验证，使用固定向量与替身，结果不混进真实模型检索指标。
verify_model.py：额外用真实 tokenizer 验证长文本切块的原文偏移、错误码、向量形状和语料预算。

安装

使用 Python 3.12。以下命令在本 code 目录执行；也可以把相对路径换成绝对路径。

这台机器已留有本次验证环境 /tmp/codex-rag-env 和模型缓存 /tmp/codex-rag-models。如果临时目录还在，可直接复用：

  HF_HOME=/tmp/codex-rag-models HF_HUB_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 /tmp/codex-rag-env/bin/python demo.py '如何申请仓库访问权限？'

临时目录可能被系统清理。换机器或长期保存时，按下面的方式重新创建环境与缓存。

  uv venv /tmp/rag-learning-env --python 3.12
  uv pip install --python /tmp/rag-learning-env/bin/python -r requirements.txt

requirements.txt 是本次实际运行环境的完整版本快照。直接依赖包括 langgraph、qdrant-client、sentence-transformers、rank-bm25、beautifulsoup4、pypdf、httpx、pytest。模型权重另行下载，不在网站或代码包里。

运行控制流和真实检索

  HF_HOME=/tmp/rag-learning-models PYTHONDONTWRITEBYTECODE=1 /tmp/rag-learning-env/bin/python demo.py '如何申请仓库访问权限？'

默认输出中会出现 fixture_judge_and_extract_only。向量查询是真实模型结果，答案部分是带引用的抽取替身。不要把这条输出演示成完整模型问答。

开启重排：

  HF_HOME=/tmp/rag-learning-models PYTHONDONTWRITEBYTECODE=1 /tmp/rag-learning-env/bin/python demo.py '如何申请仓库访问权限？' --rerank

首次需要下载约 GB 量级的重排模型文件；BGE-small 的文件小得多。模型在 CPU 上运行，重排耗时需要单独看。模型 id 与 revision 均写在 retrieval.py，避免主分支更新后换了一套权重却沿用旧结果。

可选真实模型接入

在自己的终端设置 RAG_CHAT_ENDPOINT（完整的 /chat/completions 地址）、RAG_CHAT_MODEL、RAG_CHAT_API_KEY，然后显式追加 --llm。代码不会自动读取其他工具的密钥。不要把密钥写进源码或测试报告。

--llm 会发送当前问题、短历史和最终检索片段给你配置的服务。模型只负责判断和作答，没有执行部署、修改仓库或申请权限的工具。遇到 JSON 格式不合约或引用不一致会显式失败，便于看到接口问题。

检索评测

先读 dev，再定方案。test 留到方案确定后再运行。

  HF_HOME=/tmp/rag-learning-models PYTHONDONTWRITEBYTECODE=1 /tmp/rag-learning-env/bin/python evaluate.py --split dev --output dev-retrieval.metrics.txt
  HF_HOME=/tmp/rag-learning-models PYTHONDONTWRITEBYTECODE=1 /tmp/rag-learning-env/bin/python evaluate.py --split test --output test-retrieval.metrics.txt

如果要比较重排，在这两条命令末尾添加 --rerank。命令同时比较 dense、BM25、hybrid；开启后多一项 hybrid_rerank。已经运行过的保留集，应视为已曝光，后续继续调参时另建新的保留题。

每题保存检索问题、过滤条件、返回 chunk_id 与耗时。报告保存配置、模型 revision、环境版本、manifest hash、实际索引 chunk hash 和问题集 hash。主实验用 K=5；dense 和 BM25 各出最多 20 条后做 RRF，重排路径取融合前 12 条后选 5 条。

section_recall：标注章节中有多少进入前 K 个 chunk。多个重叠块落到同一章节时去重计数。
doc_recall：同样的计算，只把单位改成文档。
mrr：前 K 个 chunk 内第一条命中标注章节的倒数排名，未命中记 0，即 MRR@K。
all_evidence：这道题标注的所有章节都在前 K 个 chunk 中，记 1，否则记 0。它表示“标注章节全覆盖”，不是事实完整性或答案正确率。

clarify/abstain 题不进入普通召回分母。它们留给真实证据判断和端到端问答评测。当前没有输出这两类模型表现的成绩。

重要实现边界

Qdrant 使用内存 local 模式，支持检索代码和 metadata 过滤验证；本实验不衡量服务端 HNSW 近似召回、百万级数据延迟或并发吞吐。
过滤器当前仅持久化 status、version、system。环境等字段保留在 Chunk metadata，尚未实现索引过滤。版本选择是可见的规则基线：本轮明确的版本意图优先；未给新条件时继承上一条用户问题。复杂时间范围仍需要结构化意图抽取与评测。
上下文选择只做 chunk_id 去重和 token 预算。父段补全、邻近块合并、跨文档冲突裁决在文章中作为优化设计展开，当前代码没有实现这些能力。
CrossEncoder 的 max_length=512 是问题与片段的联合限制。代码会检查 pair token 数，超出直接报错，不静默截断。BGE 文档与问题也有预算检查；换入长历史后应先解析本轮检索意图。
RRF 分数不是“答案置信度”。重排分数也不能直接解释成正确概率。
引用检查要求返回的 ID 属于当前上下文，正文标记与 citations 数组相符；它没有判断“这句话是否被这段证据支持”。
HTML 解析假设 h2 是章节边界。换公司 Wiki 后应先检查正文 DOM，而不是直接套选择器。PDF 不具备 HTML 的稳定 h2 section_id，本示例按 page-N 追溯；接入主索引前还要设计跨页段落与同源去重。

机制检查

  PYTHONDONTWRITEBYTECODE=1 /tmp/rag-learning-env/bin/python -m pytest -q -p no:cacheprovider test_core.py

这些检查覆盖 HTML 来源、切块、RRF、Qdrant 过滤、版本继承、LangGraph 候选替换和重试上限、引用一致性、部分召回的计分、语料标注及 family 隔离。

实现核对的官方资料

LangGraph StateGraph：https://docs.langchain.com/oss/python/langgraph/graph-api
BGE 中文模型与检索指令：https://huggingface.co/BAAI/bge-small-zh-v1.5
BGE 重排模型：https://huggingface.co/BAAI/bge-reranker-base
Sentence Transformers CrossEncoder：https://sbert.net/docs/cross_encoder/usage/usage.html
Qdrant Python local 示例：https://github.com/qdrant/qdrant-client
pypdf 文本提取限制：https://pypdf.readthedocs.io/en/stable/user/extract-text.html
