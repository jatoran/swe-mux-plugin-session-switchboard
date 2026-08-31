from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from collections.abc import Callable
from typing import Any

RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[36m"
RED="\033[31m"


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
    selected = [
        item for item in sessions
        if str(item.get("project_id")) == project_id
        and not item.get("plugin_id")
        and item.get("state") not in {"exited", "crashed"}
        and not item.get("inactive")
    ]
    return sorted(
        selected,
        key=lambda item: (
            priority.get(str(item.get("state")), 9),
            str(item.get("name", "")).lower(),
        ),
    )


def styled(value: str, style: str, color: bool) -> str:
    return f"{style}{value}{RESET}" if color else value


def state_badge(state: str, color: bool) -> str:
    tint = YELLOW if state == "awaiting" else GREEN if state in {"working", "running"} else BLUE
    return styled(f"● {state.upper():<8}", tint, color)


def render(
    project_name: str,
    rows: list[dict[str, Any]],
    status: str = "",
    *,
    color: bool = True,
) -> str:
    width = 88
    lines = [
        f"╭{'─' * (width - 2)}╮",
        f"│ {styled('SESSION SWITCHBOARD'.ljust(84), BOLD, color)}│",
        (
            f"│ {styled(project_name, BLUE, color)} · {len(rows)} regular "
            f"session{'s' if len(rows) != 1 else ''}"
        ),
        f"├{'─' * (width - 2)}┤",
        f"│ {'#':>2}  {'STATE':<10} {'CONTEXT':>7}  {'BRANCH':<20} NAME",
        f"├{'─' * (width - 2)}┤",
    ]
    for index, item in enumerate(rows, 1):
        branch = str((item.get("git") or {}).get("branch") or "-")[:20]
        context_pct = float(item.get("context_pct") or 0)
        shown_pct = context_pct * 100 if context_pct <= 1 else context_pct
        state = str(item.get("state") or "unknown")
        lines.append(
            f"│ {index:>2}  {state_badge(state, color)} {shown_pct:>6.1f}%  "
            f"{branch:<20} {str(item.get('name') or item.get('id'))[:30]}"
        )
    if not rows:
        lines.append(f"│ {styled('No regular sessions are running in this Project.', DIM, color)}")
    lines.extend([
        f"├{'─' * (width - 2)}┤",
        "│  r refresh   ·   s <#> <message> send   ·   x <#> YES stop   ·   q close",
        f"╰{'─' * (width - 2)}╯",
    ])
    if status:
        tint = GREEN if not status.startswith("operation failed") else RED
        lines.append(styled(f"  {status}", tint, color))
    return "\n".join(lines)


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
    if value.startswith(("send ", "s ")):
        parts = value.split(maxsplit=2)
        if len(parts) != 3:
            return True, "send expects a session number and message"
        target = select(rows, parts[1])
        if target is None:
            return True, "unknown session number"
        invoke("terminal.write", session_id=target["id"], data=parts[2] + "\r")
        return True, f"sent to {target.get('name') or target['id']}"
    if value.startswith(("stop ", "x ")):
        parts = value.split()
        if len(parts) != 3 or parts[2] != "YES":
            return True, "stop requires: stop <number> YES"
        target = select(rows, parts[1])
        if target is None:
            return True, "unknown session number"
        invoke("session.stop", session_id=target["id"])
        return True, f"stopped {target.get('name') or target['id']}"
    return True, "unknown command"


def current_view() -> tuple[str, list[dict[str, Any]]]:
    project_id = str(context().get("project_id") or "")
    if not project_id:
        raise RuntimeError("Project context is required")
    projects = callback("projects.list")
    project = next((item for item in projects if str(item.get("id")) == project_id), None)
    name = str(project.get("name") if project else project_id)
    return name, project_sessions(callback("sessions.list"), project_id)


def run(input_fn: Callable[[str], str] = input) -> int:
    status = ""
    while True:
        try:
            project_name, rows = current_view()
        except Exception as exc:
            print(f"Unable to load sessions: {exc}", file=sys.stderr)
            return 2
        print("\033[2J\033[H" + render(project_name, rows, status), flush=True)
        try:
            command = input_fn("\n  command › ")
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
    project_name, rows = current_view()
    print(project_name)
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
