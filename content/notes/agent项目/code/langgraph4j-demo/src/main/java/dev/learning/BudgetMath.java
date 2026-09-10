package dev.learning;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.RoundingMode;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** 合成数据实验：整数分、完整规则、按事实分币。 */
public final class BudgetMath {
  private BudgetMath() {}

  public record Share(String target, BigDecimal ratio) {
    public Share {
      Objects.requireNonNull(target);
      ratio = Objects.requireNonNull(ratio).stripTrailingZeros();
    }
  }

  public record Rule(
      String id, String axis, String measure, Map<String, List<Share>> projects, boolean approved) {
    public Rule {
      var copy = new TreeMap<String, List<Share>>();
      projects.forEach((k, v) -> copy.put(k, List.copyOf(v)));
      projects = Collections.unmodifiableMap(copy);
    }
  }

  public static List<Share> shares(String a, String ratio) {
    BigDecimal x = new BigDecimal(ratio);
    return List.of(new Share(a + "_A", x), new Share(a + "_B", BigDecimal.ONE.subtract(x)));
  }

  public static final Map<String, Long> BUDGET = Map.of("P01", 70_000_000L, "P02", 50_000_000L);
  public static final Map<String, Long> ACTUAL = Map.of("P01", 77_000_000L, "P02", 49_000_000L);
  public static final Map<String, List<Share>> DEPARTMENT =
      Map.of("P01", shares("D", "0.6"), "P02", shares("D", "0.2"));
  public static final Rule B1 =
      new Rule("budget-dept-v1", "DEPARTMENT", "BUDGET", DEPARTMENT, true);
  public static final Rule A1 =
      new Rule("actual-dept-v1", "DEPARTMENT", "ACTUAL", DEPARTMENT, true);

  public static Map<String, Long> allocate(long cents, List<Share> shares) {
    if (shares == null || shares.isEmpty()) throw new IllegalArgumentException("MISSING_RULE");
    Set<String> seen = new HashSet<>();
    BigDecimal total = BigDecimal.ZERO;
    for (Share s : shares) {
      if (!seen.add(s.target())) throw new IllegalArgumentException("DUPLICATE_TARGET");
      if (s.ratio().signum() < 0 || s.ratio().compareTo(BigDecimal.ONE) > 0)
        throw new IllegalArgumentException("INVALID_RATIO");
      total = total.add(s.ratio());
    }
    if (total.compareTo(BigDecimal.ONE) != 0)
      throw new IllegalArgumentException("RATIO_TOTAL_NOT_ONE");
    BigInteger magnitude = BigInteger.valueOf(cents).abs();
    Map<String, BigInteger> units = new TreeMap<>();
    Map<String, BigDecimal> remainders = new HashMap<>();
    for (Share s : shares) {
      BigDecimal exact = new BigDecimal(magnitude).multiply(s.ratio());
      BigInteger floor = exact.setScale(0, RoundingMode.FLOOR).toBigIntegerExact();
      units.put(s.target(), floor);
      remainders.put(s.target(), exact.subtract(new BigDecimal(floor)));
    }
    int remaining =
        magnitude
            .subtract(units.values().stream().reduce(BigInteger.ZERO, BigInteger::add))
            .intValueExact();
    List<String> order = new ArrayList<>(units.keySet());
    order.sort(
        Comparator.<String, BigDecimal>comparing(remainders::get)
            .reversed()
            .thenComparing(Comparator.naturalOrder()));
    for (int i = 0; i < remaining; i++)
      units.compute(order.get(i), (k, v) -> v.add(BigInteger.ONE));
    Map<String, Long> result = new TreeMap<>();
    units.forEach((k, v) -> result.put(k, (cents < 0 ? v.negate() : v).longValueExact()));
    return result;
  }

  public static Map<String, Long> aggregate(Map<String, Long> facts, Rule rule) {
    if (!rule.approved()) throw new IllegalArgumentException("RULE_NOT_APPROVED");
    Map<String, Long> result = new TreeMap<>();
    facts.forEach(
        (p, cents) ->
            allocate(cents, rule.projects().get(p))
                .forEach((k, v) -> result.merge(k, v, Math::addExact)));
    return result;
  }

  public static void checkComparison(Rule budget, Rule actual, Set<String> approvedPairs) {
    if (!budget.measure().equals("BUDGET") || !actual.measure().equals("ACTUAL"))
      throw new IllegalArgumentException("MEASURE_RULE_MISMATCH");
    if (!budget.axis().equals(actual.axis())) throw new IllegalArgumentException("AXIS_MISMATCH");
    if (!approvedPairs.contains(budget.id() + "/" + actual.id()))
      throw new IllegalArgumentException("COMPARISON_POLICY_REQUIRED");
  }

  public static Optional<BigDecimal> rate(long actual, long budget) {
    return budget == 0
        ? Optional.empty()
        : Optional.of(
            BigDecimal.valueOf(actual)
                .divide(BigDecimal.valueOf(budget), 12, RoundingMode.HALF_UP));
  }

  /** 示例契约只接收已经规范化的字符串字段，用长度前缀消除连接歧义。 */
  public static String digest(Map<String, String> fields) {
    StringBuilder text = new StringBuilder();
    new TreeMap<>(fields)
        .forEach(
            (k, v) ->
                text.append(k.length())
                    .append(':')
                    .append(k)
                    .append(v.length())
                    .append(':')
                    .append(v));
    try {
      return HexFormat.of()
          .formatHex(
              MessageDigest.getInstance("SHA-256")
                  .digest(text.toString().getBytes(StandardCharsets.UTF_8)));
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  public static void publish(Map<String, Rule> registry, Rule rule) {
    Rule old = registry.putIfAbsent(rule.id(), rule);
    if (old != null && !old.equals(rule))
      throw new IllegalArgumentException("IMMUTABLE_RULE_ID_CONFLICT");
  }
}
