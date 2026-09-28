import unittest
from unittest.mock import patch

from web_app import process_request, run_cli


class WebAppTests(unittest.TestCase):
    def test_bank_name_cannot_be_used_as_cli_option_or_path(self):
        with patch("web_app.subprocess.run") as execute:
            for bank in ("../secret", "--bank another", "", None):
                with self.assertRaises(ValueError):
                    run_cli(bank, ["init"])
            execute.assert_not_called()

    def test_incomplete_resolution_never_reaches_hindsight(self):
        with patch("web_app.run_cli") as execute:
            with self.assertRaises(ValueError):
                process_request("/api/retain", {"bank": "demo", "incident": {"id": "test"}})
            execute.assert_not_called()

    def test_blank_alert_never_reaches_hindsight(self):
        with patch("web_app.run_cli") as execute:
            with self.assertRaises(ValueError):
                process_request("/api/investigate", {"bank": "demo", "alert": "  "})
            execute.assert_not_called()

    def test_upstream_error_does_not_disclose_process_output(self):
        from types import SimpleNamespace
        with patch("web_app.subprocess.run", return_value=SimpleNamespace(returncode=1, stderr="private-service-response")):
            with self.assertRaises(RuntimeError) as caught:
                run_cli("demo", ["init"])
            self.assertNotIn("private-service-response", str(caught.exception))
