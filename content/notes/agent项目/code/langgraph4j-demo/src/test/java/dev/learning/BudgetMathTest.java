package dev.learning;

import static dev.learning.BudgetMath.*;
import static org.junit.jupiter.api.Assertions.*;

import java.math.BigDecimal;
import java.util.*;
import org.junit.jupiter.api.Test;

class BudgetMathTest {
  @Test
  void departmentMatchesHandCalculatedOracle() {
    assertEquals(Map.of("D_A", 52_000_000L, "D_B", 68_000_000L), aggregate(BUDGET, B1));
    assertEquals(Map.of("D_A", 56_000_000L, "D_B", 70_000_000L), aggregate(ACTUAL, A1));
  }

  @Test
  void independentAxesAreNotAdditive() {
    long total = 0;
    for (var m :
        List.of(
            DEPARTMENT,
            Map.of("P01", shares("I", "0.5"), "P02", shares("I", "0.3")),
            Map.of("P01", shares("T", "0.75"), "P02", shares("T", "0.4")))) {
      long n =
          aggregate(ACTUAL, new Rule("x", "X", "ACTUAL", m, true)).values().stream()
              .mapToLong(Long::longValue)
              .sum();
      assertEquals(126_000_000L, n);
      total += n;
    }
    assertEquals(378_000_000L, total);
  }

  @Test
  void missingAndUnapprovedRulesStopCalculation() {
    assertThrows(IllegalArgumentException.class, () -> aggregate(Map.of("P03", 100L), A1));
    assertThrows(
        IllegalArgumentException.class,
        () -> aggregate(ACTUAL, new Rule("x", "D", "ACTUAL", DEPARTMENT, false)));
  }

  @Test
  void invalidRatiosAndDuplicateTargetsAreRejected() {
    for (var rates :
        List.of(
            List.of(new Share("A", new BigDecimal(".6")), new Share("B", new BigDecimal(".3"))),
            shares("D", "1.1"),
            List.of(new Share("A", new BigDecimal(".5")), new Share("A", new BigDecimal(".5")))))
      assertThrows(IllegalArgumentException.class, () -> allocate(100, rates));
  }

  @Test
  void remainderTieBreakDoesNotDependOnInputOrder() {
    var s = shares("D", "0.5");
    assertEquals(Map.of("D_A", 1L, "D_B", 0L), allocate(1, s));
    assertEquals(allocate(1, s), allocate(1, s.reversed()));
    for (long n : new long[] {0, 1, 2, 101, 999_999_999_999L})
      assertEquals(n, allocate(n, s).values().stream().mapToLong(Long::longValue).sum());
  }

  @Test
  void reversalCancelsEveryTarget() {
    var s =
        List.of(
            new Share("A", new BigDecimal(".333333")),
            new Share("B", new BigDecimal(".333333")),
            new Share("C", new BigDecimal(".333334")));
    for (long n : new long[] {1, 2, 7, 101, 999_999}) {
      var plus = allocate(n, s);
      var minus = allocate(-n, s);
      plus.forEach((k, v) -> assertEquals(0L, v + minus.get(k)));
    }
  }

  @Test
  void roundingBeforeAggregationIsDifferent() {
    var half = shares("D", ".5");
    var byFact =
        aggregate(
            Map.of("P01", 1L, "P02", 1L),
            new Rule("x", "D", "ACTUAL", Map.of("P01", half, "P02", half), true));
    assertEquals(2L, byFact.get("D_A"));
    assertEquals(1L, allocate(2, half).get("D_A"));
  }

  @Test
  void comparisonNeedsApprovedPairAndCorrectMeasures() {
    assertDoesNotThrow(() -> checkComparison(B1, A1, Set.of(B1.id() + "/" + A1.id())));
    assertThrows(IllegalArgumentException.class, () -> checkComparison(B1, A1, Set.of()));
    assertThrows(IllegalArgumentException.class, () -> checkComparison(A1, B1, Set.of()));
  }

  @Test
  void publishedRuleCannotChangeUnderSameId() {
    var registry = new HashMap<String, Rule>();
    publish(registry, A1);
    var changed =
        new Rule(
            A1.id(),
            A1.axis(),
            A1.measure(),
            Map.of("P01", shares("D", ".5"), "P02", shares("D", ".2")),
            true);
    assertThrows(IllegalArgumentException.class, () -> publish(registry, changed));
    assertEquals(56_000_000L, aggregate(ACTUAL, registry.get(A1.id())).get("D_A"));
  }

  @Test
  void eachSemanticVersionChangesPlanDigest() {
    var plan =
        new HashMap<>(
            Map.of(
                "data_release",
                "r1",
                "axis",
                "DEPARTMENT",
                "budget_rule",
                "b1",
                "actual_rule",
                "a1",
                "comparison_policy",
                "c1",
                "rounding_policy",
                "round1",
                "metric_version",
                "m1",
                "scope",
                "alice",
                "period",
                "2026H1",
                "mapping_version",
                "org1"));
    String old = digest(plan);
    for (String k : List.copyOf(plan.keySet())) {
      var next = new HashMap<>(plan);
      next.put(k, plan.get(k) + "-changed");
      assertNotEquals(old, digest(next));
    }
  }

  @Test
  void visibilityDoesNotRenormalizeShares() {
    assertEquals(46_200_000L, aggregate(Map.of("P01", 77_000_000L), A1).get("D_A"));
  }

  @Test
  void marginalsDoNotDetermineJointShares() {
    var first =
        List.of(
            new BigDecimal(".5"), new BigDecimal(".1"), new BigDecimal("0"), new BigDecimal(".4"));
    var second =
        List.of(
            new BigDecimal(".1"), new BigDecimal(".5"), new BigDecimal(".4"), new BigDecimal("0"));
    for (var joint : List.of(first, second)) {
      assertEquals(0, joint.get(0).add(joint.get(1)).compareTo(new BigDecimal(".6")));
      assertEquals(0, joint.get(0).add(joint.get(2)).compareTo(new BigDecimal(".5")));
    }
    assertNotEquals(first.get(0), second.get(0));
  }
}
