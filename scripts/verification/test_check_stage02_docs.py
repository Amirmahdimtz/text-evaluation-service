"""Regression tests for historical Stage 02 gate and authorized Stage 03 transition."""

import unittest

from check_stage02_docs import stage_tracker_preserved


class StageTrackerTests(unittest.TestCase):
    @staticmethod
    def manifest(stage02="BLOCKED", stage03="IN_PROGRESS", approval="CONFIRMED"):
        rows = (
            f"| 02 | Repository & Detailed Architecture | `{stage02}` | remains open |\n"
            f"| 03 | Local Model Benchmark | `{stage03}` | ongoing |\n"
        )
        if approval is not None:
            rows += (
                "| `D-016` | Conditional Stage 03 entry | "
                f"`{approval}` (explicit instruction) | no waiver |\n"
            )
        return rows

    def test_historical_not_started_without_exception(self):
        self.assertTrue(stage_tracker_preserved(
            self.manifest(stage03="NOT_STARTED", approval=None)
        ))

    def test_authorized_in_progress(self):
        self.assertTrue(stage_tracker_preserved(self.manifest()))

    def test_authorized_blocked(self):
        self.assertTrue(stage_tracker_preserved(self.manifest(stage03="BLOCKED")))

    def test_authorized_done_does_not_clear_stage02(self):
        self.assertTrue(stage_tracker_preserved(self.manifest(stage03="DONE")))

    def test_stage02_not_blocked_is_rejected(self):
        self.assertFalse(stage_tracker_preserved(self.manifest(stage02="DONE")))

    def test_stage03_progress_without_approval_is_rejected(self):
        self.assertFalse(stage_tracker_preserved(self.manifest(approval=None)))

    def test_proposed_exception_is_rejected(self):
        self.assertFalse(stage_tracker_preserved(self.manifest(approval="PROPOSED")))

    def test_narrative_match_not_a_tracker_row(self):
        self.assertFalse(stage_tracker_preserved(
            "History: | 02 | previous BLOCKED and | 03 | NOT_STARTED\n"
        ))

    def test_unsupported_status_is_rejected(self):
        self.assertFalse(stage_tracker_preserved(
            self.manifest(stage03="PENDING_SERVER")
        ))


if __name__ == "__main__":
    unittest.main()
