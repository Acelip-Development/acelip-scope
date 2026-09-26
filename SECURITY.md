# Security

**PUBLIC RELEASE BLOCKER: a private security-reporting contact has not been
selected.** There is currently no published security email or approved advisory
URL. Do not put vulnerability details, secrets or raw diagnostic evidence in a
public issue. A private reporting route must be established before release;
contact the project owner through an existing trusted channel in the meantime.

Only the current Linux development branch is under active inspection. There is
no stable release support promise yet, and Windows/macOS diagnostics are not
implemented. No formal penetration test or comprehensive CVE clearance is claimed.

LUCY performs read-only diagnostics. It never escalates privileges, repairs the
host, starts services or installs packages. Flatpak permissions remain minimal;
AppImage has ordinary native process access. A report is saved only through an
explicit user action. No telemetry or automatic report upload is implemented.

AI features prepare a reviewed handoff, require fresh consent and never execute
an AI command or send a prompt. External previews are sanitized; users must still
review free-form logs. Secret filtering is a best-effort defense, not a guarantee
that a report is anonymous or safe to publish. Detailed local evidence can reveal
host identifiers. Do not send account tokens or private keys with a report.

The CI security workflow checks repository leak patterns, syntax and metadata;
it does not upload findings to a third-party scanning service. CI uses read-only
repository permissions, pinned actions, no persisted checkout credentials and
no pull_request_target execution. Runtime libraries are supplied by the pinned
GNOME runtime; review its upstream security advisories before a public release.
The inventory is not equivalent to an exhaustive vulnerability scan.
