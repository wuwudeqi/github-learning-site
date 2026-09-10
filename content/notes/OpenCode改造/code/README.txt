OpenCode 改造专题 · 独立机制实验

定位
用 TypeScript 解释报表工具、任务状态、幂等、事件重连和取消竞态。
这不是 OpenCode fork，没有访问内部模型，没有 MCP 连接，也没有 Web/IM 服务。
fixturePlanner 固定返回 sum_by_department，真实执行的是本地报表工具。
能力快照中的版本名称是合成示例。代码保存版本标签，但未实现仓库下载、摘要校验和按版本加载。

运行
已验证 Node v22.22.3。使用可擦除的 TypeScript 语法，不需要运行时第三方依赖。
在 code 目录运行：
  node --experimental-strip-types --test lab.test.ts
  node --experimental-strip-types demo.ts /tmp/opencode-lab-my-first-run
第二条命令会创建 summary.csv 和 manifest.json。每次使用新的输出目录；已有文件会报错，不静默覆盖。
正常结果：研发 80.00；销售 150.00；总计 230.00；3 行。

静态类型检查
Node 的 type stripping 不做类型检查。独立静态检查使用 TypeScript 5.9.3 与 @types/node 22。
安装开发依赖（不会添加运行时依赖）：
  npm install --save-dev typescript@5.9.3 @types/node@22
随后运行：
  npx tsc --noEmit --strict --target ES2022 --module NodeNext --moduleResolution NodeNext --allowImportingTsExtensions --types node report.ts runtime.ts demo.ts lab.test.ts
本次验证把开发依赖装在 /tmp/opencode-mechanism-types，以免笔记目录携带 node_modules。
实际执行记录及输入、源文件 SHA256 见 output.txt。
mutation-output.txt 记录在临时副本中刻意引入两个错误的结果：覆盖部门累计值引发 4 项失败，删除取消后的提交保护引发 1 项失败。原代码未修改；这只是两个选定反例，不是完整变异测试覆盖率。

文件
report.ts       严格 CSV 子集、BigInt 金额汇总和 CSV 输出。
runtime.ts      单进程内存状态机、任务创建去重、游标事件读取、协作取消、能力版本标签快照。
demo.ts         固定模型替身 + 真实本地工具，输出结果和来源清单。
lab.test.ts     20 个行为测试；使用手算 oracle 和 Promise 闸门控制竞态。
../data/        合成输入、预期、设计样例和实际 demo 输出副本。

边界
1. TaskRuntime 的 Map 随进程退出丢失，不能跨实例去重；没有分布式 exactly-once 保证。
2. actor/channel/conversation/messageId 由调用方提供；真实服务必须由可信接入层映射身份，不能信任客户端自报 actor。
3. eventsAfter 是内存查询接口，不是持久 SSE。游标只在同一任务和运行实例内有效。
4. 取消发出 AbortSignal 并阻止迟到结果提交，无法撤销已发生的外部副作用，也不能强制结束不配合的工具。
5. runtime completed 表示内存结果提交完成。demo 在此后写文件；尚未提供产物与终态的持久原子提交。
6. runtime 信任 Tool 的返回类型。真实生成代码的结果必须经过运行时 schema、业务校验及隔离执行，这些不是 TS 类型本身能保证的。
7. CSV 是明确缩小的输入约定。接入 Excel 或任意 CSV 时应换成熟解析库并新增验收数据，不能直接扩大本解析器的承诺。
8. data/workflow-v1.txt 只是规格设计；没有通用工作流引擎。演示只有一个已知报表工具。
9. 未评测模型正确率、生产并发、Web/IM 交付、真实沙箱或公司平台运行效果。
