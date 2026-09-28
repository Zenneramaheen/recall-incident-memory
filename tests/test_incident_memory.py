import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from incident_memory import investigate, load_incident, retain


class IncidentMemoryTests(unittest.TestCase):
    def test_current_evidence_can_be_analyzed_without_past_memory(self):
        client = Mock()
        client.recall.return_value = SimpleNamespace(results=[])
        client.reflect.return_value = SimpleNamespace(text="Current logs suggest a connection leak; no prior memories.", based_on=None)
        result = investigate(client, "demo", "pool full", "checkout", "demo", analyze_current=True)
        client.reflect.assert_called_once()
        self.assertEqual(result["evidence"], [])
        self.assertIn("no prior memories", result["recommendation"])

    def test_empty_memory_does_not_invent_a_past_cause(self):
        client = Mock()
        client.recall.return_value = SimpleNamespace(results=[])
        result = investigate(client, "demo", "timeouts", "checkout", "demo")
        self.assertEqual(result["evidence"], [])
        self.assertIn("unconfirmed", result["recommendation"])
        client.reflect.assert_not_called()

    def test_both_searches_scope_service_and_environment_and_keep_sources(self):
        client = Mock()
        fact = SimpleNamespace(id="fact-1", text="Synthetic incident: restart failed.")
        client.recall.return_value = SimpleNamespace(results=[fact])
        client.reflect.return_value = SimpleNamespace(text="Check pool usage.", based_on=SimpleNamespace(memories=[fact]))
        result = investigate(client, "demo", "timeouts", "checkout", "demo")
        for call in (client.recall.call_args, client.reflect.call_args):
            self.assertEqual(call.kwargs["tags"], ["service:checkout", "environment:demo"])
            self.assertEqual(call.kwargs["tags_match"], "all_strict")
        self.assertEqual(result["reflection_sources"][0]["id"], "fact-1")

    def test_retention_preserves_failed_attempts_and_synthetic_label(self):
        incident = load_incident(Path(__file__).resolve().parents[1] / "examples/resolved-incident.json")
        client = Mock()
        retain(client, "demo", incident)
        args = client.retain.call_args.kwargs
        self.assertIn(incident["failed_attempts"][0], args["content"])
        self.assertIn('"synthetic": true', args["content"])
        self.assertFalse(args["retain_async"])


if __name__ == "__main__":
    unittest.main()
