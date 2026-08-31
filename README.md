# Session Switchboard

Session Switchboard is an official swe-mux plugin that contributes a compact right-hand Project tool showing ordinary sessions, attention state, context use, branch, and name.
Plugin utility panes and ended sessions are excluded, so the switchboard never lists itself.

`s <number> <message>` writes and submits an explicit message to the selected terminal.
`x <number> YES` deliberately requires confirmation before stopping a session.
The plugin never targets a session outside the selected Project's displayed list.

## Requirements

- swe-mux 0.2.0 or newer.
- Python 3.10 or newer available as `python`.
- Windows, Linux, or macOS.

## Install

```text
swemux plugin install jatoran/swe-mux-plugin-session-switchboard --ref v0.2.0
swemux plugin approve swemux.official.session-switchboard
```

Open **Session switchboard** from a Project's Run menu or the command palette.

## Contributions

- **List Project sessions** returns a compact point-in-time list for the selected Project.
- **Session switchboard** opens an interactive split with refresh, send, stop, and close controls.

## Authority and destructive operations

The plugin requests `projects.read`, `sessions.read`, `terminal.write`, `sessions.control`, and `plugins.self` callback permissions.
It can submit text to a displayed session only after an explicit `s` command.
It can stop a displayed session only after the command contains the literal `YES` confirmation.
Stopping a session terminates that session's process and is the plugin's only destructive operation.
The plugin does not mutate Git, write Project files, or persist plugin state.

Plugins run as the current operating-system user.
swe-mux callback permissions are an API boundary, not a filesystem or process sandbox.

## Development

```text
python -m unittest -v
swemux plugin validate .
swemux plugin link .
swemux plugin approve swemux.official.session-switchboard
```

Changing any source byte invalidates the prior approval.
Disablement removes the contributed surfaces, and uninstalling a linked copy never removes this repository.

## License

MIT.
See [LICENSE](LICENSE).

