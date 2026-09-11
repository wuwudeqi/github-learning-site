"""Behavior checks for incomplete or misleading evaluation comparisons."""
import unittest
from compare_runs import compare, demo


class PairedEvaluationTests(unittest.TestCase):
    def test_higher_average_does_not_hide_a_regression(self):
        before, after = demo()
        result = compare(before, list(reversed(after)))
        self.assertGreater(result["after_pass_rate"], result["before_pass_rate"])
        self.assertEqual(result["transitions"]["regressed"], ["old-tool"])
        self.assertEqual(len(result["transitions"]["improved"]), 2)
        self.assertTrue(result["needs_regression_review"])

    def test_missing_case_and_duplicate_cannot_silently_bias_average(self):
        before, after = demo()
        for broken in [after[:-1], after + [after[0]]]:
            with self.subTest(broken=broken):
                with self.assertRaises(ValueError):
                    compare(before, broken)

    def test_string_false_and_non_finite_latency_are_rejected(self):
        before, after = demo()
        for changes in [{"passed": "false"}, {"latency_ms": float("nan")},
                        {"latency_ms": -1}, {"latency_ms": True}]:
            bad = [dict(row) for row in after]
            bad[0].update(changes)
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    compare(before, bad)


if __name__ == "__main__":
    unittest.main()
