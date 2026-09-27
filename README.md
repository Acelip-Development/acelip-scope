# Acelip Scope

**System diagnostics, made clear.**

A Linux-first system diagnostics and health-inspection application from
**Acelip Development**. The unified health dashboard combines live telemetry,
findings, evidence and optional AI explanations in a read-only GTK interface.

**Acelip Scope 1.0.0-rc1 is publicly available.** Licensed under Apache-2.0.
The [repository](https://github.com/Acelip-Development/acelip-scope) is public.

## Public RC1 release

Download from the [1.0.0-rc1 release page](https://github.com/Acelip-Development/acelip-scope/releases/tag/v1.0.0-rc1),
published September 26, 2026.

| Distribution | RC1 status |
|---|---|
| Source | Available |
| Flatpak x86_64 | Available |
| AppImage | Withheld |

**AppImage is not distributed with 1.0.0-rc1.** Third-party redistribution and
advisory review remains incomplete. See the
[publication record](docs/RC1-PUBLICATION.md) and [release checklist](docs/RELEASE-CHECKLIST.md).

## RC2 development

This branch prepares **1.0.0-rc2-dev** with a compact Overview and dedicated
**Findings** and **Reports** views. Subsystem details and optional screen-sharing
validation are in Findings; exports and AI handoff are in Reports. Scans,
observation timestamps, live telemetry and themes persist across navigation.
Run development builds from source. The RC1 downloads above remain unchanged;
no RC2 package is published. See [RC2 UI validation](docs/RC2-UI-VALIDATION.md).

## What it does

- CPU/GPU/memory/storage/network visibility and lightweight live graphs.
- CPU, disk and cooling telemetry; optional NVIDIA and SMART observations.
- Linux service, journal and package inspection with explicit coverage limits.
- Audio/PipeWire/WirePlumber, Discord and screen-sharing prerequisite checks.
- Reviewed Markdown/JSON exports, secret filtering and a sanitized privacy mode.
- Optional AI explanation through a reviewed copy/save command handoff. Acelip Scope
  does not execute AI commands or transmit prompts.
- Thirteen original themes, including a System theme that follows GTK appearance.

Unavailable tools, permissions and sandboxes are coverage limits, not proof of a
healthy or broken system. No repair, configuration changes or elevation occurs.

## Platform support

| Platform | Current status |
|---|---|
| Linux | Implemented diagnostics backend; actual coverage depends on tools/session/permissions |
| Windows | Architecture prepared; diagnostics backend placeholder returns UNSUPPORTED |
| macOS | Architecture prepared; diagnostics backend placeholder returns UNSUPPORTED |

This release targets Linux. The [Linux compatibility
matrix](docs/LINUX-COMPATIBILITY.md) separates real Ubuntu/GNOME host validation,
isolated Linux userspaces, synthetic distro/desktop fixtures and untested
independent desktops. Container GUI output is not desktop/service certification.
Rename acceptance is recorded in [NAMESPACE-VALIDATION.md](docs/NAMESPACE-VALIDATION.md).
The [v1.6 validation](docs/V1.6-VALIDATION.md) is historical engineering evidence.

## Flatpak for RC1

Download `acelip-scope-1.0.0-rc1-x86_64.flatpak` and `SHA256SUMS` from the release
page above into the same directory. Verify the checksum before installation:

```sh
sha256sum --check SHA256SUMS
flatpak install --user ./acelip-scope-1.0.0-rc1-x86_64.flatpak
flatpak run io.github.acelip_development.acelip-scope
```

Expected Flatpak SHA-256:

```text
672c3247f4c3c61acb5eedf1a86efaea0f8791716d83c264ce1c7748063eef6a
```

Continue only if checksum verification reports `OK`. Developer build instructions
are in [PACKAGING.md](docs/PACKAGING.md).

Flatpak needs its GNOME runtime; offline installation requires that runtime to
already be present. It supplies a consistent sandboxed GUI, with reduced host
diagnostic visibility. Acelip Scope does not ask for blanket filesystem/device access.
Restricted checks are PARTIAL/UNAVAILABLE, with an explanation.

## Run from source

Use a checkout of [Acelip-Development/acelip-scope](https://github.com/Acelip-Development/acelip-scope).
The public HTTPS checkout requires no repository-specific access:

```sh
git clone https://github.com/Acelip-Development/acelip-scope.git
cd acelip-scope
./scripts/launch.sh
./scripts/launch.sh --scan 'Quick Scan'
./scripts/launch.sh --scan 'Full Scan' --json
./scripts/launch.sh --build-info
```

Python 3.11+ is required. GUI use additionally needs PyGObject, Pycairo, GTK 4.10+
and libadwaita 1.5+ from the distribution. CLI scans do not need GTK or a display.
The source launcher uses the distribution Python; a virtual environment/pip
install is unnecessary. The app never installs dependencies. Optional tools and
build requirements are listed in [DEPENDENCIES.md](docs/DEPENDENCIES.md).

A clean first launch uses System theme, immediately offers the dashboard and
needs no internet, AI account or external project-memory service. Network checks
can be unavailable while other diagnostics continue. The optional
`scripts/install-user.py` installs a user launcher/desktop entry only when
explicitly run; it does not install packages or alter system settings.

## Privacy and control

There is no telemetry, automatic report upload, automatic AI transmission,
automatic repair or privilege escalation. Scans read local observations.
Network scans retain limited, documented traffic: one ICMP echo to the detected
gateway and `1.1.1.1`; relevant AI-stack checks read the local Ollama loopback API.
Launching the app does not depend on those endpoints being reachable.

Reports are prepared as copies for review. Both export modes remove recognized
secrets. Sanitized mode additionally masks user/home/host identities, private
and arbitrary public IPs, MACs, local shares, serials and similar identifiers.
The documented public connectivity probe address is retained for context.
Filtering is best effort: review the preview before sharing, including free-form
logs. Raw observations and detailed local reports can still contain identifiers.
CLI scan output and the local dashboard report are raw observations; use the
reviewed export flow for sharing. No diagnostic report is saved without a
destination and explicit save action.

AI handoff requires fresh consent for the exact preview. External previews are
sanitized; local Ollama handoff can also be sanitized. Acelip Scope does not perform
inference, so it cannot certify an external AI client's availability or policy.
Keep credentials out of reports and issue attachments. See [SECURITY.md](SECURITY.md).

## Known limits

SMART may be permission-restricted. Missing optional tools and non-systemd
sessions limit coverage. Flatpak hides host services, package databases, raw
devices and network interfaces. Audio detection does not prove playback;
ScreenCast properties do not prove frame capture. The validation report records
actual manual chooser/session results separately from end-to-end sharing.
Windows/macOS diagnostics and broad desktop certification remain outside RC1.
AppImage redistribution/advisory clearance remains blocked; that format is
excluded from the approved source + Flatpak distribution.

Packaged preferences use app-specific XDG storage; a source checkout retains
local `var/` preferences. Only preferences and bounded warning logs persist
automatically; scan history stays in memory. About/`--build-info` includes version,
source commit, package, architecture, reproducible build epoch and backend.

## Development and support

[CONTRIBUTING.md](CONTRIBUTING.md) covers setup, tests, privacy and architectural
boundaries. [SUPPORT.md](SUPPORT.md) explains what sanitized information is useful
for reports through [GitHub Issues](https://github.com/Acelip-Development/acelip-scope/issues).
Normal support uses public Issues. Report security vulnerabilities through
[GitHub private vulnerability reporting](https://github.com/Acelip-Development/acelip-scope/security/advisories/new),
not public Issues.
[CHANGELOG.md](CHANGELOG.md) records development milestones.
[LICENSING-NOTES.md](docs/LICENSING-NOTES.md) records third-party notices and
unresolved distribution obligations. GitHub workflows build/test development
artifacts only; they do not publish releases.

Acelip Scope was developed under the working name LUCY Diagnose through the
1.6.0-dev development cycle. The final application ID is
`io.github.acelip_development.acelip-scope`; developer ID is
`io.github.acelip_development`. The live
[repository and homepage](https://github.com/Acelip-Development/acelip-scope)
and [support/issues tracker](https://github.com/Acelip-Development/acelip-scope/issues)
are public. Private vulnerability reporting is enabled. See
[RC1 publication record](docs/RC1-PUBLICATION.md);
[repository metadata validation](docs/REPOSITORY-METADATA.md) records the earlier state, and
[namespace preparation](docs/NAMESPACE-VALIDATION.md) records the earlier baseline.

Before launching the final-ID Flatpak over a previous development installation,
close both apps and run the explicit host-side preference migration described in
[PREFERENCE-MIGRATION.md](docs/PREFERENCE-MIGRATION.md). The new sandbox cannot
silently read another app ID's private settings. Native preference paths remain stable.

## License

Acelip Scope is licensed under the Apache License 2.0.
See [LICENSE](LICENSE) for the standard license text and [NOTICE](NOTICE) for
attributions. Copyright 2026 Acelip Development.

Third-party dependencies and assets retain their respective licenses. The
[licensing notes](docs/LICENSING-NOTES.md) distinguish the application grant
from unresolved dependency redistribution requirements. See the
[publication clearance report](docs/PUBLICATION-CLEARANCE.md) for the current
source, Flatpak and AppImage decisions.
