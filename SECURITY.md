# Security

Report vulnerabilities privately through the security advisory form for this repository.
Do not include terminal contents, credentials, Project paths, session identifiers, or plugin tokens in a public issue.

Session Switchboard runs as the current operating-system user and has explicit terminal-write and session-control authority.
Its declared swe-mux permissions limit callback operations but do not sandbox filesystem, process, credential, or network access.
