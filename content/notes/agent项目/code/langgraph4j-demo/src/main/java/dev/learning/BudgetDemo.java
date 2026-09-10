package dev.learning;

import java.nio.file.*;
import java.util.*;
import org.bsc.langgraph4j.GraphInput;

/** 三条命令在三个独立 JVM 中运行；不调用真实模型、不生成 Excel 文件。 */
public final class BudgetDemo {
  public static void main(String[] args) throws Exception {
    if (args.length < 2) throw new IllegalArgumentException("用法: start|answer|resume <演示目录>");
    Path directory = Path.of(args[1]).toAbsolutePath();
    Files.createDirectories(directory);
    var graph =
        BudgetGraph.compile(directory, args[0].equals("answer"), BudgetGraph.FIXTURE_POLICY);
    var config = BudgetGraph.config("demo-run-001");
    if (args[0].equals("start")) {
      try (var files = Files.list(directory.resolve("checkpoints"))) {
        if (files.findAny().isPresent()) throw new IllegalStateException("请为新实验选择空目录");
      }
      graph.invoke(
          Map.of(
              "run_id",
              "demo-run-001",
              "actor",
              "alice",
              "authorized",
              true,
              "plan_revision",
              1,
              "want_details",
              true),
          config);
    } else if (args[0].equals("answer")) {
      config = BudgetGraph.answer(graph, config, "alice", 1, "ADJUSTED");
      try {
        graph.invoke(GraphInput.resume(), config);
      } catch (Exception e) {
        if (!rootMessage(e).contains("SIMULATED_RESPONSE_LOST_AFTER_COMMIT")) throw e;
        System.out.println("已注入故障：导出任务已提交，图尚未收到返回。");
      }
    } else if (args[0].equals("resume")) {
      graph.invoke(GraphInput.resume(), config);
    } else throw new IllegalArgumentException("未知命令");
    // updateState 返回的配置可能固定在某个检查点；展示进度时重新读取线程最新状态。
    var state = graph.getState(BudgetGraph.config("demo-run-001"));
    System.out.println("next=" + state.next() + " state=" + state.state().data());
    System.out.println(
        "export_task_count=" + new ExportStore(directory.resolve("exports")).count());
  }

  private static String rootMessage(Throwable e) {
    while (e.getCause() != null) e = e.getCause();
    return String.valueOf(e.getMessage());
  }
}
