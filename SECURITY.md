# Security

**GitHub private vulnerability reporting is enabled.** Use
[Report a vulnerability](https://github.com/Acelip-Development/acelip-scope/security/advisories/new)
to send a confidential report to the maintainers. Sign in to GitHub to submit it.
The [repository](https://github.com/Acelip-Development/acelip-scope) is public;
security reports should use this private reporting route rather than public Issues.

Do not put vulnerability details, credentials or raw diagnostic evidence in public
Issues. Include affected version/package, impact, reproduction steps and only
necessary sanitized evidence in the private report. No security email address is
invented; central metadata identifies the verified GitHub reporting URL.

RC1 is publicly released as source + Flatpak. AppImage remains withheld pending its
redistribution/advisory clearance; a successful development build does not
approve that format for release. See the [publication record](docs/RC1-PUBLICATION.md).

The current Linux release candidate and development branch are under active inspection. There is
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
no pull_request_target execution. Flatpak uses a separately supplied GNOME runtime. The withheld AppImage bundles
libraries whose advisory and redistribution review remains blocked. CI success
and an inventory do not constitute exhaustive vulnerability clearance.
