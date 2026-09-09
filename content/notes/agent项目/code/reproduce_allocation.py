"""Synthetic allocation experiments; this is not the production implementation.

Run with Python 3 standard library: python3 reproduce_allocation.py
Money is represented as integer cents; rules use exact Decimal values.
The rounding rule and all example allocation policies are explicit lab choices.
"""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR, localcontext
import hashlib
import json
import platform
import sqlite3
import sys
import unittest


@dataclass(frozen=True)
class Rule:
    rule_id: str
    axis: str
    measure: str
    # Immutable tuples: (project, ((target, Decimal fraction), ...)).
    projects: tuple
    approved: bool = True


def rule(rule_id, axis, measure, mapping, approved=True):
    return Rule(rule_id, axis, measure, tuple(
        (project, tuple((target, Decimal(value)) for target, value in targets))
        for project, targets in mapping.items()), approved)


def rates_for(spec, project):
    if not spec.approved:
        raise ValueError("RULE_NOT_APPROVED")
    if len({p for p, _ in spec.projects}) != len(spec.projects):
        raise ValueError("DUPLICATE_PROJECT_RULE")
    targets = dict(spec.projects).get(project)
    if not targets:
        raise ValueError("MISSING_RULE")
    if len({t for t, _ in targets}) != len(targets):
        raise ValueError("DUPLICATE_TARGET")
    if any(not ratio.is_finite() or ratio < 0 or ratio > 1
           for _, ratio in targets):
        raise ValueError("INVALID_RATIO")
    if sum((ratio for _, ratio in targets), Decimal(0)) != Decimal(1):
        raise ValueError("RATIO_TOTAL_NOT_ONE")
    return targets


def allocate_cents(cents, targets):
    """Largest remainder on absolute cents; stable target tie-break, then sign.

    The caller validates full, approved rules before any permission-based display
    filtering. This function is deliberately limited to synthetic integer cents.
    """
    if type(cents) is not int:
        raise ValueError("INTEGER_CENTS_REQUIRED")
    with localcontext() as context:
        context.prec = 60
        exact = {target: Decimal(abs(cents)) * ratio for target, ratio in targets}
        floor = {target: int(value.to_integral_value(rounding=ROUND_FLOOR))
                 for target, value in exact.items()}
        remaining = abs(cents) - sum(floor.values())
        order = sorted(exact, key=lambda target: (-(exact[target] - floor[target]), target))
        for target in order[:remaining]:
            floor[target] += 1
        sign = -1 if cents < 0 else 1
        return {target: sign * value for target, value in sorted(floor.items())}


def aggregate(facts, spec):
    result = {}
    for project, cents in sorted(facts.items()):
        for target, amount in allocate_cents(cents, rates_for(spec, project)).items():
            result[target] = result.get(target, 0) + amount
    return result


def compare(budget, actual, budget_rule, actual_rule, approved_pairs):
    if budget_rule.measure != "BUDGET" or actual_rule.measure != "ACTUAL":
        raise ValueError("MEASURE_RULE_MISMATCH")
    if budget_rule.axis != actual_rule.axis:
        raise ValueError("AXIS_MISMATCH")
    if (budget_rule.rule_id, actual_rule.rule_id) not in approved_pairs:
        raise ValueError("COMPARISON_POLICY_REQUIRED")
    return aggregate(budget, budget_rule), aggregate(actual, actual_rule)


def digest(payload):
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def rule_fingerprint(spec):
    return digest({"axis": spec.axis, "measure": spec.measure,
                   "approved": spec.approved,
                   "projects": sorted((project, sorted((target, str(value.normalize()))
                       for target, value in targets)) for project, targets in spec.projects)})


def publish(registry, spec):
    previous = registry.get(spec.rule_id)
    if previous is not None and rule_fingerprint(previous) != rule_fingerprint(spec):
        raise ValueError("IMMUTABLE_RULE_ID_CONFLICT")
    registry[spec.rule_id] = spec


DEPARTMENT = {"P01": (("D_A", "0.6"), ("D_B", "0.4")),
              "P02": (("D_A", "0.2"), ("D_B", "0.8"))}
INVESTOR = {"P01": (("I_A", "0.5"), ("I_B", "0.5")),
            "P02": (("I_A", "0.3"), ("I_B", "0.7"))}
TEAM = {"P01": (("T_A", "0.75"), ("T_B", "0.25")),
        "P02": (("T_A", "0.4"), ("T_B", "0.6"))}
BUDGET = {"P01": 70_000_000, "P02": 50_000_000}
ACTUAL = {"P01": 77_000_000, "P02": 49_000_000}
B1 = rule("budget-dept-v1", "DEPARTMENT", "BUDGET", DEPARTMENT)
A1 = rule("actual-dept-v1", "DEPARTMENT", "ACTUAL", DEPARTMENT)


class AllocationExperiments(unittest.TestCase):
    def test_01_department_hand_calculated_oracle(self):
        budget, actual = compare(BUDGET, ACTUAL, B1, A1, {(B1.rule_id, A1.rule_id)})
        self.assertEqual(budget, {"D_A": 52_000_000, "D_B": 68_000_000})
        self.assertEqual(actual, {"D_A": 56_000_000, "D_B": 70_000_000})
        self.assertEqual(actual["D_A"] - budget["D_A"], 4_000_000)
        self.assertEqual(sum(actual.values()) - sum(budget.values()), 6_000_000)

    def test_02_each_axis_conserves_but_axes_are_not_additive(self):
        totals = []
        for axis, mapping in (("DEPARTMENT", DEPARTMENT), ("INVESTOR", INVESTOR), ("TEAM", TEAM)):
            allocated = aggregate(ACTUAL, rule(axis, axis, "ACTUAL", mapping))
            self.assertEqual(sum(allocated.values()), 126_000_000)
            if axis == "TEAM":
                self.assertEqual(allocated, {"T_A": 77_350_000, "T_B": 48_650_000})
                allocated_budget = aggregate(BUDGET, rule("team-budget", axis, "BUDGET", mapping))
                self.assertEqual(allocated_budget, {"T_A": 72_500_000, "T_B": 47_500_000})
            totals.append(sum(allocated.values()))
        # Three complete views of the same costs do not create three times costs.
        self.assertEqual(sum(totals), 378_000_000)
        self.assertNotEqual(sum(totals), sum(ACTUAL.values()))

    def test_03_sql_multiple_rule_joins_duplicate_department_costs(self):
        db = sqlite3.connect(":memory:")
        try:
            db.executescript("""
                CREATE TABLE fact(project TEXT PRIMARY KEY, cents INTEGER);
                CREATE TABLE allocation(project TEXT, axis TEXT, target TEXT, bps INTEGER,
                    PRIMARY KEY(project,axis,target));
            """)
            db.executemany("INSERT INTO fact VALUES(?,?)", ACTUAL.items())
            for axis, mapping in (("D", DEPARTMENT), ("I", INVESTOR)):
                db.executemany("INSERT INTO allocation VALUES(?,?,?,?)", [
                    (project, axis, target, int(Decimal(ratio) * 10000))
                    for project, targets in mapping.items() for target, ratio in targets])
            wrong = db.execute("""
                SELECT d.target,SUM(f.cents*d.bps/10000)
                FROM fact f JOIN allocation d ON f.project=d.project AND d.axis='D'
                JOIN allocation i ON f.project=i.project AND i.axis='I'
                GROUP BY d.target ORDER BY d.target
            """).fetchall()
            correct = db.execute("""
                SELECT d.target,SUM(f.cents*d.bps/10000)
                FROM fact f JOIN allocation d ON f.project=d.project AND d.axis='D'
                GROUP BY d.target ORDER BY d.target
            """).fetchall()
            self.assertEqual(wrong, [("D_A", 112_000_000), ("D_B", 140_000_000)])
            self.assertEqual(correct, [("D_A", 56_000_000), ("D_B", 70_000_000)])
        finally:
            db.close()

    def test_04_marginals_do_not_identify_a_joint_allocation(self):
        # Both tables have department margins .6/.4 and investor margins .5/.5.
        # Their D_A/I_A cell differs, so multiplying .6*.5 is not a proven fact.
        joint_1 = {("D_A", "I_A"): Decimal(".5"), ("D_A", "I_B"): Decimal(".1"),
                   ("D_B", "I_A"): Decimal("0"), ("D_B", "I_B"): Decimal(".4")}
        joint_2 = {("D_A", "I_A"): Decimal(".1"), ("D_A", "I_B"): Decimal(".5"),
                   ("D_B", "I_A"): Decimal(".4"), ("D_B", "I_B"): Decimal("0")}
        for joint in (joint_1, joint_2):
            self.assertEqual(sum(v for (d, _), v in joint.items() if d == "D_A"), Decimal(".6"))
            self.assertEqual(sum(v for (_, i), v in joint.items() if i == "I_A"), Decimal(".5"))
            self.assertEqual(sum(joint.values()), Decimal(1))
        self.assertNotEqual(joint_1[("D_A", "I_A")], joint_2[("D_A", "I_A")])

    def test_05_missing_unapproved_and_invalid_rules_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "MISSING_RULE"):
            aggregate({"P03": 100}, A1)
        with self.assertRaisesRegex(ValueError, "RULE_NOT_APPROVED"):
            aggregate(ACTUAL, replace(A1, approved=False))
        cases = [(".6", ".3"), (".6", ".5"), ("-.1", "1.1"),
                 ("NaN", "1"), ("Infinity", "0")]
        for x, y in cases:
            with self.subTest(ratios=(x, y)):
                invalid = rule("bad", "DEPARTMENT", "ACTUAL", {"P01": (("A", x), ("B", y))})
                with self.assertRaises(ValueError):
                    aggregate({"P01": 100}, invalid)
        duplicate = rule("bad-dup", "DEPARTMENT", "ACTUAL", {"P01": (("A", ".5"), ("A", ".5"))})
        with self.assertRaisesRegex(ValueError, "DUPLICATE_TARGET"):
            aggregate({"P01": 100}, duplicate)

    def test_06_rounding_conserves_cents_and_is_stable_under_order_change(self):
        targets = (("A", Decimal(".5")), ("B", Decimal(".5")))
        self.assertEqual(allocate_cents(1, targets), {"A": 1, "B": 0})
        self.assertEqual(allocate_cents(1, targets[::-1]), {"A": 1, "B": 0})
        for cents in (0, 1, 2, 7, 101, 999_999_999_999):
            with self.subTest(cents=cents):
                self.assertEqual(sum(allocate_cents(cents, targets).values()), cents)

    def test_07_negative_reversal_cancels_each_target_exactly(self):
        targets = (("A", Decimal(".333333")), ("B", Decimal(".333333")),
                   ("C", Decimal(".333334")))
        for cents in (1, 2, 7, 101, 999_999):
            with self.subTest(cents=cents):
                forward, reversal = allocate_cents(cents, targets), allocate_cents(-cents, targets)
                self.assertEqual(sum(reversal.values()), -cents)
                self.assertTrue(all(forward[t] + reversal[t] == 0 for t in forward))

    def test_08_rounding_grain_cannot_silently_change_between_summary_and_detail(self):
        tiny = rule("tiny", "DEPARTMENT", "ACTUAL", {
            "P01": (("A", ".5"), ("B", ".5")), "P02": (("A", ".5"), ("B", ".5"))})
        detail_first = aggregate({"P01": 1, "P02": 1}, tiny)
        total_first = allocate_cents(2, rates_for(tiny, "P01"))
        self.assertEqual(detail_first, {"A": 2, "B": 0})
        self.assertEqual(total_first, {"A": 1, "B": 1})
        self.assertNotEqual(detail_first, total_first)

    def test_09_different_budget_actual_rules_require_explicit_comparison_policy(self):
        b2 = rule("budget-dept-v2", "DEPARTMENT", "BUDGET", {
            "P01": (("D_A", ".5"), ("D_B", ".5")), "P02": DEPARTMENT["P02"]})
        with self.assertRaisesRegex(ValueError, "COMPARISON_POLICY_REQUIRED"):
            compare(BUDGET, ACTUAL, b2, A1, {(B1.rule_id, A1.rule_id)})
        # Lab policy explicitly permits this pair; different rules are not
        # inherently forbidden, but the comparison must be approved and labeled.
        budget, actual = compare(BUDGET, ACTUAL, b2, A1, {(b2.rule_id, A1.rule_id)})
        self.assertEqual(budget["D_A"], 45_000_000)
        self.assertEqual(actual["D_A"], 56_000_000)
        self.assertEqual(actual["D_A"] - budget["D_A"], 11_000_000)
        with self.assertRaisesRegex(ValueError, "MEASURE_RULE_MISMATCH"):
            compare(BUDGET, ACTUAL, A1, B1, {(A1.rule_id, B1.rule_id)})

    def test_10_rule_publication_is_immutable_and_existing_plan_remains_replayable(self):
        registry = {}
        publish(registry, A1)
        old = aggregate(ACTUAL, registry[A1.rule_id])
        a2 = rule("actual-dept-v2", "DEPARTMENT", "ACTUAL", {
            "P01": (("D_A", ".5"), ("D_B", ".5")), "P02": DEPARTMENT["P02"]})
        publish(registry, a2)
        self.assertEqual(aggregate(ACTUAL, registry[A1.rule_id]), old)
        self.assertEqual(aggregate(ACTUAL, registry[a2.rule_id])["D_A"], 48_300_000)
        with self.assertRaisesRegex(ValueError, "IMMUTABLE_RULE_ID_CONFLICT"):
            publish(registry, replace(a2, rule_id=A1.rule_id))

    def test_11_effective_plan_identity_changes_for_every_material_version(self):
        base = {"data_release": "r1", "axis": "DEPARTMENT", "budget_rule": B1.rule_id,
                "budget_rule_hash": rule_fingerprint(B1), "actual_rule": A1.rule_id,
                "actual_rule_hash": rule_fingerprint(A1), "comparison_policy": "pair-v1",
                "metric_version": "adjusted-budget-accrual-v1", "mapping_version": "org-v1",
                "rounding_policy": "project-measure-cents-lrm-v1", "query": "projects:P01,P02;2026Q2",
                "scope_fingerprint": "alice-visible-targets-v1"}
        old_id = digest(base)
        # Useful as a key-contract regression, not proof of cache authorization.
        for field in base:
            with self.subTest(field=field):
                self.assertNotEqual(old_id, digest({**base, field: base[field] + "-changed"}))
        self.assertEqual(old_id, digest(dict(reversed(list(base.items())))))

    def test_12_permission_filter_does_not_renormalize_authorized_share(self):
        # Internal trusted calculation sees the full approved rule. A viewer
        # allowed only D_A receives its 60%, never 100% of the original cost.
        whole = aggregate({"P01": 77_000_000}, A1)
        visible = {target: cents for target, cents in whole.items() if target == "D_A"}
        self.assertEqual(visible, {"D_A": 46_200_000})
        self.assertNotEqual(sum(visible.values()), 77_000_000)


if __name__ == "__main__":
    print("Synthetic allocation lab — no Java, PostgreSQL, LangGraph or model execution.", flush=True)
    print("Executed at:", datetime.now(timezone.utc).isoformat(), flush=True)
    print("Python:", platform.python_version(), "SQLite:", sqlite3.sqlite_version, flush=True)
    print("Platform:", platform.platform(), flush=True)
    print("Rules: full allocation; independent axes; per-project/measure cent rounding.", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AllocationExperiments)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
