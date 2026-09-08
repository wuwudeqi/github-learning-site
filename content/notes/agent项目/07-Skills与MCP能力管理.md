---
id: budget-agent-capability-management
title: Agent 项目｜业务维护 Skills、开发封装 MCP 与 Function Calling
category: 笔记
author: 个人整理
date: "2026-09-08"
description: 业务可维护分析方法、开发复用已有接口，详解技能发布、工具适配、身份传递、版本兼容、运行轨迹和面试追问。
tags: [Skills, MCP, FunctionCalling, 能力管理]
---

# 业务维护 Skills，开发封装 MCP 能力

> 本文是目标实现设计。接口、表结构及版本号为项目自定义示例，不表示系统已经实现，也不表示它们是框架自带字段。

## 1. 业务目标与职责边界

预算管理人员希望调整分析方式，例如“超支项目继续拆分费用类别，汇报必须附数据截止时间”；开发人员不应为每次报告风格变化重新发布应用。另一方面，业务不能通过改一段自然语言获得更大的数据权限或新增不存在的数据接口。

因此分为三类职责：业务维护任务方法与输出规范，开发维护可执行业务能力，平台维护选择、加载、鉴权、版本和执行状态。

| 层次 | 负责内容 | 不负责的内容 |
| --- | --- | --- |
| Skill | 何时使用、分析方法、参考资料、报告模板 | 授予数据权限、重定义正式指标、自动获得新工具 |
| Function Calling | 模型提出结构化工具调用请求 | 实际访问数据库、保证参数语义正确 |
| MCP | 工具发现、描述和调用的标准接口 | 企业组织权限、业务事务、自动幂等 |
| LangGraph 运行层 | 状态、路由、等待输入、恢复、停止 | 代替业务数据服务维护所有规则 |
| Java 预算应用 | 可信指标、权限、查询、结果集和产物 | 自由解释用户目标与无限自主规划 |

模型提出工具调用后，应用负责执行并返回结果；工具 schema 并不会把业务执行权交给模型。[工具调用官方说明](https://docs.spring.io/spring-ai/reference/api/tools.html)

![Skills 与 MCP 协作关系](./images/capability-management.svg)

## 2. Skill 管什么：方法可编辑，规则有权威来源

先做两个 Skill：

| 名称 | 触发条件 | 方法 | 交付 |
| --- | --- | --- | --- |
| budget-execution-analysis | 查预算执行、定位主要差异 | 确认口径、查询汇总、选择下钻、引用业务说明 | 结果集、结论、待核查项 |
| budget-report-generation | 基于有效分析生成汇报 | 检查证据完整性、选择模板和图表、组织汇报 | SVG、Excel、报告及核对清单 |

Skill 可采用 SKILL.md 加 references、assets 的目录结构，并按元数据、正文和资源逐级加载。这里的业务后台、发布状态和依赖校验是本项目新增的管理能力。[Agent Skills 格式规范](https://agentskills.io/specification)

```text
budget-execution-analysis/
  SKILL.md
  references/
    analysis-method.md
    edge-cases.md
  assets/
    report-template.md
```

Skill 示例节选：

```yaml
---
name: budget-execution-analysis
description: 分析指定组织与期间的预算执行，确认口径并定位主要差异贡献。
metadata:
  version: "1.2.0"
---
```

正文约定：查询前取得指标定义；预算版本含糊时追问；按费用类别或项目选择下钻；原因需关联说明；无证据时输出待核查项。Skill 可以要求展示执行率，但计算公式来自指标目录，不在自然语言里另存一套。

分析关注阈值可成为受校验业务配置，例如“差异超过多少需要展示”。它属于报告关注规则，不应修改账务事实或正式指标公式。配置需要单位、范围和适用期间，不能只有一个没有含义的数字。

## 3. 业务维护页面与数据模型

业务页面提供：名称、适用场景、输入条件、分析步骤、输出要求、参考资料和试运行入口。底层渲染为 Skill 文件，业务不必学习 Markdown 或 MCP 协议。

强制项使用结构化字段，例如 required_sections=[data_scope,data_date,evidence]；灵活的下钻建议放在正文。前者由程序检查，后者由模型参考。不能把“必须有数据来源”只写在自然语言中却没有验证。

| 对象 | 关键字段 | 说明 |
| --- | --- | --- |
| skill_definition | skill_id、name、owner、status | 稳定身份与归属 |
| skill_revision | revision_id、body_hash、content_uri、created_by | 不可变内容版本 |
| skill_dependency | revision_id、tool_key、contract_version | 项目自定义依赖，不冒充标准字段 |
| skill_release | skill_id、active_revision、published_at | 当前发布指针 |
| skill_eval_run | revision、dataset_version、metrics、failures | 发布前验证记录 |
| analysis_run | skill_revision、tool_catalog_hash、template_revision | 执行时固定依赖 |

编辑权限、发布权限和数据访问权限独立。发布者的权限不传给运行者。试运行同样使用试运行者可访问的数据，或者明确隔离的合成测试数据。

## 4. 发布流程与灰度

流程：草稿 → 结构校验 → 依赖校验 → 固定案例试运行 → 发布；必要时退回草稿。发布是更新活动版本指针，不覆盖已有版本。

校验内容包括：名称与描述、引用文件路径、所需工具是否存在、参数合同是否兼容、强制输出项是否可验证、资源大小和不支持的脚本。首版不允许业务上传任意可执行脚本。

新请求取得当前发布版本，运行中的任务固定旧版本。紧急禁用属于安全策略，优先于版本固定：旧任务在下一次执行边界被阻止，不能以“复现旧版本”为理由继续调用危险能力。

灰度可按显式测试用户或任务比例实施，记录版本归属。只有两个 Skill 时不必先建复杂发布平台，但至少有不可变版本、发布指针、回滚和回归记录。

## 5. Skill 选择与按需加载

1. 先按当前用户可用功能与发布状态过滤候选。
2. 提供名称和适用场景，必要时结合关键词检索；候选很少时无需向量库。
3. 模型或确定性路由选择 Skill；没有合适候选则追问或说明能力范围。
4. 加载正文与本次需要的参考资料，记录内容摘要。
5. 工具集合由运行策略约束，不按 Skill 的自然语言任意扩充。

可用工具集合可表示为：已注册且兼容的工具 ∩ 当前系统允许工具 ∩ 本任务所需工具 ∩ 当前主体可用功能。真实行列权限仍在工具后端校验，不能用工具可见性代替数据隔离。

Skill 描述本身可能有歧义。评测同时记录误选率、无合适 Skill 时的正确处理、上下文 Token 和任务成功率，不只看“成功加载文件”。

## 6. MCP 如何包装已有 Java 能力

Java 应用内新增薄适配模块，不复制查询逻辑：

```text
MCP 工具适配器
  → 认证上下文解析
  → 参数与合同校验
  → 既有预算领域服务
  → 统一结果与错误转换
```

| 工具名（示例） | 复用服务 | 核心返回 |
| --- | --- | --- |
| budget_get_metric | 指标定义服务 | 口径、粒度、允许维度 |
| budget_query | 受控指标查询 | result_id、schema、统计摘要 |
| budget_validate_sql | SQL 校验服务 | 绑定权限与版本的 validated_query_id |
| budget_execute_query | 受控执行服务 | result_id、完整性、证据 |
| budget_get_result | 结果集读取服务 | 有界分页与字段元数据 |
| budget_create_artifact | 产物服务 | artifact_job_id、状态 |

MCP 提供 tools/list 和 tools/call；项目仍需自行建立工具到业务服务的映射、权限与错误语义。[MCP Tools 规范](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)

Spring AI 提供 Spring Boot MCP Server 集成能力，可用于接口包装；运行时鉴权需要单独配置，不能认为注册工具就自动拥有安全边界。此处使用 Spring AI 的 MCP 模块不代表再部署一套 Java Agent 编排循环。[Spring AI MCP Server 文档](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-server-boot-starter-docs.html)

实际实现需锁定 Spring Boot、Spring AI/MCP SDK 与客户端兼容版本，并用合同测试验证。本文不提供未经运行验证的依赖组合。

## 7. Function Calling 与 MCP 的转换链

预算分析不是模型直接发送 MCP 协议请求。运行层先发现工具，转换成模型支持的工具定义；模型生成调用后，再由执行器转成 MCP 调用。

示例为逻辑内容，不是完整协议报文：

```json
{
  "tool": "budget_create_artifact",
  "arguments": {
    "resultId": "res-001",
    "formats": ["xlsx", "svg"]
  }
}
```

actor、tenant、operation_id 和服务凭证由可信运行层附加或注入，不作为模型可以随意更改的参数。对工具参数中的未知字段按合同拒绝，避免模型夹带身份字段。

适配器保存 model_tool_call_id → tool_key/server_id → contract_version → operation_id 的映射。工具名冲突可在模型可见名称上加受控命名空间；不能只按裸工具名路由到第一个同名 Server。

工具结果按调用 ID 配对。MCP 结果的传输成功、工具报告的业务成功、最终任务成功分别记录。收到业务错误时不能只因为 HTTP 200 就标记成功。

## 8. 完整执行场景

业务发布 Skill v1.2：按费用类别拆分，再定位项目，并输出 SVG 与 Excel。用户有研发一部查询和导出权限。

运行服务固定 Skill 版本，加载相关工具合同；模型确认期间与预算口径，生成查询计划。Java 创建有效查询并执行，将完整结果写为 res-001。模型基于结果摘要决定下钻，创建派生结果 res-002；报告产物的 manifest 引用所用结果及变换。

模型要求导出时，执行器使用稳定 operation_id 调用 MCP。Java 校验来源结果、当前权限及图表配置，创建异步产物任务。用户得到图表、Excel 和查询数据入口，三个入口受同样的结果归属约束。

## 9. 难点与排查

### Skill 更新后调用不存在的参数

检查顺序：run 固定的 Skill revision → 依赖声明 → 工具目录 hash → 模型获得的 schema → 实际 MCP 工具版本。修复是合同兼容校验与发布回归，不是让模型无限修正参数。重大变更用明确新合同版本；删除旧工具会影响在途任务，需要安排迁移或显式失败。

### 一个任务加载多个冲突 Skill

不直接拼接所有正文。明确主任务 Skill，辅助 Skill 只能补充指定阶段；冲突按平台策略处理并记录。输出方法可以组合，权限、公式和强制规则不能由“最后加载的文件”覆盖。

### MCP Server 超时

按发现失败、连接失败、执行超时和业务失败分类。副作用调用使用稳定操作 ID；不能因为换了 MCP transport 或重连就重新生成身份。工具恢复后再次校验合同，禁止静默调用不同语义的同名工具。

## 10. 面试追问与验证标准

| 追问 | 回答核心 | 实验 |
| --- | --- | --- |
| Skill 和 Prompt 有何区别？ | 包含适用描述、方法及可按需加载资源；本项目加管理生命周期 | 对比全量上下文与按需加载 |
| 业务写“必须导出全公司”能提权吗？ | 不能，权限由当前用户与工具服务决定 | 普通用户运行高权限作者发布的 Skill |
| MCP 替代 Function Calling 吗？ | 一个是能力接入协议，一个是模型调用请求机制 | 展示一次双向转换轨迹 |
| 固定版本后权限还能撤销吗？ | 版本固定不冻结授权，当前拒绝策略优先 | 运行途中撤权或禁用工具 |
| MCP 端点是不是公开服务？ | 这里向授权内部客户端开放，非默认公网匿名 | 未认证连接及无权调用负例 |

验收至少覆盖：Skill 选择、版本回滚、缺工具、合同变化、正文注入、跨用户试运行、重复调用和工具异常。上述功能当前为设计，不能将合同草图当成已运行能力。

继续阅读：[权限闭环](08-数据权限与导出安全.md)、[Text-to-SQL](09-Text-to-SQL生成与评测.md)、[多格式导出](10-多格式导出与数据核对.md)。
