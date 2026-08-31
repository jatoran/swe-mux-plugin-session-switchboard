import unittest

import session_switchboard as switchboard


class SwitchboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            {"id": "s1", "name": "alpha", "project_id": "p1", "state": "idle"},
            {"id": "s2", "name": "beta", "project_id": "p1", "state": "awaiting"},
            {"id": "s3", "name": "other", "project_id": "p2", "state": "working"},
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


if __name__ == "__main__":
    unittest.main()
