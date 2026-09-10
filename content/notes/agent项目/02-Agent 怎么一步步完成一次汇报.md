---
id: budget-agent-design
title: "Agent 怎么一步步完成一次汇报"
category: 笔记
author: 个人整理
date: '2026-09-10'
description: 用 LangGraph4j 1.8.27 的实际 Java 代码解释状态、条件路由、等待用户、检查点恢复与副作用去重。
tags: [Java, LangGraph4j, Agent, 状态, 恢复]
---

# Agent 怎么一步步完成一次汇报

用户说：“把 P01、P02 上半年的费用按部门整理一下，再导出。”Agent 不能直接开查。至少还要知道预算用年初版还是调整后，以及部门指哪种业务关系。缺的内容先补齐，确定后再生成可执行计划。

这一章对应 [Java 示例](code/langgraph4j-demo.zip)。版本固定为 Java 21、LangGraph4j 1.8.27，API 以该版本源码为准。示例里的决策器是固定测试替身，便于复现执行过程；接真实模型时，再替换 `NextStepPolicy`。

![从确认口径到导出任务的执行过程](images/flow.svg)

## 图里的一步，要有清楚的输入与结果

示例从 `resolve` 开始。如果缺预算口径，写入等待问题并走向 `await_basis`；否则进入 `validate_plan`。随后查询汇总，由 `decide` 判断要不要按项目下钻，最后准备导出意图、提交任务并结束。

| 节点 | 做什么 | 什么情况下不能继续 |
| --- | --- | --- |
| `resolve` | 找出缺少的预算口径 | 进入等待分支 |
| `await_basis` | 接收已补充的口径 | 值不在允许集合中 |
| `validate_plan` | 生成计划 ID，绑定发布版本 | 范围、口径或权限不通过 |
| `query_summary` | 得到 D_A 汇总与结果 ID | 数据或版本无效 |
| `decide` | 从允许动作中选下一步 | 未知动作或重复下钻 |
| `query_project` | 查询项目差异，追加证据 | 结果不属于当前计划 |
| `prepare_export` | 保存稳定操作编号 | 导出条件未满足 |
| `submit_export` | 创建或取回同一导出任务 | 同编号对应不同参数 |

模型可以建议“下钻”，但不能自行增加不存在的工具名。程序验证动作后才走条件边。固定替身与真实模型都必须经过同一检查，这样测试才不会绕过运行时边界。

## State 保存下一步需要的事实

LangGraph4j 的状态类继承 `AgentState`。下面摘自可运行源码：

```java
public static final class State extends AgentState {
  public State(Map<String, Object> data) {
    super(data);
  }

  public static final Map<String, Channel<?>> SCHEMA = Map.of(
      "evidence_archive",
      Channels.<Map<String, String>>base(
          BudgetGraph::mergeEvidence, HashMap::new),
      "active_result_ids",
      Channels.<List<String>>base(ArrayList::new));
}
```

状态中有任务编号、计划版本、预算口径、数据发布版本和当前结果编号。示例为了方便观察还保存少量合成金额；完整应用应把大结果单独存储，只在状态里引用它。

两个 Channel 刻意采用不同策略。`evidence_archive` 按结果 ID 合并哈希：同 ID 同哈希可以重放，同 ID 不同内容直接冲突。`active_result_ids` 采用覆盖，计划变化时可以清空。如果所有列表都用追加，用户改成另一预算口径后，旧结果还会留在当前集合，后面的解释就可能串数。

普通消息历史可以追加，但历史事实与当前有效证据不能混为一个列表。使用任何现成 reducer 前，都要先回答“这类更新应该覆盖、追加，还是按业务键合并”。

## 缺口径时，停在指定节点之前

本例使用编译配置中的静态断点：

```java
return workflow.compile(
    CompileConfig.builder()
        .checkpointSaver(new FileSystemSaver(
            directory.resolve("checkpoints"),
            workflow.getStateSerializer()))
        .interruptBefore("await_basis")
        .releaseThread(false)
        .recursionLimit(20)
        .build());
```

只有缺口径的路由会经过 `await_basis`，所以已具备口径的请求不会无故暂停。`resolve` 先把问题与等待版本写进状态，执行在 `await_basis` 前停住，前端根据业务状态显示问题。

这里的 20 是图步骤上限，用来约束异常循环；它不等于 20 次模型调用，也不是完整的成本预算。真实应用还要限制总时长、token、工具调用次数和单次查询规模。

FileSystemSaver 配合本例的 `ObjectStreamStateSerializer` 保存状态。实际验证覆盖单执行者的独立进程重启。该文件实现不能据此宣称能承受写文件瞬间断电，也不能直接支持多实例并发写同一线程；生产持久层需要另外验证原子写入、锁、容量和迁移策略。

## 用户回答后，继续原来的 thread

`run_id` 同时用作这次执行的 `threadId`。新请求创建新编号，补充回答仍使用原编号：

```java
var config = BudgetGraph.config("demo-run-001");
var resumed = BudgetGraph.answer(
    graph, config, "alice", 1, "ADJUSTED");
graph.invoke(GraphInput.resume(), resumed);
```

`answer` 先读取检查点，核对任务主人、等待节点、等待版本和允许值，再用 `graph.updateState(snapshot.config(), ...)` 写入答案。返回的配置交给 `GraphInput.resume()`，从原任务继续。不能用普通新输入再启动一次图，假装那叫恢复。

有一个容易忽略的细节：`updateState` 返回的配置可能固定到某个检查点。恢复执行后，如果要显示最新进度，应使用只含原 `threadId` 的新配置读取最新状态，不能一直拿旧检查点配置查看过去。命令行演示已经按这个方式输出。

示例仅用状态中的授权标记测试拒绝路径，真实入口必须重新向权限服务核对。检查点里的旧授权结果不是长期通行证。此外，同一个等待问题的两个并发回答还需要持久化 `command_id` 去重，并串行处理该任务；本例没有实现分布式恢复锁。

## 根据结果下钻，但别无限循环

D_A 的汇总结果是预算 52 万、实际 56 万。如果用户要解释差异，决策器选 `drilldown`，得到 P01 的 4.2 万和 P02 的 -0.2 万；否则可直接准备导出。

下钻回来再次经过 `decide`。程序检查明细是否已经存在：若决策器仍要求重复下钻，返回错误，而不是继续查同一份数据。真实模型接入后，可以结合已完成动作、允许动作与预算给出结构化选项，并记录实际选择。

这也是固定流程与 Agent 的分界：权限、有效计划、查询校验是硬步骤；是否下钻、怎样组织说明可以交给模型在允许范围内选择。不需要把每个确定性计算都变成一次模型调用。

## 外部操作成功，图却没记住怎么办

示例在 `prepare_export` 先保存 `operation_id`，下一个节点才调用导出服务。数据库用 `(actor, operation_id)` 唯一约束识别同一次意图，并校验规范化参数哈希。

实验故意在数据库提交成功后抛异常。此时图还没保存成功返回，恢复后会重跑提交节点；导出服务返回原来的任务 ID，数据库仍只有一条任务。这里允许重复调用，业务结果靠唯一约束收敛。

不能把随机 UUID 放在提交节点里每次重新生成，否则重跑变成新意图。也不能在内存里设一个布尔值防重：换个 JVM 就丢了。完整实现见 [ExportStore.java](code/langgraph4j-demo/src/main/java/dev/learning/ExportStore.java)。

## 图走到 END，究竟完成了什么

当前示例把 `completion_scope` 明确设为 `query_and_export_task_accepted`。它完成查数和导出任务受理，未生成文件。生产流程还要等待交付 Worker，核对文件哈希、行数与总额，确认下载可用后才可以向用户报告报表交付完成。

面试时可以拿这一点展开：“图运行结束”是框架事件，“员工拿到了可核对的汇报材料”才是业务结果。两者之间还需要明确的验收步骤。

[LangGraph4j 1.8.27 发布记录](https://github.com/langgraph4j/langgraph4j/releases/tag/v1.8.27) · [GraphInput 源码](https://github.com/langgraph4j/langgraph4j/blob/v1.8.27/langgraph4j-core/src/main/java/org/bsc/langgraph4j/GraphInput.java) · [完整 BudgetGraph.java](code/langgraph4j-demo/src/main/java/dev/learning/BudgetGraph.java)

[← 业务与架构](01-先讲明白：这个%20Agent%20替员工省哪一步？.md) · [能力接入 →](03-Skill、Function%20Calling%20和%20MCP%20怎么配合.md)
