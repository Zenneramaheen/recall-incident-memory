import unittest
from checkout_lab import CheckoutLab


class CheckoutLabTests(unittest.TestCase):
    def setUp(self):
        self.lab = CheckoutLab()

    def fail(self, scenario="first"):
        self.lab.inject(scenario)
        status, _ = self.lab.checkout()
        self.assertEqual(status, 503)

    def test_healthy_order_and_fault_are_real_state_changes(self):
        self.assertEqual(self.lab.checkout()[0], 200)
        self.fail()
        self.assertEqual(self.lab.orders, 1)
        self.assertEqual(self.lab.metrics()["database_connections"], 20)

    def test_restart_only_gives_one_success_then_fails_again(self):
        self.fail()
        self.lab.action("restart")
        self.assertEqual(self.lab.checkout()[0], 200)
        self.assertFalse(self.lab.verified)
        self.assertEqual(self.lab.checkout()[0], 503)
        with self.assertRaises(ValueError):
            self.lab.resolution()

    def test_learning_requires_fix_and_successful_verification(self):
        self.fail()
        self.lab.action("connection-fix")
        with self.assertRaises(ValueError):
            self.lab.resolution()
        self.assertEqual(self.lab.checkout()[0], 200)
        self.assertIn("connections leaked", self.lab.resolution()["root_cause"])
        self.assertTrue(self.lab.resolution()["synthetic"])

    def test_same_symptom_different_cause_old_fix_does_not_work(self):
        self.lab.lessons_saved = 1
        self.fail("different")
        self.assertEqual(self.lab.metrics()["database_connections"], 4)
        self.lab.action("connection-fix")
        self.assertEqual(self.lab.checkout()[0], 503)
        self.lab.action("payment-fix")
        self.assertEqual(self.lab.checkout()[0], 200)
        incident = self.lab.resolution()
        self.assertIn("Payment gateway", incident["root_cause"])
        self.assertIn("database was healthy", incident["failed_attempts"][0])

    def test_agent_evidence_does_not_include_hidden_scenario(self):
        self.fail()
        evidence = self.lab.evidence()
        self.assertNotIn('"fault"', evidence)
        self.assertNotIn('"scenario"', evidence)
        self.assertIn("20/20", evidence)

    def test_an_empty_bank_does_not_unlock_later_chapters(self):
        self.lab.bank_ready = True
        with self.assertRaises(ValueError):
            self.lab.inject("repeat")

    def test_new_round_does_not_reuse_previous_success_or_diagnosis(self):
        self.fail()
        self.lab.action("connection-fix")
        self.lab.checkout()
        self.lab.diagnosis = {"recommendation": "old"}
        self.lab.lessons_saved = 1
        old_id = self.lab.incident_id
        self.lab.inject("repeat")
        self.assertNotEqual(old_id, self.lab.incident_id)
        self.assertIsNone(self.lab.diagnosis)
        self.assertFalse(self.lab.verified)

    def test_comparison_rejects_old_connection_fix_when_visible_signals_conflict(self):
        self.lab.lessons_saved = 1
        self.fail("different")
        comparison = self.lab.comparison([{"text": "Past connection leak"}])
        self.assertEqual(comparison["status"], "conflict")
        self.assertIn("Do not repair connection cleanup", comparison["decision"])
        self.assertTrue(any("Database pool is healthy" in item for item in comparison["conflicts"]))

    def test_comparison_accepts_old_lesson_only_on_three_matching_visible_signals(self):
        self.lab.lessons_saved = 1
        self.fail("repeat")
        comparison = self.lab.comparison([{"text": "Past connection leak"}])
        self.assertEqual(comparison["status"], "applies")
        self.assertEqual(len(comparison["conflicts"]), 0)
        self.assertGreaterEqual(len(comparison["matches"]), 3)

    def test_scorecard_tracks_current_evidence_reuse_and_safe_rejection(self):
        self.fail("first")
        self.lab.diagnosis = {"comparison": self.lab.comparison([])}
        self.lab.record_investigation_result()
        self.assertTrue(self.lab.scorecard["first_investigated"])

        self.lab.lessons_saved = 1
        self.lab.inject("repeat")
        self.lab.checkout()
        self.lab.diagnosis = {"comparison": self.lab.comparison([{"text": "old"}])}
        self.lab.record_investigation_result()
        self.assertTrue(self.lab.scorecard["repeat_recalled"])

        self.lab.inject("different")
        self.lab.checkout()
        self.lab.diagnosis = {"comparison": self.lab.comparison([{"text": "old"}])}
        self.lab.record_investigation_result()
        self.assertTrue(self.lab.scorecard["different_rejected"])
