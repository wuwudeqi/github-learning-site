"""Small local experiments, not a Java/LangGraph implementation.

Python standard library only. All data are synthetic. SQLite demonstrates
relational/uniqueness invariants, not PostgreSQL transaction parity.
Run: python3 reproduce_invariants.py
"""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest


def canonical_hash(payload):
    # This input already uses canonical domain values. A real API must normalize
    # dates, enums, ordering semantics and decimal representations first.
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def rate(actual, budget):
    return None if budget == 0 else Decimal(actual) / Decimal(budget)


def connect(path):
    db = sqlite3.connect(path, timeout=15)
    return db


def create_export(path, actor, operation, payload):
    db = connect(path)
    try:
        digest = canonical_hash(payload)
        with db:
            db.execute(
                "INSERT INTO export_task(actor,operation,payload_hash,status,token) "
                "VALUES(?,?,?,'QUEUED',0) ON CONFLICT(actor,operation) DO NOTHING",
                (actor, operation, digest),
            )
            row = db.execute(
                "SELECT id,payload_hash FROM export_task WHERE actor=? AND operation=?",
                (actor, operation),
            ).fetchone()
            if row[1] != digest:
                raise ValueError("IDEMPOTENCY_CONFLICT")
            return row[0]
    finally:
        db.close()


class Invariants(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="budget-agent-lab-")
        self.path = str(Path(self.temp.name) / "lab.sqlite")
        self.db = connect(self.path)
        self.db.executescript("""
            CREATE TABLE budget(release TEXT,project TEXT,amount INTEGER);
            CREATE TABLE actual(release TEXT,project TEXT,amount INTEGER);
            CREATE TABLE export_task(
                id INTEGER PRIMARY KEY,
                actor TEXT NOT NULL, operation TEXT NOT NULL,
                payload_hash TEXT NOT NULL, status TEXT NOT NULL,
                token INTEGER NOT NULL, file_key TEXT,
                UNIQUE(actor,operation)
            );
        """)
        # Integers are cents, never binary floating-point financial values.
        self.db.executemany("INSERT INTO budget VALUES(?,?,?)", [
            ("r1", "P01", 70_000_000), ("r1", "P02", 50_000_000)])
        self.db.executemany("INSERT INTO actual VALUES(?,?,?)", [
            ("r1", "P01", 30_000_000), ("r1", "P01", 47_000_000),
            ("r1", "P02", 49_000_000)])
        self.db.commit()
        self.payload = {"plan_id": "plan-1", "release": "r1", "format": "xlsx"}

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_01_join_fanout_and_preaggregation(self):
        wrong = self.db.execute("""
            SELECT SUM(b.amount),SUM(a.amount)
            FROM budget b JOIN actual a
              ON a.project=b.project AND a.release=b.release
            WHERE b.release='r1' AND b.project='P01'
        """).fetchone()
        corrected = self.db.execute("""
            WITH b AS (SELECT project,SUM(amount) amount FROM budget
              WHERE release='r1' GROUP BY project),
            a AS (SELECT project,SUM(amount) amount FROM actual
              WHERE release='r1' GROUP BY project)
            SELECT b.amount,a.amount FROM b JOIN a USING(project)
            WHERE project='P01'
        """).fetchone()
        self.assertEqual(wrong, (140_000_000, 77_000_000))
        self.assertEqual(corrected, (70_000_000, 77_000_000))
        self.assertEqual(rate(wrong[1], wrong[0]), Decimal("0.55"))
        self.assertEqual(rate(corrected[1], corrected[0]), Decimal("1.1"))

    def test_02_ratio_of_sums_not_average_of_ratios(self):
        wrong = (rate(77, 70) + rate(49, 50)) / 2
        correct = rate(126, 120)
        self.assertEqual(wrong, Decimal("1.04"))
        self.assertEqual(correct, Decimal("1.05"))

    def test_03_zero_budget_is_undefined(self):
        self.assertIsNone(rate(20, 0))
        self.assertEqual(rate(0, 100), Decimal("0"))

    def test_04_pinned_release_survives_new_release(self):
        old = self.db.execute("SELECT SUM(amount) FROM actual WHERE release='r1'").fetchone()[0]
        with self.db:
            self.db.execute("INSERT INTO actual SELECT 'r2',project,amount FROM actual WHERE release='r1'")
            self.db.execute("UPDATE actual SET amount=52000000 WHERE release='r2' AND project='P02'")
        new = self.db.execute("SELECT SUM(amount) FROM actual WHERE release='r2'").fetchone()[0]
        replay = self.db.execute("SELECT SUM(amount) FROM actual WHERE release='r1'").fetchone()[0]
        self.assertNotEqual(old, new)
        self.assertEqual(old, replay)
        self.assertEqual((old, new), (126_000_000, 129_000_000))

    def test_05_retry_after_lost_response_returns_same_task(self):
        committed = create_export(self.path, "alice", "op-1", self.payload)
        # Pretend the first response never reached the caller.
        retry = create_export(self.path, "alice", "op-1", self.payload)
        self.assertEqual(committed, retry)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM export_task").fetchone()[0], 1)

    def test_06_same_operation_changed_payload_conflicts(self):
        first = create_export(self.path, "alice", "op-1", self.payload)
        with self.assertRaisesRegex(ValueError, "IDEMPOTENCY_CONFLICT"):
            create_export(self.path, "alice", "op-1", {**self.payload, "release": "r2"})
        self.assertEqual(first, create_export(self.path, "alice", "op-1", self.payload))

    def test_07_new_intent_same_parameters_is_allowed(self):
        a = create_export(self.path, "alice", "op-1", self.payload)
        b = create_export(self.path, "alice", "op-2", self.payload)
        self.assertNotEqual(a, b)

    def test_08_concurrent_duplicates_create_one_logical_task(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(lambda _: create_export(
                self.path, "alice", "op-parallel", self.payload), range(12)))
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM export_task").fetchone()[0], 1)

    def test_09_actor_namespace_does_not_merge_tasks(self):
        a = create_export(self.path, "alice", "op-1", self.payload)
        b = create_export(self.path, "bob", "op-1", self.payload)
        self.assertNotEqual(a, b)

    def test_10_stale_worker_cannot_publish(self):
        task = create_export(self.path, "alice", "op-1", self.payload)
        with self.db:
            self.db.execute("UPDATE export_task SET status='RUNNING',token=2 WHERE id=?", (task,))
            stale = self.db.execute("""UPDATE export_task SET status='SUCCEEDED',file_key='old'
                WHERE id=? AND status='RUNNING' AND token=1""", (task,)).rowcount
            current = self.db.execute("""UPDATE export_task SET status='SUCCEEDED',file_key='new'
                WHERE id=? AND status='RUNNING' AND token=2""", (task,)).rowcount
        self.assertEqual((stale, current), (0, 1))
        self.assertEqual(self.db.execute("SELECT file_key FROM export_task WHERE id=?", (task,)).fetchone()[0], "new")

    def test_11_json_key_order_does_not_change_hash(self):
        self.assertEqual(canonical_hash({"a": 1, "b": 2}), canonical_hash({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
