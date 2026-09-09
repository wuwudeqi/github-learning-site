---
id: budget-agent-design
title: Agent 项目｜从汇报需求到可信结果的执行设计
category: 笔记
author: 个人整理
date: "2026-09-09"
description: 围绕多项目及不同分摊口径，设计需求计划、有效计划、澄清、下钻、变更失效、工具契约和可恢复执行。
tags: [LangGraph, 工具调用, 状态管理, Agent, 分摊口径]
---

# 从汇报需求到可信结果的执行设计

> 本文是基于真实业务背景提出的 Agent 方案，尚不代表线上实现。工具名、字段、版本及运行轨迹均为项目自定义示例，金额为合成数据。必须区分“模型建议”“后端批准”和“实际执行结果”。

## 1. Agent 要完成什么业务任务

原系统已经集中项目、预算、项目支出、人力费用和投资方相关数据，卡片、图表由开发定制。员工仍需要理解页面入口、筛选条件和分摊口径，临时汇报则导出 Excel 二次加工。Agent 应把“学会系统以后才能取数”改成“描述汇报任务，系统帮助补齐条件并完成取数与加工”。

典型请求：

> 整理 P01、P02 上半年的预算执行情况，按部门看，找出主要费用差异，给我图表和 Excel，附上原查询数据。

交付包含四件可核对的东西：已采用的业务口径、确定性查询结果、关联证据的解释、基于同一结果生成的文件。查不到原因时输出待核查项，不能把金额变化推测成真实业务原因。

本文采用的**实践假设**：部门、重量级团队、投资是同一项目的独立分摊观察轴；预算和实际费用分别绑定已审核的分摊规则。不能把不同轴的结果相加，也不能把部门比例乘以投资比例推导“部门 × 投资方”的联合分摊。真实系统若维护联合规则，应作为单独受控能力接入。

## 2. 受控状态图：哪些判断交给模型

![Agent 执行流程](./images/flow.svg)

图示表达主流程；本项目查询前的“口径”具体包含分摊轴、预算定义、费用范围及各自的规则版本。

| 阶段 | 模型可以决定 | 程序必须决定 |
| --- | --- | --- |
| 理解需求 | 判断“我们部门”可能指组织筛选还是部门分摊，提出候选解释 | 当前用户、可访问项目、候选项合法性 |
| 形成计划 | 提取项目、期间、指标、分摊轴和呈现要求 | 条件是否缺失、规则是否存在、组合能否计算 |
| 观察结果 | 按项目或费用类别继续查，或结束分析 | 下钻范围、当前权限、查询预算、重复动作 |
| 解释结论 | 组织事实、对比和待核查项 | 金额及比率计算、引用归属、完整性 |
| 生成材料 | 建议卡片或图表类型、排列顺序 | 结果版本、图表配置校验、导出幂等和授权 |

固定流程并不排除 Agent：看到部门 D_A 的差异后，模型可以选择按项目拆分，再判断是否需要费用类别。但它不能重新定义分摊公式，也不能绕过有效计划直接查库。

首版使用单 Agent。核心复杂度在业务口径、证据和执行可靠性，拆成多个“财务专家 Agent”会先增加上下文传递与结论冲突成本。待单 Agent 评测显示独立子任务确有收益，再考虑并行。

## 3. 两份计划：用户想查什么，系统实际执行什么

### 3.1 requested_plan 保留原始意图与条件来源

“按部门看”至少涉及三个不同概念：`project_scope` 选择哪些项目，`allocation_axis` 选择哪个规则轴计算承担金额，`group_by` 决定在合法分摊结果上按什么粒度呈现。

部门分摊不等于按项目所属部门做 `GROUP BY`。一个项目可以分摊给多个部门；“查看 D_A 承担的费用”也不意味着用户拥有 D_A 全部数据权限。

下面是模型提议的需求计划，`null` 表示待确认，不是让模型猜一个值：

```json
{
  "project_scope": {"mode": "EXPLICIT", "project_refs": ["P01", "P02"]},
  "period": {"start": "2026-01-01", "end_exclusive": "2026-07-01"},
  "metric_id": "budget_execution",
  "budget_basis": null,
  "actual_basis": "ACCRUED",
  "expense_scope": "labor_and_other_project_costs",
  "allocation_axis": "DEPARTMENT",
  "group_by": ["allocation_target_id"],
  "requested_outputs": ["chart", "xlsx", "query_data"],
  "field_sources": {
    "allocation_axis": "USER_EXPLICIT",
    "period": "USER_EXPLICIT",
    "actual_basis": "PUBLISHED_METRIC_DEFAULT"
  }
}
```

字段来源区分用户明确表达、已确认上下文、已发布业务默认和模型推断。只有来源可靠且无冲突的值才能自动继承。业务默认必须能从目录查到，不能把模型多次猜中当成默认规则。

### 3.2 effective_plan 是 Java 创建的执行合同

Java 将名称映射为合法 ID，检查项目范围、规则覆盖、粒度、期间和授权，形成不可变有效计划：

```json
{
  "effective_plan_id": "plan-demo-002",
  "plan_revision": 2,
  "project_ids": ["P01", "P02"],
  "period": {"start": "2026-01-01", "end_exclusive": "2026-07-01"},
  "budget_basis": "ADJUSTED",
  "actual_basis": "ACCRUED",
  "allocation_axis": "DEPARTMENT",
  "group_by": ["allocation_target_id"],
  "metric_version": "metric-v1",
  "allocation_rule_bundle_id": "alloc-bundle-v1",
  "budget_rule_version": "budget-dept-v1",
  "actual_rule_version": "actual-dept-v1",
  "comparison_policy": "APPROVED_SAME_BASIS",
  "rounding_policy": "PER_FACT_LARGEST_REMAINDER_V1",
  "data_release": "rel-001",
  "rule_binding_manifest_id": "bindings-demo-001",
  "scope_binding_id": "scope-demo-001",
  "allowed_drilldowns": ["project", "expense_category"],
  "query_route": "TRUSTED_METRIC"
}
```

规则包 `alloc-bundle-v1` 固定预算与实际各自命中的规则和比较策略。示例 `APPROVED_SAME_BASIS` 表示已审核的可比口径，不能仅凭版本字符串相等判断可比；不同规则也可以比较，但必须有已批准策略，并在结果中解释差异。`PER_FACT_LARGEST_REMAINDER_V1` 表示本例采用逐事实分摊与最大余数分配的舍入策略，具体算法见技术实现篇。

真实规则可能按项目、费用类别和生效期选择，不能假定一个版本号对应全公司所有比例。这里的两个 `rule_version` 表示规则集合版本，`rule_binding_manifest_id` 指向本次实际命中的项目、期间及规则明细，便于复核。

执行节点使用 Java 返回的计划 ID，不用模型复制回来的对象作为权威。计划保存授权范围以便追溯，但不冻结权限：每次执行和读取仍校验当前授权。用户明确要求无权范围时拒绝或说明可选范围，不能偷偷缩小以后仍标成“全公司”。

标准预算执行走可信指标能力；临时字段组合可进入受限 Text-to-SQL，但 SQL 也绑定同一有效计划及允许数据集。两条路径返回统一 `result_id`，不能形成两套分摊公式。

## 4. 状态契约：恢复、证据和版本都要可追踪

以下是项目逻辑字段，不是框架内置 Schema。

| 状态组 | 字段 | 不变量 |
| --- | --- | --- |
| 任务 | run_id、thread_id、request_id、status | 一个 run 对应一个 checkpoint thread，UI 会话可关联多个 run |
| 需求 | request_text、requested_plan、field_sources、plan_revision | 用户新意图形成新修订，不覆盖历史 |
| 执行合同 | effective_plan_id、effective_plan_summary、validated_query_id | 只能接收可信 Java 返回值 |
| 语义版本 | allocation_axis、metric_version、allocation_rule_bundle_id、budget_rule_version、actual_rule_version、comparison_policy、rounding_policy、data_release、rule_binding_manifest_id | 计算条件变化，旧证据不能支撑新结论 |
| 方法版本 | skill_revision、guidance_revision_refs、tool_catalog_hash、template_revision | 固定本次实际使用的内容和合同 |
| 等待 | pending_question、waiting_revision、resume_command_id | 只消费属于当前等待修订的回答，重复恢复可去重 |
| 证据 | result_ids、active_evidence_refs、evidence_plan_revision | 完整数据在结果服务，状态只存引用与有界摘要 |
| 控制 | visited_query_hashes、step_count、deadline_at、termination_reason | 重复动作、超时或无新证据时有出口 |
| 副作用 | artifact_intent_id、export_operation_id、artifact_job_id | 稳定操作 ID 在调用产物服务前持久化 |

**可信执行上下文与模型状态分开。** actor、租户、服务凭证、委托关系和当前权限来自认证层，不由用户文本、Skill 或模型参数提供。检查点只保存受控上下文引用，恢复时重新取得当前授权，不能把历史权限集合装载为有效授权。

状态字段区分写入者：模型生成候选计划与动作，校验节点写有效计划，工具节点写结果引用。把整个状态交给模型随意修改，会让“标记已校验”变成可伪造文本。

并行读取携带计划修订号。迟到结果若属于旧修订，只保留审计记录，不进入当前证据集合。证据按 ID 去重，避免列表累加在重放时制造重复结论。LangGraph 的状态更新与 reducer 需要显式设计。[Graph API 文档](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 5. 何时必须澄清，何时直接执行

减少培训成本不是把页面字段换成一长串对话。只有会实质改变金额、范围或解释的歧义才阻止执行。

| 用户表达或系统条件 | 行为 | 原因 |
| --- | --- | --- |
| “按部门看”；项目归属和费用承担均可能，无合法默认 | 问“看项目所属部门，还是部门分摊后的承担金额？” | 两种统计对象不同 |
| “预算执行”；年初/调整预算均可用，无发布默认 | 问采用哪种预算 | 分母不同会改变执行率 |
| “我们团队”；组织目录中有多个匹配 | 给出可访问候选，要求选择 | 不靠名称相似猜组织 ID |
| “把全部导出”；已有明确有效计划 | 导出该计划完整授权结果，显示范围及行数 | 通常是去掉预览分页，不是扩大权限 |
| “同样一份，改成柱状图” | 复用结果，修改合法 ChartSpec | 呈现不改变查询语义 |
| “改按投资看” | 继承项目/期间，重新验证规则与授权 | 改变分摊计算，不能只换图例 |
| 缺少本期已审核分摊规则 | 返回 RULE_COVERAGE_GAP 及受影响范围 | 不自动均分或套用别的项目比例 |
| 已发布默认显示万元，用户没有冲突要求 | 应用并在条件区显示 | 无损显示单位无需额外追问 |

一次追问一个关键分歧，解释选择含义；已确认条件不重复问。可靠的会话条件可以明确标注“沿用上次项目范围”。用户只要图表时，不强制先走异常分析。

## 6. 完整轨迹：部门汇报，然后切换投资视图

### 6.1 可手工核对的合成输入

仅为便于演示，本例预算和实际在部门轴采用相同比例，真实设计仍分别绑定各自已审核规则。实际费用包含人力费用和其他项目支出，费用分类的互斥性、完整性由指标目录声明。

| 项目 | 调整后预算 | 实际费用 | D_A 比例 | D_B 比例 |
| --- | ---: | ---: | ---: | ---: |
| P01 | 700,000 | 770,000 | 60% | 40% |
| P02 | 500,000 | 490,000 | 20% | 80% |
| 项目合计（分摊前） | 1,200,000 | 1,260,000 | — | — |

金额单位为元。演示主体可查看这两个项目及两个部门的完整分摊结果，因此可检验轴内总额守恒。真实受限用户只看到部分份额时，不要求可见小计等于全项目总额，也不能借核对暴露隐藏金额。

### 6.2 每一步的输入、决定和证据

| 步骤 | 发生什么 | 固化什么 |
| --- | --- | --- |
| 1. 接收 | 用户提出 P01、P02 上半年部门汇报及图表、Excel、查询数据要求 | 原文、request_id、候选 requested_plan |
| 2. 定义解析 | 目录说明部门分摊视图；预算有两种且无默认 | 合法轴、指标含义、缺失 budget_basis |
| 3. 澄清 | 用户选择调整后预算 | plan_revision=2、来源 USER_CONFIRMED |
| 4. 校验 | Java 验证项目、规则覆盖和授权，绑定数据及规则版本 | plan-demo-002，候选计划不能冒充执行结果 |
| 5. 汇总 | D_A 预算 520,000、实际 560,000；D_B 预算 680,000、实际 700,000 | res-dept-001、单位、完整性和版本 |
| 6. 决策 | D_A 差异 40,000，大于 D_B 的 20,000；建议先按项目拆 D_A | 动作、依据结果 ID、reason_code |
| 7. 下钻 | 创建同数据与规则版本的派生计划，限制 D_A，按项目查询 | P01 差异 +42,000，P02 差异 −2,000，合计 +40,000 |
| 8. 解释 | 可说“D_A 超支主要来自 P01”；无说明时不写“人力投入增加导致” | 事实与原因分开，原因缺口作为待核查项 |
| 9. 交付 | 核对引用，可信服务生成卡片数据、SVG、Excel和查询数据 | 同一组 result_id、报告清单、稳定导出操作 ID |

D_A 预算为 `700000 × 60% + 500000 × 20% = 520000`；实际为 `770000 × 60% + 490000 × 20% = 560000`。执行率由服务计算为 `560000 / 520000 ≈ 107.69%`，不能平均两个项目的执行率。

若需要解释人力费用贡献，必须确认预算与实际都有可比较的费用分类及分摊规则。只有实际人力明细、没有人力预算时，可以说明“实际费用构成”，不能构造“人力预算超支”。

### 6.3 用户说“同样一份，改按投资看”

1. 继承项目、上半年、调整后预算和输出形式，生成新计划修订；allocation_axis 改为 INVESTOR。
2. 清空当前可用于新结论的部门结果引用、下钻筛选和数据型图表配置。旧结果保留历史，已有部门导出仍标为部门视图。
3. Java 检查投资轴支持情况、当前授权、预算/实际投资分摊规则及完整性。原发布版本若不包含对应规则，不能静默切到新数据，应明确选择可用的完整版本。
4. 创建新有效计划和结果。不能把 D_A、D_B 标签改成投资方，也不能从部门份额乘出投资方金额。
5. 对话显示“沿用上半年与调整后预算，改为投资维度”；最终报告呈现投资轴及规则，不沿用部门结论。

如果只说“单位改成万元”，则保留计算结果，产生新的呈现版本，不必重查数据库。这是语义变化与显示变化的区别。

## 7. 节点与工具契约

| 节点 | 职责 | 后续 |
| --- | --- | --- |
| understand | 提取意图、选择主 Skill，构造 requested_plan | resolve_context |
| resolve_context | 获取授权范围内的指标、轴、能力及说明版本 | clarify / validate_plan |
| clarify | 保存一个关键分歧并等待 | 回答后重做条件与版本校验 |
| validate_plan | Java 创建 effective_plan | 标准指标 / 受限 SQL 分支 |
| execute_query | 可信服务执行并保存统一结果 | observe |
| observe | 读取摘要，决定下钻或交付 | 派生计划校验 / compose |
| compose | 组织事实、说明与待核查项 | verify_output |
| verify_output | 核对数值、单位、引用、范围、完整性 | prepare_artifact / finish |
| prepare_artifact | 冻结结果和配置，持久化稳定操作 ID | submit_artifact |
| submit_artifact | 创建或查询幂等产物任务 | 返回任务入口 |

完整 MCP 目录在第 03 篇，这里仅保留执行主链。以下为项目逻辑合同，不是已经实现的 API。

| 工具 | 模型可提供的参数 | 可信服务返回 |
| --- | --- | --- |
| budget_resolve_context | 项目候选、意图、期间、轴候选 | 合法指标/轴/粒度、规则可用性、条件歧义 |
| budget_validate_plan | requested_plan；下钻时附 parent_plan_id | effective_plan_id、语义摘要、版本或错误 |
| budget_query | effective_plan_id | result_id、schema、汇总、完整性、版本 |
| budget_get_result | result_id、合法分页游标、所需字段 | 有界数据、总行数和截断标志 |
| budget_create_artifact | result_ids、合法格式、ChartSpec、模板 | artifact_job_id、状态 |

budget_query 不允许模型临时覆盖已校验期间、维度或过滤。条件变化必须建立派生计划，由 Java 检查父计划、版本和范围。总行数、总金额也可能敏感，返回前同样受授权控制。

一个成功结果摘要：

```json
{
  "ok": true,
  "result_id": "res-dept-001",
  "effective_plan_id": "plan-demo-002",
  "allocation_axis": "DEPARTMENT",
  "unit": "CNY",
  "rows": [
    {"allocation_target_id": "D_A", "budget": "520000.00", "actual": "560000.00", "variance": "40000.00"},
    {"allocation_target_id": "D_B", "budget": "680000.00", "actual": "700000.00", "variance": "20000.00"}
  ],
  "row_count": 2,
  "completeness": "COMPLETE",
  "truncated": false,
  "data_release": "rel-001"
}
```

金额使用十进制字符串传输，Java 精确计算。模型不负责组装大量数据数组，完整数据、schema 和版本清单存于结果服务。

错误按处理语义分类：AMBIGUOUS_BASIS 进入澄清；RULE_COVERAGE_GAP 指向缺失规则；JOINT_ALLOCATION_UNSUPPORTED 拒绝无依据的联合分摊；FORBIDDEN 不重试提权；TEMPORARY_UNAVAILABLE 才考虑有界重试。NO_DATA、ZERO_VALUE、PARTIAL_DATA 分别表示无记录、真实为零、不完整，不能统一返回空数组。

## 8. 动作边界、上下文与停止条件

模型产生有界动作，不是任意脚本：

```json
{
  "action": "DRILL_DOWN",
  "parent_plan_id": "plan-demo-002",
  "group_by": ["project"],
  "filters": [{"field": "allocation_target_id", "op": "EQ", "value": "D_A"}],
  "evidence_refs": ["res-dept-001"],
  "reason_code": "LOCATE_VARIANCE_CONTRIBUTOR"
}
```

运行层检查父计划仍为当前修订、证据归属、过滤范围、合法分组、重复查询及执行预算。reason_code 是简短动作依据，不要求模型输出内部思维链。

上下文优先保留当前有效计划、指标含义、版本、有效证据和用户最新要求。历史长表与失效结论移出工作上下文，用引用保留。压缩摘要不能把“部门分摊实际费用”变成含糊的“部门金额”。结构化输出约束格式，不能保证业务含义正确，仍需后端验证。[LangChain 结构化输出文档](https://docs.langchain.com/oss/python/langchain/structured-output)

| 改动 | 可继承 | 必须重新建立 |
| --- | --- | --- |
| 改单位或图形 | 有效结果、原始精度 | 呈现配置、产物清单 |
| 改项目、期间、预算定义或分摊轴 | 无冲突的已确认条件 | 有效计划、结果、结论、数据型图表 |
| 要求最新数据 | 业务目标 | 新 release 绑定及全部查询证据 |
| 只改汇报措辞 | 有效事实与引用 | 文本验证、报告版本 |
| 撤权或紧急禁用工具 | 审计历史 | 重新授权，不满足则终止或拒绝读取 |

停止包含硬上限（截止时间、模型/工具次数、下钻深度、重复查询）与业务条件（用户需要的图表已完成、主要差异已定位、无可比较维度、没有新证据）。演示可设最多三次下钻，但必须标为实验配置。

“达到三步”只能说明预算耗尽或部分完成，不能写“已全面分析”。差异贡献区分正向超支和负向结余，避免用被抵消后的净差异制造误导性占比。

## 9. 持久化、澄清恢复与导出重试

Python 管理分析执行状态，Java 保存请求归属、run 映射和业务操作事实。受理请求持久化为 QUEUED 后由 Worker 认领，不能只在 HTTP 中启动内存协程。首版一个 Worker 足够演示可靠性，再扩展并发认领与 fencing。

request_id 在可信用户范围内唯一；同 ID、同规范化内容返回同一 run，不同内容报冲突。恢复校验 run 归属、等待状态及 waiting_revision，并以 resume_command_id 去重。两个恢复请求通过串行处理或版本比较防止同时推进。

LangGraph 的持久化检查点保存和恢复图状态；纯内存 checkpointer 不能证明跨进程恢复。检查点与 Java 任务表不构成天然的跨服务事务，需要稳定业务操作身份关联。[LangGraph 持久化文档](https://docs.langchain.com/oss/python/langgraph/persistence)

澄清节点示意：

```python
from langgraph.types import interrupt

def clarify(state):
    # 此前只读取状态，不创建导出或修改业务规则。
    answer = interrupt({
        "waiting_revision": state["waiting_revision"],
        "question": state["pending_question"],
    })
    return validate_answer_for_revision(answer, state)
```

恢复使用原 thread_id 和 Command(resume=...)；含 interrupt 的节点会从头执行，副作用应独立并幂等，不用宽泛异常捕获吞掉暂停信号。一轮只放一个澄清点，回答无效则记录新的等待状态后进入下一轮。[LangGraph interrupts 文档](https://docs.langchain.com/oss/python/langgraph/interrupts)

导出先写稳定意图与 export_operation_id，再调用 Java。若 Java 已创建任务但响应丢失，恢复时用同一 ID 查询或重试。验证所选持久化模式是否在副作用前形成可靠写入边界；不满足时用独立操作意图表，不能声称“有 checkpoint 就只执行一次”。

模型 tool_call_id 只配对本轮请求/结果，MCP 请求 ID 只关联协议交互，它们都不是导出幂等键。显示连接断开不等于取消任务；显式取消在节点安全边界处理，已受理产物另行取消。

## 10. 观测与验收

先用合成黄金集验证口径、计算、变更失效与证据，再接模型评估理解和动作选择，不能把生成一张图视为全链路通过。

| 验收场景 | 可检查结果 |
| --- | --- |
| 部门轴多项目汇报 | 采用已审核规则，D_A 预算 520,000、实际 560,000 |
| 缺预算口径且无默认 | 只澄清实质歧义，不自行选分母 |
| 部门切投资，旧查询迟到 | 新计划不含旧证据，旧结果只进入历史 |
| 要求部门 × 投资，无联合规则 | 明确不支持，不相乘比例猜结果 |
| 实际有明细、预算无同粒度 | 可输出实际构成，不能伪造细分预算差异 |
| 说明与后端规则不一致 | 权威规则优先，标记说明版本冲突 |
| 暂停期间撤权 | 恢复或读取时拒绝，不复用旧权限 |
| 导出响应丢失 | 复用同一业务任务，不重复创建 |

每次节点记录 run、计划修订、Skill/工具合同版本、工具名、结果 ID、耗时、重试和停止原因；敏感明细不直接打日志。排查顺序是“用户原意 → 候选计划 → 后端有效计划 → 工具结果 → 输出引用”，定位偏差发生的层次。

评测至少关注正确完成率、错误自动执行率、必要澄清召回率、不必要澄清率、工具次数、p95 耗时和每成功任务成本。固定样本与分母后再报告数据，不写未经验证的提升比例。本表仍是待实现验收目标，不与已运行的确定性实验混淆。

## 11. 面试连续追问

**为什么不直接做自然语言转 SQL？** 用户要的是可核对的汇报，还包含口径确认、分摊规则、权限、版本、下钻和多格式交付。Text-to-SQL 是一条查询实现路径，不能替代执行合同与证据闭环。

**有固定节点，Agent 自主性在哪里？** 节点守住边界，模型根据结果在合法维度中选动作。D_A 差异突出时先看项目，再根据粒度判断是否拆人力与其他费用。分析路径可变化，计算规则不可被模型改写。

**怎样证明“按部门看”理解正确？** 保存原文、字段来源及 requested_plan；Java 返回采用部门分摊而非项目归属的 effective_plan，页面显示口径，结果携带规则绑定。真有两种含义且无默认时，先澄清。

**有 checkpoint，重复导出解决了吗？** 没有。恢复可能重放节点，跨服务副作用也可能成功但响应丢失。稳定操作 ID 必须先持久化，Java 用唯一约束和参数哈希识别同一意图；状态恢复与业务幂等分别解决问题。

**同项目换维度，为什么不能复用结果？** 部门与投资是独立计算口径，改变轴就改变规则和可见份额。项目、期间可继承，有效计划和结果需重建；只换图形或显示单位才复用结果。

继续阅读：[Skills、MCP 与 Function Calling](03-Skills与MCP能力管理.md)，再进入[技术实现与工程边界](04-分摊语义与Java工程实现.md)。
