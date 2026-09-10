预算 Agent：Java 21 + LangGraph4j 1.8.27 演示

需要 JDK 21、Maven 3.9+、首次下载 Maven 依赖的网络连接。
不需要模型 API key。所有金额是合成算例。在本目录执行：
  mvn -B -ntp test

32 项 JUnit 检查：12 项分摊、11 项业务一致性、9 项图状态/恢复。

在三个独立进程中按顺序执行（目录必须是本轮实验专用的新目录）：
  mvn -B -ntp exec:java '-Dexec.args=start /tmp/budget-agent-demo-01'
  mvn -B -ntp exec:java '-Dexec.args=answer /tmp/budget-agent-demo-01'
  mvn -B -ntp exec:java '-Dexec.args=resume /tmp/budget-agent-demo-01'

start：缺预算口径，next=await_basis，export_task_count=0。
answer：回答调整后预算，提交任务后模拟响应丢失；next=submit_export，count=1。
resume：新 JVM 恢复原 thread，next=__END__，count 仍为 1。
预算/实际/差额以分打印：52000000 / 56000000 / 4000000。
answer 和部分负例测试会打印预期异常；以最终测试报告和命令结果判断。

文件：
  BudgetMath.java：精确分摊、尾差、规则与摘要。
  ExportStore.java：H2 唯一约束、意图冲突、发布 token。
  BudgetGraph.java：状态与 reducer、条件边、静态断点和恢复。
  BudgetDemo.java：三进程演示入口。
  src/test：上述机制的行为测试。

pom 将编译输出放在 java.io.tmpdir/budget-agent-langgraph4j-build，避免把 target 打入资料网站。
不要同时运行多个此工程的 Maven 构建。示例任务状态与 H2 文件保存在传入的实验目录。

实际范围：
决策器为固定替身。代码验证查询与导出任务受理，不生成 Excel 或 SVG。
Spring Boot HTTP、真实模型、生产身份/权限、MCP、PostgreSQL RLS 尚未接入。
授权标记是测试夹具；生产恢复入口必须重新鉴权。
调用方需串行恢复同一 run，并持久化 command_id 去重；本例未实现分布式恢复锁。
FileSystemSaver 只验证单执行者下干净进程重启，不承诺写入时断电安全或并发写入。
ObjectStreamStateSerializer 的检查点仅供本应用受信写入，不能读取用户上传的序列化文件。
演示仅含调整后预算数据；选择 INITIAL 会明确拒绝，不冒充年初数据。
H2 自动提交冲突处理不能原样等同 PostgreSQL 事务内错误恢复。

官方版本：https://github.com/langgraph4j/langgraph4j/releases/tag/v1.8.27
