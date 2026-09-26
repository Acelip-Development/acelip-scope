# LUCY Diagnose

**LUCY Diagnose 1.6.0-dev** is a Linux-first, read-only system diagnostics and
health-inspection application built with GTK4 and libadwaita. One dashboard
combines live telemetry, findings, evidence and optional AI explanation handoff.

This is an **unreleased development build**, not a published download. The name
is still LUCY Diagnose. Public distribution awaits explicit approval of the name,
publisher, application license and release action. **PUBLIC RELEASE BLOCKER:
Application license not selected.** See the [release checklist](docs/RELEASE-CHECKLIST.md).

## What it does

- CPU/GPU/memory/storage/network visibility and lightweight live graphs.
- CPU, disk and cooling telemetry; optional NVIDIA and SMART observations.
- Linux service, journal and package inspection with explicit coverage limits.
- Audio/PipeWire/WirePlumber, Discord and screen-sharing prerequisite checks.
- Reviewed Markdown/JSON exports, secret filtering and a sanitized privacy mode.
- Optional AI explanation through a reviewed copy/save command handoff. LUCY
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

This is not yet a fully cross-platform application. The [Linux compatibility
matrix](docs/LINUX-COMPATIBILITY.md) separates real Ubuntu/GNOME host validation,
isolated Linux userspaces, synthetic distro/desktop fixtures and untested
independent desktops. Container GUI output is not desktop/service certification.
Current phase results are in [V1.6-VALIDATION.md](docs/V1.6-VALIDATION.md).

## Run a locally built package

No public GitHub download URL exists yet. Obtain a trusted local build and verify
its accompanying `SHA256SUMS` before running it. Build prerequisites and exact
locked inputs are in [PACKAGING.md](docs/PACKAGING.md).

```sh
(cd dist && sha256sum --check SHA256SUMS)
chmod +x dist/lucy-diagnose-1.6.0-dev-x86_64.AppImage
./dist/lucy-diagnose-1.6.0-dev-x86_64.AppImage
```

AppImage bundles Python/GTK/libadwaita and runs as the current user. If FUSE is
unavailable, use its `--appimage-extract-and-run` option; this needs temporary
space. Host diagnostic tools remain optional. It is not a sandbox.

For a locally built Flatpak bundle, installation is an explicit user action:

```sh
flatpak install --user dist/lucy-diagnose-1.6.0-dev-x86_64.flatpak
flatpak run org.lucydiagnose.LucyDiagnose
```

Flatpak needs its GNOME runtime; offline installation requires that runtime to
already be present. It supplies a consistent sandboxed GUI, with reduced host
diagnostic visibility. LUCY does not ask for blanket filesystem/device access.
Restricted checks are PARTIAL/UNAVAILABLE, with an explanation.

## Run from source

Use a checkout obtained through the project's eventual approved repository URL.
No particular checkout directory is required:

```sh
cd LUCY-Diagnose
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
No diagnostic report is saved without a destination and explicit save action.

AI handoff requires fresh consent for the exact preview. External previews are
sanitized; local Ollama handoff can also be sanitized. LUCY does not perform
inference, so it cannot certify an external AI client's availability or policy.
Keep credentials out of reports and issue attachments. See [SECURITY.md](SECURITY.md).

## Known limits

SMART may be permission-restricted. Missing optional tools and non-systemd
sessions limit coverage. Flatpak hides host services, package databases, raw
devices and network interfaces. Audio detection does not prove playback;
ScreenCast properties do not prove frame capture. The validation report records
actual manual chooser/session results separately from end-to-end sharing.
Windows/macOS diagnostics, broad desktop certification, finalized public URLs,
security contact and application licensing remain unresolved.

Packaged preferences use app-specific XDG storage; a source checkout retains
local `var/` preferences. Only preferences and bounded warning logs persist
automatically; scan history stays in memory. About/`--build-info` includes version,
source commit, package, architecture, reproducible build epoch and backend.

## Development and support

[CONTRIBUTING.md](CONTRIBUTING.md) covers setup, tests, privacy and architectural
boundaries. [SUPPORT.md](SUPPORT.md) explains what sanitized information is useful
for reports and the current absence of public support channels.
[CHANGELOG.md](CHANGELOG.md) records development milestones.
[LICENSING-NOTES.md](docs/LICENSING-NOTES.md) records third-party notices and
unresolved distribution obligations. GitHub workflows build/test development
artifacts only; they do not publish releases.
