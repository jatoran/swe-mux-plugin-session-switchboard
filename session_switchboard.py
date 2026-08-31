from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from collections.abc import Callable
from typing import Any


def callback(operation: str, **payload: Any) -> Any:
    request = urllib.request.Request(
        os.environ["SWEMUX_API_URL"],
        data=json.dumps({"operation": operation, **payload}).encode(),
        headers={
            "Authorization": f"Bearer {os.environ['SWEMUX_PLUGIN_TOKEN']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def context() -> dict[str, Any]:
    return json.loads(os.environ.get("SWEMUX_PLUGIN_CONTEXT_JSON", "{}"))


def project_sessions(sessions: list[dict[str, Any]], project_id: str) -> list[dict[str, Any]]:
    priority = {"awaiting": 0, "working": 1, "running": 2, "idle": 3, "starting": 4}
    selected = [item for item in sessions if str(item.get("project_id")) == project_id]
    return sorted(
        selected,
        key=lambda item: (
            priority.get(str(item.get("state")), 9),
            str(item.get("name", "")).lower(),
        ),
    )


def render(rows: list[dict[str, Any]]) -> None:
    print("\033[2J\033[H", end="")
    print("SESSION SWITCHBOARD")
    print("=" * 94)
    print(f"{'#':>2}  {'STATE':<10} {'CONTEXT':>7}  {'BRANCH':<22} NAME")
    print("-" * 94)
    for index, item in enumerate(rows, 1):
        branch = str((item.get("git") or {}).get("branch") or "-")[:22]
        context_pct = float(item.get("context_pct") or 0)
        shown_pct = context_pct * 100 if context_pct <= 1 else context_pct
        print(
            f"{index:>2}  {str(item.get('state') or '?'):<10} {shown_pct:>6.1f}%  "
            f"{branch:<22} {str(item.get('name') or item.get('id'))}"
        )
    if not rows:
        print("No sessions belong to this Project.")
    print("\nCommands: refresh | send <number> <message> | stop <number> YES | quit")


def select(rows: list[dict[str, Any]], raw: str) -> dict[str, Any] | None:
    try:
        index = int(raw) - 1
    except ValueError:
        return None
    return rows[index] if 0 <= index < len(rows) else None


def apply_command(
    command: str,
    rows: list[dict[str, Any]],
    invoke: Callable[..., Any],
) -> tuple[bool, str]:
    value = command.strip()
    if value in {"q", "quit", "exit"}:
        return False, ""
    if value in {"", "r", "refresh"}:
        return True, "refreshed"
    if value.startswith("send "):
        parts = value.split(maxsplit=2)
        if len(parts) != 3:
            return True, "send expects a session number and message"
        target = select(rows, parts[1])
        if target is None:
            return True, "unknown session number"
        invoke("terminal.write", session_id=target["id"], data=parts[2] + "\r")
        return True, f"sent to {target.get('name') or target['id']}"
    if value.startswith("stop "):
        parts = value.split()
        if len(parts) != 3 or parts[2] != "YES":
            return True, "stop requires: stop <number> YES"
        target = select(rows, parts[1])
        if target is None:
            return True, "unknown session number"
        invoke("session.stop", session_id=target["id"])
        return True, f"stopped {target.get('name') or target['id']}"
    return True, "unknown command"


def current_rows() -> list[dict[str, Any]]:
    project_id = str(context().get("project_id") or "")
    if not project_id:
        raise RuntimeError("Project context is required")
    return project_sessions(callback("sessions.list"), project_id)


def run(input_fn: Callable[[str], str] = input) -> int:
    status = ""
    while True:
        try:
            rows = current_rows()
        except Exception as exc:
            print(f"Unable to load sessions: {exc}", file=sys.stderr)
            return 2
        render(rows)
        if status:
            print(f"\n{status}")
        try:
            command = input_fn("\nswitchboard> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        try:
            keep_running, status = apply_command(command, rows, callback)
        except Exception as exc:
            keep_running, status = True, f"operation failed: {exc}"
        if not keep_running:
            return 0


def print_list() -> int:
    rows = current_rows()
    for index, item in enumerate(rows, 1):
        print(f"{index}. {item.get('state', '?'):<10} {item.get('name') or item.get('id')}")
    print(f"{len(rows)} Project session(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    return print_list() if args.list else run()


if __name__ == "__main__":
    raise SystemExit(main())
