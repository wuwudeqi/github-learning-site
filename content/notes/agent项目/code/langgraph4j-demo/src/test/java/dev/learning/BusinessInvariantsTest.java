package dev.learning;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigDecimal;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;

class BusinessInvariantsTest {
  @TempDir Path dir;
  ExportStore store;
  final Map<String, String> payload =
      Map.of("result_id", "res-1", "data_release", "r1", "format", "xlsx");

  @BeforeEach
  void setup() throws Exception {
    store = new ExportStore(dir.resolve("lab"));
    try (var db = store.open();
        var s = db.createStatement()) {
      s.execute("CREATE TABLE budget(release_id VARCHAR,project VARCHAR,cents BIGINT)");
      s.execute("CREATE TABLE actual(release_id VARCHAR,project VARCHAR,cents BIGINT)");
      s.execute("INSERT INTO budget VALUES('r1','P01',70000000),('r1','P02',50000000)");
      s.execute(
          "INSERT INTO actual VALUES('r1','P01',30000000),('r1','P01',47000000),('r1','P02',49000000)");
    }
  }

  long[] query(String sql) throws Exception {
    try (var db = store.open();
        var s = db.createStatement();
        var r = s.executeQuery(sql)) {
      r.next();
      long[] out = new long[r.getMetaData().getColumnCount()];
      for (int i = 0; i < out.length; i++) out[i] = r.getLong(i + 1);
      return out;
    }
  }

  @Test
  void joinFanoutRequiresPreaggregation() throws Exception {
    assertArrayEquals(
        new long[] {140_000_000L, 77_000_000L},
        query(
            "SELECT SUM(b.cents),SUM(a.cents) FROM budget b JOIN actual a ON a.project=b.project AND a.release_id=b.release_id WHERE b.project='P01'"));
    assertArrayEquals(
        new long[] {70_000_000L, 77_000_000L},
        query(
            "WITH b AS (SELECT project,SUM(cents) amount FROM budget WHERE release_id='r1' GROUP BY project),a AS (SELECT project,SUM(cents) amount FROM actual WHERE release_id='r1' GROUP BY project) SELECT b.amount,a.amount FROM b JOIN a ON b.project=a.project WHERE b.project='P01'"));
  }

  @Test
  void ratioOfSumsIsNotMeanOfRatios() {
    BigDecimal wrong =
        BudgetMath.rate(77, 70)
            .orElseThrow()
            .add(BudgetMath.rate(49, 50).orElseThrow())
            .divide(BigDecimal.TWO);
    assertEquals(0, wrong.compareTo(new BigDecimal("1.04")));
    assertEquals(0, BudgetMath.rate(126, 120).orElseThrow().compareTo(new BigDecimal("1.05")));
  }

  @Test
  void zeroBudgetIsUndefined() {
    assertTrue(BudgetMath.rate(20, 0).isEmpty());
    assertEquals(0, BudgetMath.rate(0, 100).orElseThrow().signum());
  }

  @Test
  void newReleaseDoesNotChangePinnedData() throws Exception {
    try (var db = store.open();
        var s = db.createStatement()) {
      s.execute("INSERT INTO actual SELECT 'r2',project,cents FROM actual WHERE release_id='r1'");
      s.execute("UPDATE actual SET cents=52000000 WHERE release_id='r2' AND project='P02'");
    }
    assertEquals(126_000_000L, query("SELECT SUM(cents) FROM actual WHERE release_id='r1'")[0]);
    assertEquals(129_000_000L, query("SELECT SUM(cents) FROM actual WHERE release_id='r2'")[0]);
  }

  @Test
  void retryAfterLostResponseReturnsSameTask() throws Exception {
    long first = store.create("alice", "op-1", payload);
    assertEquals(first, new ExportStore(dir.resolve("lab")).create("alice", "op-1", payload));
    assertEquals(1, store.count());
  }

  @Test
  void sameOperationWithDifferentPayloadConflicts() throws Exception {
    store.create("alice", "op-1", payload);
    assertThrows(
        IllegalArgumentException.class,
        () -> store.create("alice", "op-1", Map.of("result_id", "res-2")));
    assertEquals(1, store.count());
  }

  @Test
  void laterUserIntentGetsAnotherTask() throws Exception {
    assertNotEquals(store.create("alice", "op-1", payload), store.create("alice", "op-2", payload));
  }

  @Test
  void concurrentDuplicatesCreateOneLogicalTask() throws Exception {
    try (var pool = Executors.newFixedThreadPool(4)) {
      List<Callable<Long>> calls = new ArrayList<>();
      for (int i = 0; i < 12; i++) calls.add(() -> store.create("alice", "op-parallel", payload));
      Set<Long> ids = new HashSet<>();
      for (Future<Long> f : pool.invokeAll(calls)) ids.add(f.get());
      assertEquals(1, ids.size());
      assertEquals(1, store.count());
    }
  }

  @Test
  void actorNamespaceSeparatesTasks() throws Exception {
    assertNotEquals(store.create("alice", "op-1", payload), store.create("bob", "op-1", payload));
  }

  @Test
  void staleWorkerCannotPublish() throws Exception {
    long task = store.create("alice", "op-1", payload);
    store.claim(task, 2);
    assertFalse(store.publish(task, 1, "old-file"));
    assertTrue(store.publish(task, 2, "new-file"));
    assertFalse(store.publish(task, 2, "again"));
  }

  @Test
  void normalizedFieldOrderDoesNotChangeDigest() {
    var a = new LinkedHashMap<String, String>();
    a.put("a", "1");
    a.put("b", "2");
    var b = new LinkedHashMap<String, String>();
    b.put("b", "2");
    b.put("a", "1");
    assertEquals(BudgetMath.digest(a), BudgetMath.digest(b));
  }
}
