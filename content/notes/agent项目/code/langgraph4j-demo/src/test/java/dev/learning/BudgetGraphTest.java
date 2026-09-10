package dev.learning;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Path;
import java.util.*;
import org.bsc.langgraph4j.*;
import org.bsc.langgraph4j.state.AgentState;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class BudgetGraphTest {
  @TempDir Path dir;

  Map<String, Object> input(boolean details) {
    return Map.of(
        "run_id",
        "run-001",
        "actor",
        "alice",
        "authorized",
        true,
        "want_details",
        details,
        "plan_revision",
        1);
  }

  CompiledGraph<BudgetGraph.State> graph(boolean fault) throws Exception {
    return BudgetGraph.compile(dir, fault, BudgetGraph.FIXTURE_POLICY);
  }

  @Test
  void missingBasisPausesBeforeAnyBusinessTask() throws Exception {
    var g = graph(false);
    var c = BudgetGraph.config("run-001");
    g.invoke(input(true), c);
    assertEquals("await_basis", g.getState(c).next());
    assertEquals("WAITING_INPUT", g.getState(c).state().text("status"));
    assertEquals(0, new ExportStore(dir.resolve("exports")).count());
  }

  @Test
  void newSaverInstanceResumesSameThread() throws Exception {
    var c = BudgetGraph.config("run-001");
    graph(false).invoke(input(true), c);
    var restarted = graph(false);
    c = BudgetGraph.answer(restarted, c, "alice", 1, "ADJUSTED");
    var result = restarted.invoke(GraphInput.resume(), c).orElseThrow();
    assertEquals("SUCCEEDED", result.text("status"));
    assertEquals(56_000_000L, result.<Long>value("actual_cents").orElseThrow());
    assertEquals(4_200_000L, result.<Long>value("p01_variance_cents").orElseThrow());
    assertEquals(-200_000L, result.<Long>value("p02_variance_cents").orElseThrow());
  }

  @Test
  void lostResponseReplaysSubmitWithoutCreatingAnotherTask() throws Exception {
    var c = BudgetGraph.config("run-001");
    var g = graph(true);
    g.invoke(input(false), c);
    var answered = BudgetGraph.answer(g, c, "alice", 1, "ADJUSTED");
    assertThrows(Exception.class, () -> g.invoke(GraphInput.resume(), answered));
    var store = new ExportStore(dir.resolve("exports"));
    assertEquals(1, store.count());
    var restarted = graph(false);
    assertEquals("submit_export", restarted.getState(c).next());
    var done = restarted.invoke(GraphInput.resume(), c).orElseThrow();
    assertEquals("SUCCEEDED", done.text("status"));
    assertEquals(1, store.count());
  }

  @Test
  void answerChecksOwnerAndWaitingRevision() throws Exception {
    var c = BudgetGraph.config("run-001");
    var g = graph(false);
    g.invoke(input(false), c);
    assertThrows(SecurityException.class, () -> BudgetGraph.answer(g, c, "bob", 1, "ADJUSTED"));
    assertThrows(
        IllegalStateException.class, () -> BudgetGraph.answer(g, c, "alice", 2, "ADJUSTED"));
    assertThrows(
        IllegalArgumentException.class, () -> BudgetGraph.answer(g, c, "alice", 1, "GUESS"));
  }

  @Test
  void revokedAuthorizationStopsResume() throws Exception {
    var c = BudgetGraph.config("run-001");
    var g = graph(false);
    g.invoke(input(false), c);
    g.updateState(c, Map.of("authorized", false));
    assertThrows(SecurityException.class, () -> BudgetGraph.answer(g, c, "alice", 1, "ADJUSTED"));
  }

  @Test
  void evidenceReducerDeduplicatesAndRejectsConflictingIdentity() {
    assertEquals(
        Map.of("r1", "hash"),
        BudgetGraph.mergeEvidence(Map.of("r1", "hash"), Map.of("r1", "hash")));
    assertThrows(
        IllegalArgumentException.class,
        () -> BudgetGraph.mergeEvidence(Map.of("r1", "hash"), Map.of("r1", "changed")));
  }

  @Test
  void newPlanClearsActiveEvidenceButKeepsHistory() {
    var state =
        AgentState.updateState(
            Map.of(
                "evidence_archive",
                Map.of("r1", "hash"),
                "active_result_ids",
                List.of("r1"),
                "effective_plan_id",
                "p1",
                "data_release",
                "rel-001",
                "plan_revision",
                1),
            BudgetGraph.changePlan(2),
            BudgetGraph.State.SCHEMA);
    assertEquals(List.of(), state.get("active_result_ids"));
    assertEquals(Map.of("r1", "hash"), state.get("evidence_archive"));
    assertFalse(BudgetGraph.currentEvidence(1, "p1", "rel-001", new BudgetGraph.State(state)));
  }

  @Test
  void modelCannotInventToolOrRepeatQuery() throws Exception {
    for (String action : List.of("delete_budget", "drilldown")) {
      var p = dir.resolve(action);
      java.nio.file.Files.createDirectories(p);
      var g = BudgetGraph.compile(p, false, state -> action);
      var c = BudgetGraph.config("run-001");
      var inputs = new HashMap<>(input(true));
      inputs.put("budget_basis", "ADJUSTED");
      assertThrows(Exception.class, () -> g.invoke(inputs, c));
    }
  }

  @Test
  void aChartOnlyRequestSkipsDrilldown() throws Exception {
    var g = graph(false);
    var inputs = new HashMap<>(input(false));
    inputs.put("budget_basis", "ADJUSTED");
    var done = g.invoke(inputs, BudgetGraph.config("run-001")).orElseThrow();
    assertTrue(done.text("detail_result_id").isEmpty());
    assertEquals("SUCCEEDED", done.text("status"));
  }
}
