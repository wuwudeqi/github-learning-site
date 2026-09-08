---
id: budget-agent-design
title: Agent 项目｜Agent 设计与执行流程
category: 笔记
author: 个人整理
date: "2026-09-08"
description: 单 Agent 的状态、工具契约、路由、追问、上下文和恢复设计。
tags: [LangGraph, 工具调用, 状态管理, Agent]
---

# Agent 设计与执行流程

## 1. 编排方式

采用受控状态图：固定节点保障权限、校验、版本绑定和副作用处理；模型用于理解问题、选择下钻方向和组织解释。这是包含 Agent 决策的工作流，不把整个系统描述成完全自主规划。

![Agent 执行流程](./images/flow.svg)

## 2. 状态设计

以下是数据契约示意，不是可直接运行的框架代码。

```python
from typing import TypedDict

class AnalysisState(TypedDict):
    run_id: str
    thread_id: str
    request_text: str
    query_plan: dict | None
    plan_revision: int
    missing_fields: list[str]
    validated_plan_id: str | None
    clarification: dict | None
    release_id: str | None
    metric_version: str | None
    evidence_refs: list[str]
    visited_queries: list[str]
    step_count: int
    deadline_at: str
    termination_reason: str | None
    skill_revision: str | None
    tool_catalog_hash: str | None
    validated_query_id: str | None
    result_ids: list[str]
    artifact_job_id: str | None
    export_operation_id: str | None
    export_task_id: str | None
    status: str
```

身份、授权与凭证放在服务端可信执行上下文，不由模型输出决定。持久化状态也不是授权依据：恢复任务和下载时仍然重新鉴权。

状态保存计划与证据引用，不保存完整大表。证据对象单独存储，包含归属、版本、查询摘要和保留期。并行节点更新集合时使用明确的合并规则，或先汇集结果再由一个节点更新，防止覆盖与重复。

## 3. 节点与路由

下面是基础指标路径。目标版本在 understand 后增加 Skill 选择与按需加载；validate_plan 按标准指标/探索 SQL 分支，后者加入 schema 检索、SQL 生成和校验。查询节点返回统一 result_id，最终交付调用产物服务。具体展开见第 07～10 篇，恢复与权限检查仍由固定节点承担。

| 节点 | 工作 | 后续路由 |
| --- | --- | --- |
| understand | 提取任务目标及候选指标 | resolve_metrics |
| resolve_metrics | 获取相关指标与合法维度 | clarify 或 validate_plan |
| clarify | 保存缺失条件，暂停等待回答 | 回答后重新校验计划 |
| validate_plan | 后端校验参数与授权，绑定数据和定义版本，创建有效计划 | query_summary 或明确错误 |
| query_summary | 返回计算结果与证据引用 | decide_drilldown |
| decide_drilldown | 模型从允许维度中选择下一步 | drilldown 或 compose |
| drilldown | 执行受控明细分析 | 回到 decide_drilldown |
| compose | 生成事实、说明与待核查项 | verify_answer |
| verify_answer | 数值、引用、权限输出检查 | prepare_export 或 finish |
| prepare_export | 持久化操作 ID 与冻结参数 | submit_export |
| submit_export | 创建或查询已有导出任务 | 返回任务入口 |

循环必须具有硬上限，例如最多三次下钻、重复查询摘要时停止；具体数值为初始实验配置，并非生产最佳值。没有新证据或数据不足时直接结束并说明限制。

## 4. 工具契约

| 工具 | 核心输入 | 输出 |
| --- | --- | --- |
| resolve_metric | 指标关键词与分析意图 | 定义、别名、公式说明、可用维度 |
| validate_query_plan | 指标、组织候选、期间、口径 | 绑定数据与定义版本的有效计划 ID 或结构化错误 |
| query_budget | 有效计划 ID、允许的分组维度 | 汇总、单位、证据 ID、版本 |
| query_detail | 有效计划 ID、明细筛选与分页 | 有界明细、总量、证据 ID |
| create_export | 有效计划 ID、格式；可信层附加操作 ID | 任务 ID 与状态 |
| get_export_status | 任务 ID | 状态、进度、下载入口或错误 |

工具名与字段是项目自定义契约。后端每次检查计划归属、当前权限、版本有效性与查询上限。不能因为模型提供了一个合法格式的计划 ID 就直接执行。

目标版本以 [MCP 工具目录](07-Skills与MCP能力管理.md) 中的查询、SQL 校验、结果读取和产物能力为准。上表用于解释原有领域职责，可由适配器映射；不同时实现两套不同语义的预算查询。query_result 由 Java 管理，图状态只保存 ID 和有界摘要。

统一返回结构：

```json
{
  "ok": true,
  "data": {"budget": "1200000.00", "actual": "1260000.00", "execution_rate": "1.05"},
  "unit": "CNY",
  "result_id": "res-demo-001",
  "release_id": "rel-demo-001",
  "evidence_id": "ev-demo-001",
  "truncated": false
}
```

金额使用十进制字符串传输，后端用精确十进制处理。错误返回 error_code、retryable、用户可理解的信息和 trace_id，不把堆栈、凭证或内部 SQL直接交给模型。

## 5. 模型指令与上下文

模型上下文包含任务目标、相关指标定义、已确认条件、可用工具和有界结果摘要。组织权限由后端执行，提示词仅解释行为边界。

指令约束：不得自行编造指标与组织；缺少关键条件必须返回 clarification；数值只能引用工具证据；业务原因必须关联说明来源；检索内容和用户输入不能修改工具授权或系统规则。

结构化输出只保证结果满足某种结构约束，不能保证业务含义正确，因此仍需校验指标组合、组织映射和期间范围。[LangChain 结构化输出文档](https://docs.langchain.com/oss/python/langchain/structured-output)

会话记录用于理解“换成下半年”等跟进问题。新问题如果改变期间、组织或预算口径，需要生成新有效计划，并使旧的证据与导出参数失效。不同 run 的数据不能仅因同一会话而混用。

## 6. 追问与人工介入

用户没有说明预算版本，且系统没有合法默认规则时，生成一个具体问题：“采用年初预算还是调整后预算？”保存当前状态后等待。恢复接口校验 thread/run 归属、当前等待状态以及回答是否针对同一计划版本。

LangGraph 的 interrupt 可以暂停等待输入；恢复时相关节点可能重新从头执行，因此 interrupt 前的逻辑需可重复执行，外部副作用应拆成独立节点并实现幂等。[官方 interrupts 文档](https://docs.langchain.com/oss/python/langgraph/interrupts)

本项目查询和用户明确要求的导出无需额外审批。人工介入主要用于口径澄清，不人为增加每一步确认。

## 7. 持久化与恢复

开发演示可以用文件型存储，故障恢复实验使用持久化 checkpointer；纯内存状态不能证明跨进程恢复。检查点负责图状态，业务任务表负责操作执行事实，两者通过稳定操作 ID 关联。[LangGraph 持久化文档](https://docs.langchain.com/oss/python/langgraph/persistence)

同一 run 的恢复请求必须串行化或用版本比较控制，避免两个恢复同时执行。进程重启后先读取任务状态，不盲目重发所有工具。

分析执行状态由 Python 统一管理，Java 只维护请求归属与 run_id 映射。Python 的受理事务写入 QUEUED 任务，后台 Worker 认领并驱动图；不能只在 HTTP 路由里启动内存协程。request_id 在受信用户范围内唯一，相同请求重试返回相同 run_id；同一 ID 携带不同内容应报冲突。恢复答案也用 command_id 去重并校验等待版本。

停止包括：完成、需要用户输入、不可恢复错误、达到时间/步数预算和取消。首版页面轮询任务；后续若增加 SSE，连接断开仅停止传输。显式取消通过单独接口发出，在节点安全边界检查标记；已创建的导出任务需独立取消，不能认为取消 Agent 自动撤销业务操作。

## 8. 深入面试：一次完整的“观察—决策—行动”

只有状态图还不足以体现 Agent。需要把模型在每一轮看到了什么、允许决定什么、程序否决什么说清楚。

### 一条具体的执行轨迹

以下是合成案例设计，不是实际模型运行记录。

| 步骤 | 已有观察 | 下一动作 | 谁作决定 |
| --- | --- | --- | --- |
| 1 | 用户要求“上半年研发预算执行” | 询问年初还是调整后预算 | 规则检测关键字段缺失，模型组织追问 |
| 2 | 用户确认调整后预算、实际发生额 | 创建绑定 rel-001 的计划 | Java 校验并创建 |
| 3 | 预算 120 万、实际 126 万 | 选择按费用类别拆分 | 模型从允许维度中选择 |
| 4 | 外协差异 +8 万、设备差异 -2 万 | 下钻外协相关项目 | 模型根据结果选择；程序校验过滤收窄 |
| 5 | P01 外协贡献 +7 万，其他外协 +1 万 | 读取 P01 可访问的说明，或标记缺少原因证据 | 模型选择是否需要补充证据 |
| 6 | 已定位主要贡献，没有业务说明 | 返回差异事实和待核查项 | 程序检查停止条件，模型写解释 |

“外协超支主要集中在 P01”可以由数据支持；“供应商涨价导致超支”不能由这组金额推出。若没有业务说明，必须保持为未确定原因。

### 模型动作契约

模型返回一个有界动作，而不是任意 Python 或 SQL。示意：

```json
{
  "action": "DRILL_DOWN",
  "dimension": "project",
  "filters": [{"field": "expense_category", "op": "EQ", "value": "OUTSOURCE"}],
  "evidence_refs": ["ev-category-001"],
  "reason_code": "LOCATE_VARIANCE_CONTRIBUTOR"
}
```

reason_code 是供用户和排查使用的简短决策依据，不要求输出模型内部思维链。执行器校验 dimension 在计划允许列表、filters 不扩大组织和时间范围、evidence_refs 属于当前计划、动作未重复且预算尚有余额。

如果模型提出按“供应商”下钻，而预算仅有费用类别粒度，后端返回 UNSUPPORTED_DIMENSION；不能拿付款单供应商维度去伪造预算分摊。

## 9. 工具设计：粒度、描述和协议匹配

### 为什么不用一个 execute_sql 工具

它把指标口径、连接路径、权限与查询成本同时交给模型判断；执行成功也无法说明结果正确。反过来，为每张报表建立一个工具又会产生大量语义相近的工具，增加选择错误和提示长度。

本项目采用“少量能力型工具 + 受限查询计划”：查询预算执行、下钻明细、查询定义、创建导出。固定的是合法能力与计算规则，变化的是期间、粒度和过滤，因此不是把每个自然语言问题硬编码成一个接口。

### 工具描述至少写四件事

以 query_budget 为例：说明何时使用、前置有效计划、支持的维度、零预算/无数据的返回含义。加入反例：“不能用于查询付款流水，不能自行补全缺失预算版本”。明确错误码比泛泛写“查询财务数据”更有帮助。

工具返回区分 NO_DATA、ZERO_VALUE、PARTIAL_DATA、FORBIDDEN。单纯返回空数组会让模型把不同情况混为一谈。分页结果必须标识完整性，模型不能根据前十行下结论说“全公司只有这些项目”。

### Tool Calling 的调用 ID

常见消息式调用中，模型生成工具名、参数和调用 ID，应用执行后将结果按该 ID 配对返回。多个工具结果不能仅按完成顺序拼接。并行调用只适用于无依赖且没有共享副作用的操作。

模型调用 ID 是本轮协议关联标识，业务 operation_id 是一次操作的持久身份。重试后模型可能生成不同调用 ID，因此不能直接把它当作业务幂等键。

## 10. 状态、记忆、证据和缓存为什么分开

| 对象 | 生命周期 | 例子 | 不能承担的职责 |
| --- | --- | --- | --- |
| conversation | 用户连续交互 | “改成下半年” | 不能直接作为授权状态 |
| run / checkpoint thread | 一次可恢复分析 | 追问前后状态 | 不自动代表跨任务长期记忆 |
| query plan revision | 一组固定查询语义 | 时间、组织、预算口径 | 不能在进行中的导出里被修改 |
| evidence | 一次确定性查询结果 | 126 万元汇总 | 不能跨版本随意复用 |
| preference | 明确允许复用的偏好 | 默认显示万元 | 不能偷偷保存一次猜测为业务默认 |
| cache | 可重建的加速数据 | 同版本同权限查询结果 | 不能作为任务完成事实来源 |

本项目约定一个 run 对应一个 checkpoint thread。一个 UI 会话可以包含多个 run，后续问题通过显式继承已确认条件建立新计划。若采用框架 thread 承载整个长期会话的另一种映射，需要额外处理并发消息与新任务状态清理，不混用两种约定。

### 条件继承与失效

用户“换成下半年”时继承组织与预算口径，替换期间，创建新计划版本；汇总、明细与原因引用全部失效。用户“把结果显示成万元”只改变呈现，不必重新查询，但应保留原始精度。用户“用最新数据重算”创建绑定新发布版本的分析，不能覆盖旧证据。

### 上下文预算

将模型窗口分为固定指令、当前指标、已确认计划、近期工具摘要和输出余量，具体额度随模型与评测确定。先删除可重新查询的明细，再压缩历史叙述；指标口径、权限边界和有效计划必须保持结构化，不依赖摘要记住。

删除历史工具交互时保持请求和结果配对；不要留下没有对应结果的调用记录。对于超长结果，返回证据 ID、汇总、总行数、截断标志和分页工具入口。

## 11. LangGraph 追问：节点并非只执行一次

StateGraph 的节点返回状态更新；并行写同一键要定义 reducer 或集中汇合。简单列表相加不一定幂等，重放和重复结果可能产生重复证据。本设计优先按 evidence_id 去重合并；查询计划由单一节点更新。[Graph API 文档](https://docs.langchain.com/oss/python/langgraph/graph-api)

下面是接口级示意，需在锁定的依赖版本下集成测试，不是完整应用：

```python
from langgraph.types import interrupt

def clarify(state):
    # 此前只读取已持久化的缺失条件，不创建导出、不扣费。
    answer = interrupt({
        "plan_revision": state["plan_revision"],
        "missing_fields": state["missing_fields"],
    })
    # 校验失败后由外层进入新的澄清轮次。
    return validate_clarification(answer, state)
```

恢复使用原 thread_id 和 Command(resume=...)，节点在恢复时可能从头执行。不要用广泛的 try/except 把 interrupt 当普通失败吞掉。一个节点多个 interrupt 的次序也影响恢复值匹配；本项目一轮只放一个澄清点。[Interrupts 文档](https://docs.langchain.com/oss/python/langgraph/interrupts)

导出拆为 prepare_export 和 submit_export：前者生成稳定 ID 并形成持久化边界，后者才调用 Java。需要验证所选持久化模式在进入副作用节点前确实完成必要状态写入。边界不足时，增加独立的操作意图表，不能假定“有 checkpoint 就一定不会重新生成 ID”。

## 12. 什么时候停止，如何防止循环

仅配置 recursion_limit 只能避免无限运行，无法说明分析是否充分。项目使用两类条件：

- 硬条件：截止时间、模型调用次数、工具次数、最大下钻深度、重复规范化查询。
- 业务条件：主要差异已定位、无进一步可用维度、没有新的证据、用户目标已完成。

对于差异贡献覆盖率，按正向超支分别计算更容易解释；总差异可能被结余抵消，不用绝对值混算一个看似漂亮的占比。停止时返回 termination_reason，如 GOAL_MET、NO_MORE_EVIDENCE、BUDGET_EXHAUSTED，并说明还有什么未分析。

不能只问模型“是否完成”，也不能达到三步就总是输出“已完成全面分析”。

继续阅读：[Skills、MCP 与 Function Calling](07-Skills与MCP能力管理.md)，再进入[技术实现与工程边界](03-技术实现与工程边界.md)。
