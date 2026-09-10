"""Behavior checks for interruption, corruption, and date isolation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("resume_job.py")


class ResumeChecks(unittest.TestCase):
    def invoke(self, root, date="2026-09-10", *extra):
        return subprocess.run([sys.executable, str(SCRIPT), "--date", date,
                               "--root", str(root), *extra],
                              text=True, capture_output=True)

    def test_interruption_and_repeat(self):
        with tempfile.TemporaryDirectory() as root:
            first = self.invoke(root, "2026-09-10", "--stop-after-draft")
            self.assertEqual(first.returncode, 75)
            folder = Path(root) / "2026-09-10"
            before = (folder / "draft.md").stat().st_mtime_ns
            self.assertFalse((folder / "receipt.json").exists())
            self.assertEqual(self.invoke(root).returncode, 0)
            self.assertEqual(self.invoke(root).returncode, 0)
            self.assertEqual(before, (folder / "draft.md").stat().st_mtime_ns)
            receipt = json.loads((folder / "receipt.json").read_text())
            self.assertEqual(receipt["issueDate"], "2026-09-10")
            self.assertEqual(len(receipt["artifactHashes"]), 2)

    def test_completed_material_is_rechecked(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(self.invoke(root).returncode, 0)
            draft = Path(root) / "2026-09-10" / "draft.md"
            draft.write_text("# 演示任务 2026-09-10\n被修改的内容\n")
            result = self.invoke(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("内容已改变", result.stderr)
            self.assertFalse(draft.with_name("receipt.json").exists())
            state = json.loads(draft.with_name("state.json").read_text())
            self.assertEqual(state["stage"], "drafted")

    def test_yesterday_cannot_complete_today(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(self.invoke(root, "2026-09-09").returncode, 0)
            result = self.invoke(root, "2026-09-10", "--stop-after-draft")
            self.assertEqual(result.returncode, 75)
            self.assertFalse((Path(root) / "2026-09-10" / "receipt.json").exists())
            state_file = Path(root) / "2026-09-10" / "state.json"
            state = json.loads(state_file.read_text())
            state["issueDate"] = "2026-09-09"
            state_file.write_text(json.dumps(state))
            self.assertEqual(self.invoke(root).returncode, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
