# Security

**Private vulnerability reporting: UNRESOLVED / private-repository-limited.**
The [Acelip Scope repository](https://github.com/Acelip-Development/acelip-scope)
now exists and is private. A working repository or Issues URL does not establish
a configured confidential reporting route. GitHub private vulnerability reporting
has not been configured or verified for this repository; no security email
address is supplied or invented. Central metadata retains `security_contact: null`
and `security_reporting_configured: false`.

Do not put vulnerability details, secrets or raw diagnostic evidence in ordinary
Issues, including private-repository Issues: they may be visible to other
collaborators. Use an existing trusted private channel to the project owner until
a specific private reporting route is verified. Repository visibility and
security settings were not changed by this metadata update.

Only the current Linux development branch is under active inspection. There is
no stable release support promise yet, and Windows/macOS diagnostics are not
implemented. No formal penetration test or comprehensive CVE clearance is claimed.

Acelip Scope performs read-only diagnostics. It never escalates privileges, repairs the
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
