# Session Switchboard

Session Switchboard contributes a compact right-hand Project tool showing ordinary sessions, attention state, context use, branch, and name.
Plugin utility panes and ended sessions are excluded, so the switchboard never lists itself.

`s <number> <message>` writes and submits an explicit message to the selected terminal.
`x <number> YES` deliberately requires confirmation before stopping a session.
The plugin never targets a session outside the selected Project's displayed list.

Run tests with `python -m unittest -v`.

