package dev.learning;

import static org.bsc.langgraph4j.StateGraph.*;
import static org.bsc.langgraph4j.action.AsyncEdgeAction.edge_async;
import static org.bsc.langgraph4j.action.AsyncNodeAction.node_async;

import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import org.bsc.langgraph4j.*;
import org.bsc.langgraph4j.checkpoint.FileSystemSaver;
import org.bsc.langgraph4j.serializer.std.ObjectStreamStateSerializer;
import org.bsc.langgraph4j.state.*;

public final class BudgetGraph {
  public static final class State extends AgentState {
    public State(Map<String, Object> data) {
      super(data);
    }

    public String text(String key) {
      return this.<String>value(key).orElse("");
    }

    public int revision() {
      return this.<Integer>value("plan_revision").orElse(1);
    }

    public static final Map<String, Channel<?>> SCHEMA =
        Map.of(
            "evidence_archive",
                Channels.<Map<String, String>>base(BudgetGraph::mergeEvidence, HashMap::new),
            "active_result_ids", Channels.<List<String>>base(ArrayList::new));
  }

  public interface NextStepPolicy {
    String choose(State state);
  }

  /** 固定测试替身，实际应用在此适配 LangChain4j 或 Spring AI 的模型响应。 */
  public static final NextStepPolicy FIXTURE_POLICY =
      state ->
          state.<Boolean>value("want_details").orElse(false)
                  && state.text("detail_result_id").isEmpty()
              ? "drilldown"
              : "export";

  public static Map<String, String> mergeEvidence(
      Map<String, String> old, Map<String, String> update) {
    var result = new HashMap<>(old == null ? Map.of() : old);
    update.forEach(
        (id, hash) -> {
          String previous = result.putIfAbsent(id, hash);
          if (previous != null && !previous.equals(hash))
            throw new IllegalArgumentException("EVIDENCE_ID_CONFLICT");
        });
    return result;
  }

  public static Map<String, Object> changePlan(int revision) {
    return Map.of(
        "plan_revision",
        revision,
        "effective_plan_id",
        "",
        "active_result_ids",
        List.of(),
        "detail_result_id",
        "");
  }

  public static boolean currentEvidence(
      int revision, String planId, String dataRelease, State state) {
    return revision == state.revision()
        && planId.equals(state.text("effective_plan_id"))
        && dataRelease.equals(state.text("data_release"));
  }

  public static RunnableConfig config(String run) {
    // 演示只接收受信任务编号；不能把任意路径放进 FileSystemSaver 的 threadId。
    if (!run.matches("[a-zA-Z0-9_-]{1,64}")) throw new IllegalArgumentException("INVALID_RUN_ID");
    return RunnableConfig.builder().threadId(run).build();
  }

  public static CompiledGraph<State> compile(
      Path directory, boolean loseResponse, NextStepPolicy policy) throws Exception {
    java.nio.file.Files.createDirectories(directory);
    ExportStore exports = new ExportStore(directory.resolve("exports"));
    AtomicBoolean fault = new AtomicBoolean(loseResponse);
    var workflow =
        new StateGraph<>(State.SCHEMA, new ObjectStreamStateSerializer<>(State::new))
            .addNode(
                "resolve",
                node_async(
                    state ->
                        state.text("budget_basis").isEmpty()
                            ? Map.of(
                                "status",
                                "WAITING_INPUT",
                                "pending_question",
                                "预算用年初版还是调整后？",
                                "waiting_revision",
                                state.revision())
                            : Map.of("status", "RUNNING")))
            .addNode(
                "await_basis",
                node_async(
                    state -> {
                      if (!Set.of("ADJUSTED", "INITIAL").contains(state.text("budget_basis")))
                        throw new IllegalArgumentException("INVALID_BASIS");
                      return Map.of("status", "RUNNING", "pending_question", "");
                    }))
            .addNode(
                "validate_plan",
                node_async(
                    state -> {
                      if (!"ADJUSTED".equals(state.text("budget_basis")))
                        throw new IllegalArgumentException("DEMO_ONLY_HAS_ADJUSTED_BUDGET");
                      if (!state.<Boolean>value("authorized").orElse(false))
                        throw new SecurityException("FORBIDDEN");
                      return Map.of(
                          "effective_plan_id",
                          state.text("run_id") + "-plan-" + state.revision(),
                          "data_release",
                          "rel-001");
                    }))
            .addNode(
                "query_summary",
                node_async(
                    state -> {
                      long budget =
                          BudgetMath.aggregate(BudgetMath.BUDGET, BudgetMath.B1).get("D_A");
                      long actual =
                          BudgetMath.aggregate(BudgetMath.ACTUAL, BudgetMath.A1).get("D_A");
                      String id = state.text("effective_plan_id") + "-summary";
                      return Map.of(
                          "budget_cents",
                          budget,
                          "actual_cents",
                          actual,
                          "variance_cents",
                          actual - budget,
                          "summary_result_id",
                          id,
                          "active_result_ids",
                          List.of(id),
                          "evidence_archive",
                          Map.of(
                              id,
                              BudgetMath.digest(
                                  Map.of(
                                      "budget",
                                      Long.toString(budget),
                                      "actual",
                                      Long.toString(actual)))));
                    }))
            .addNode(
                "decide",
                node_async(
                    state -> {
                      String action = policy.choose(state);
                      if (!Set.of("drilldown", "export").contains(action))
                        throw new IllegalArgumentException("TOOL_NOT_ALLOWED");
                      if (action.equals("drilldown") && !state.text("detail_result_id").isEmpty())
                        throw new IllegalArgumentException("REPEATED_QUERY");
                      return Map.of("next_action", action);
                    }))
            .addNode(
                "query_project",
                node_async(
                    state -> {
                      String id = state.text("effective_plan_id") + "-detail";
                      long p01 =
                          BudgetMath.allocate(7_000_000L, BudgetMath.shares("D", "0.6")).get("D_A");
                      long p02 =
                          BudgetMath.allocate(-1_000_000L, BudgetMath.shares("D", "0.2"))
                              .get("D_A");
                      return Map.of(
                          "detail_result_id",
                          id,
                          "p01_variance_cents",
                          p01,
                          "p02_variance_cents",
                          p02,
                          "active_result_ids",
                          List.of(state.text("summary_result_id"), id),
                          "evidence_archive",
                          Map.of(
                              id,
                              BudgetMath.digest(
                                  Map.of("P01", Long.toString(p01), "P02", Long.toString(p02)))));
                    }))
            .addNode(
                "prepare_export",
                node_async(
                    state ->
                        Map.of(
                            "operation_id",
                            state.text("run_id") + "-r" + state.revision() + "-export-1")))
            .addNode(
                "submit_export",
                node_async(
                    state -> {
                      long id =
                          exports.create(
                              state.text("actor"),
                              state.text("operation_id"),
                              Map.of(
                                  "result_id",
                                  state.text("summary_result_id"),
                                  "format",
                                  "xlsx",
                                  "data_release",
                                  state.text("data_release")));
                      if (fault.compareAndSet(true, false))
                        throw new IllegalStateException("SIMULATED_RESPONSE_LOST_AFTER_COMMIT");
                      return Map.of("artifact_job_id", id);
                    }))
            .addNode(
                "finish",
                node_async(
                    state ->
                        Map.of(
                            "status",
                            "SUCCEEDED",
                            "completion_scope",
                            "query_and_export_task_accepted")))
            .addEdge(START, "resolve")
            .addConditionalEdges(
                "resolve",
                edge_async(state -> state.text("budget_basis").isEmpty() ? "clarify" : "ready"),
                Map.of("clarify", "await_basis", "ready", "validate_plan"))
            .addEdge("await_basis", "validate_plan")
            .addEdge("validate_plan", "query_summary")
            .addEdge("query_summary", "decide")
            .addConditionalEdges(
                "decide",
                edge_async(state -> state.text("next_action")),
                Map.of("drilldown", "query_project", "export", "prepare_export"))
            .addEdge("query_project", "decide")
            .addEdge("prepare_export", "submit_export")
            .addEdge("submit_export", "finish")
            .addEdge("finish", END);
    return workflow.compile(
        CompileConfig.builder()
            .checkpointSaver(
                new FileSystemSaver(
                    directory.resolve("checkpoints"), workflow.getStateSerializer()))
            .interruptBefore("await_basis")
            .releaseThread(false)
            .recursionLimit(20)
            .build());
  }

  public static RunnableConfig answer(
      CompiledGraph<State> graph,
      RunnableConfig config,
      String actor,
      int waitingRevision,
      String basis)
      throws Exception {
    var snapshot = graph.getState(config);
    State state = snapshot.state();
    if (!state.text("actor").equals(actor)) throw new SecurityException("RUN_OWNER_MISMATCH");
    if (!state.<Boolean>value("authorized").orElse(false)) throw new SecurityException("FORBIDDEN");
    if (!"await_basis".equals(snapshot.next())
        || state.<Integer>value("waiting_revision").orElse(-1) != waitingRevision)
      throw new IllegalStateException("STALE_ANSWER");
    if (!Set.of("ADJUSTED", "INITIAL").contains(basis))
      throw new IllegalArgumentException("INVALID_BASIS");
    // 调用者必须串行恢复同一 run，并持久化 command_id 去重；这里仅演示单执行者。
    return graph.updateState(snapshot.config(), Map.of("budget_basis", basis));
  }
}
