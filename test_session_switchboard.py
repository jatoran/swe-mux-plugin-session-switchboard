import io
import sys
import unittest
from unittest.mock import patch

import session_switchboard as switchboard


class SwitchboardTests(unittest.TestCase):
    def test_output_is_utf8_even_when_windows_selected_a_legacy_pipe_encoding(self):
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1252")
        with patch.object(sys, "stdout", stream), patch.object(sys, "stderr", stream):
            switchboard.configure_output()
            print("┌─┐")
            stream.flush()
            self.assertEqual(raw.getvalue().decode("utf-8").strip(), "┌─┐")

    def setUp(self) -> None:
        self.rows = [
            {"id": "s1", "name": "alpha", "project_id": "p1", "state": "idle"},
            {"id": "s2", "name": "beta", "project_id": "p1", "state": "awaiting"},
            {"id": "s3", "name": "other", "project_id": "p2", "state": "working"},
            {
                "id": "plugin", "name": "switchboard", "project_id": "p1",
                "state": "running", "plugin_id": "switchboard",
            },
            {"id": "ended", "name": "ended", "project_id": "p1", "state": "exited"},
        ]

    def test_rows_are_project_scoped_and_attention_first(self) -> None:
        selected = switchboard.project_sessions(self.rows, "p1")
        self.assertEqual([item["id"] for item in selected], ["s2", "s1"])

    def test_send_targets_only_the_selected_row(self) -> None:
        calls = []
        switchboard.apply_command(
            "send 2 review this", self.rows[:2], lambda *a, **k: calls.append((a, k))
        )
        self.assertEqual(
            calls, [(("terminal.write",), {"session_id": "s2", "data": "review this\r"})]
        )

    def test_stop_requires_literal_confirmation(self) -> None:
        calls = []
        _, message = switchboard.apply_command(
            "stop 1", self.rows, lambda *a, **k: calls.append((a, k))
        )
        self.assertIn("YES", message)
        self.assertEqual(calls, [])
        switchboard.apply_command("stop 1 YES", self.rows, lambda *a, **k: calls.append((a, k)))
        self.assertEqual(calls[0][0], ("session.stop",))

    def test_render_is_a_compact_project_tool_not_a_plain_report(self) -> None:
        rendered = switchboard.render("Alpha", self.rows[:2], "refreshed", color=False)
        self.assertIn("SESSION SWITCHBOARD", rendered)
        self.assertIn("Alpha · 2 regular sessions", rendered)
        self.assertIn("r refresh", rendered)
        self.assertIn("refreshed", rendered)


if __name__ == "__main__":
    unittest.main()
