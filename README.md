# LUCY Diagnose

A native GTK4/libadwaita diagnostics app with a Linux backend, version **1.4.0-dev**. The dashboard observes system
health, explains unavailable checks, and prepares optional AI handoffs. It never
repairs the machine, changes GNOME settings, or requests elevated privileges.

Linux diagnostics have real execution evidence on Ubuntu 26.04.1 / GNOME
Wayland and isolated Debian 13, Fedora 44, Arch and openSUSE Tumbleweed
userspaces. Fedora GTK also ran on the Ubuntu compositor; this is not Fedora
Workstation or a second desktop session. Other desktops remain fixture-only. Windows and macOS have architecture placeholders that return
**UNSUPPORTED**; their diagnostics and native packaging are not implemented.
See the [compatibility matrix](docs/LINUX-COMPATIBILITY.md),
[validation evidence](docs/V1.4-VALIDATION.md), and
[platform architecture](docs/PLATFORM-ARCHITECTURE.md).

## Run

This checkout is the application. No virtual environment, pip installation, web
server, or webview is needed. Use the distribution's Python for PyGObject:

```sh
cd /path/to/LUCY-Diagnose
./scripts/launch.sh
```

After user integration is installed, search **LUCY Diagnose** in GNOME or run
`~/.local/bin/lucy-diagnose`. The launcher and desktop entry reference this
checkout; rerun the installer if you move it.

LUCY defaults to GTK's Cairo renderer for this lightweight interface, avoiding
Vulkan presentation warnings observed on the target NVIDIA desktop. This is a
process-local choice, not a GNOME or driver change. An explicit `GSK_RENDERER`
environment setting takes precedence.

CLI diagnostics do not need a graphical session:

```sh
./scripts/launch.sh --scan 'Quick Scan'
./scripts/launch.sh --scan 'Full Scan' --json
./scripts/launch.sh --scan GPU
```

## Dependencies

These package names describe the validated Ubuntu host. Other distributions use
their own package names. Missing tools remain unavailable capabilities.

| Packages / tool | Purpose | Required? |
| --- | --- | --- |
| `python3` (3.11+), `python3-gi` | Python and GObject bindings | Yes |
| `gir1.2-gtk-4.0` (GTK 4.10+), `gir1.2-adw-1` (libadwaita 1.5+) | Native interface | For GUI |
| `python3-cairo`, `python3-gi-cairo` | Native lightweight graphs | For GUI; already installed on target host |
| `systemd`, `dpkg`, `apt`, `procps`, `util-linux` | Services, journal, Debian package audits, processes and disks | Per-check capabilities; systemd is optional |
| `lm-sensors` | CPU / disk sensor readings | Optional |
| Existing `nvidia-smi` | NVIDIA telemetry and driver CUDA compatibility | Optional |
| `smartmontools` | ATA and NVMe SMART data through `smartctl` | Optional; permissions may restrict access |
| `iproute2`, `iputils-ping` | Interfaces, sockets, routes, reachability | Optional |
| `codex`, `claude`, `gemini`, `opencode` | Executable detection and `--version` | Optional |
| Ollama service; LM Studio / `lms` | Local AI stack detection | Optional |
| `busctl`, PipeWire, WirePlumber or pipewire-media-session, xdg-desktop-portal / desktop backend | Sharing prerequisites | Optional; not GNOME-specific |
| `dpkg-query`, `rpm`, `pacman`, `snap`, `flatpak`; Discord | Package/version/sandbox metadata | Optional; native manager selected by distro family |
| `git`, `desktop-file-utils` | Development / desktop validation | Development only |

Required GUI packages and Ubuntu diagnostic tools were present on the target
host. RPM, pacman and zypper are absent on the host; native package databases
were exercised in disposable distro userspaces. They are not required for Ubuntu. `nvme-cli` is installed but is
not required: `smartctl --all --json` covers NVMe health. Tests use Python's
built-in `unittest`; pytest is not required. The app never installs packages.

## Scans and coverage

The main window is one unified control center. Overall health and severity
counts, six live graphs, and all six subsystem summaries remain in the same
dashboard. System, GPU / NVIDIA, Network, Storage, AI Stack, and Discord /
Screen Sharing cards expand inline. One central findings list supports severity
and subsystem filters, timestamped evidence, source, explanation, Copy, Details,
and Explain with AI. AI previews and local reports also expand inline; only an
explicit Save opens GNOME's native file picker. No diagnostic mode opens another
application window. The layout targets 1920×1080 and reflows on smaller screens.

- **Quick Scan:** OS, kernel, uptime, CPU model/load/temperature, RAM/swap,
  NVIDIA name/driver/temperature/utilization/VRAM/power/fan, CUDA compatibility,
  filesystem usage, service failures where supported, Debian-family dpkg audit
  and held packages, semantic CPU/cooling sensors, the last hour of
  visible journal errors, and visible recent OOM events.
- **Full Scan:** Quick Scan plus storage, networking, AI stack, and sharing. Journal
  errors cover the last 24 hours. Queries are bounded to 100 error entries and
  50 OOM matches. Kernel OOM visibility is current boot only, up to 7 days back.
- **GPU, Network, Storage, AI Stack, Discord / Screen Sharing:** focused scans
  update, expand, and filter the corresponding part of the same dashboard.

One initial Full Scan fills the dashboard. Further detailed scans run only when
requested. A focused scan replaces results in its scope, removes resolved
findings, and retains other scopes with their original timestamps. The oldest
observation time is shown on each subsystem card. Unknown or inaccessible checks
never count as a clean bill of health. Overall health and severity counts reflect
scan findings, separate from the live performance graphs.

Checks carry a separate coverage value: **SUPPORTED**, **PARTIAL**,
**UNAVAILABLE**, **UNSUPPORTED**, or **UNKNOWN**. Missing commands and unimplemented
backends are coverage limits, not errors. Coverage appears in findings, inspection
details and all report formats. Incomplete coverage prevents a misleading all-clear.
Systems without a detected running systemd instance report service inspection as
unsupported. Full Scan also supports bounded RPM file verification on Fedora/RHEL
and openSUSE (`rpm -Va --noscripts --nodeps`), plus partial Arch file/mtree
verification (`pacman -Qkk`). These are read-only observations, not repair or
complete security audits. Quick Scan omits these potentially expensive checks.
Debian retains its dpkg state audit and held-package inspection.

Audio capability checks use independent service/process evidence and optional
`wpctl` or `pactl` replies; neither tool is mandatory. Dormant audio services are
not activated. A successful metadata query does not validate playback or capture.

CPU utilization (counter deltas, not load average), CPU temperature, RAM, GPU
utilization, GPU temperature, and VRAM refresh every two seconds in one worker.
CPU/memory use `/proc`, temperatures read recognized CPU hwmon sensors, and GPU
metrics use a single bounded CSV query to `nvidia-smi` (1.5-second timeout).
This access belongs to `platform/linux/`; shared graph models and UI do not read
Linux paths or invoke OS commands. Detailed scans and lightweight samples share
CPU semantics: AMD k10temp Tctl, then Tdie, then Intel package sensors, then other
recognized CPU readings. A hotter CCD, GPU, disk or coolant sensor cannot displace
an available Tctl. Cooling (coolant, pump RPM, fan RPM) appears separately in
System details. NVMe, GPU, RAM/SPD and network temperatures retain their categories.
The GPU graphs show the first NVIDIA GPU; detailed scans list all GPUs. Missing
readings are gaps, never fabricated zeroes. The first CPU reading waits for a
second sample. Pause freezes the visible readings and resets the CPU baseline
on resume. No overlapping live jobs are queued, and unmapped windows skip samples.
The graph buffer holds at most 60 samples in RAM; no series or scan history is
saved. Journal, SMART, network probes, and AI clients are never live-polled.
Scans use bounded background workers, and only `GLib.idle_add` callbacks update
GTK. Cancel terminates active command groups; an active local HTTP request may
take up to its 3-second socket timeout to return.

Sharing checks normalize GNOME, KDE Plasma, Cinnamon, XFCE, MATE, LXQt or unknown
desktop state and Wayland/X11 metadata. They inspect
PipeWire/WirePlumber/portal service states, the PipeWire socket unit and runtime
socket metadata, installed portal backend definitions, and the read-only
`ScreenCast.AvailableSourceTypes` property. D-Bus auto-start and interactive
authorization are disabled. The socket is inspected without connecting to it.
Discord source/version comes from dpkg, RPM/dnf, pacman, RPM/zypper, Snap or
Flatpak metadata, with low-confidence AppImage/manual PATH discovery;
Snap connections and Flatpak permissions are inspected when applicable. LUCY
does not execute Discord to obtain its version, inspect account data, or read
process arguments. Multiple installations and unknown/renamed installs are
reported without claiming which package owns a running process. Native
Chromium sandbox enforcement is not verified.

Relevant portal units are selected by desktop; KDE does not require GNOME
services. Acquired backend bus names identify available candidates, not proven
ScreenCast ownership. Unknown ownership remains explicit. Flatpak versions come
from structured application/version/installation columns. Query failures and
malformed output are distinct from confirmed package absence.

Up to 40 sharing-service error entries from the last 24 hours are read only on
Full or Sharing scans. Inactive on-demand services are informational; failed
services are findings. No capture session, recording, or microphone is opened.
A Wayland session with zero advertised capture sources produces a prerequisite
mismatch warning, not a claim of a proven root cause. Installed backend metadata
does not establish which backend owns the session. See the
[ScreenCast portal specification](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html).

**Test Screen Sharing** is an optional, explicitly initiated **manual checklist**.
This build cannot inspect captured frames or receiver output. The user performs
the share in their existing Discord session and records PASS, FAIL, or
INCONCLUSIVE. PASS requires an acknowledgement that the receiver saw moving
frames; it is labeled user-reported and does not validate audio. Cancelling is
INCONCLUSIVE. LUCY cannot stop a sharing session the user started in Discord;
the checklist explains that the user must stop it there. Test results remain
only in the current dashboard memory unless explicitly exported. There is no
automated capture validation or hidden capture path.

All command arguments are lists, with no shell execution. Default command
timeout is 7 seconds; SMART/CLI version queries use 10 seconds and ping 4 seconds.
Command output is limited to 256 KiB. Ollama responses are limited to 1 MiB and
use only GET `/api/version`, `/api/tags`, `/api/ps` on `127.0.0.1:11434`, ignoring
proxy environment variables and redirects. No inference, model pulls, service
starts, device self-tests, or repairs occur.

Network scans send one ICMP echo to the detected gateway and to `1.1.1.1`.
They transmit no report data. A missing reply is inconclusive because ICMP can
be blocked; DNS configuration is displayed, but DNS/HTTPS reachability is not
inferred from ping. VPN detection is a type/name heuristic, not proof that
traffic is protected by a VPN.

The NVIDIA CUDA value is the **driver's supported CUDA version**, not an
installed toolkit version. Inference readiness means driver visibility only;
no model workload is run. LM Studio executable/process detection is best effort
across PATH, common install locations, and AppImage names.

Missing commands, malformed results, timeouts, and permission failures appear
as **Unavailable**, not healthy. System journal coverage is always limited by
the current user's permissions. SMART access may be denied for all devices,
while unprivileged `sensors` still provides NVMe temperatures. The app neither
bypasses those restrictions nor asks for sudo. Disk capacity is a warning at
85% used and an error at 95%; GPU temperature warns at 85°C.

## Reports, privacy, and AI

The inline local report displays current **raw local observations**, with timestamps and
separate error, warning, unavailable, and information/passed groups. Raw Copy
is explicit and local. **Export report** supports Markdown and JSON and prepares
the exact saved contents in a background worker. Review the preview and choose
**Save reviewed report** to open GNOME's native file picker. Changing options
or refreshing scan observations invalidates the old preview. Nothing is saved
automatically. Files use private creation flags and default to this project.

Exports include app version, generation and observation timestamps, a limited
host summary, scan types performed, subsystem status, severity counts, findings,
evidence/source, sharing results, guidance, and detected tool versions. The
scan-type set is metadata, not a history of earlier results. JSON uses schema
version 1. Filenames have the form `lucy-diagnose-YYYY-MM-DD-HHMMSS.md` or `.json`.

**Sanitized** is the default export privacy level: recognized secrets and common
identifiers are removed. **Local details · secrets removed** keeps identifiers
for local troubleshooting but still strips recognized credentials. Neither
mode changes the original observations. Both are best-effort filters: review
the preview before sharing. Export settings do not weaken external AI filtering.

Warning/error Details include what happened, why it matters, evidence, a labeled
likely-cause hypothesis, and suggested next steps. Any displayed commands are
manual read-only suggestions; the app never executes them. Suggested commands
require no sudo and may show permission-dependent gaps. No fix buttons exist.

**Codex** and **Claude** choices are visibly labeled **External**, and their
preview is labeled sanitized. `privacy.py` creates a new filtered string before any
external preview or handoff. It masks current username/home/hostname, other home
paths, non-global IPs, MAC addresses, UUIDs, machine IDs, serial/device IDs,
email addresses, common API keys, credentials, private keys, and known secret
fields. Raw snapshots are never changed. Free-form text may contain additional
identifiers: filtering is best effort and the preview must be reviewed.

**Ollama** is labeled **Local**, with a loopback notice. It keeps raw data by
default, with a checkbox to redact it too. Choose an already installed local
model. Obvious `:cloud`/`-cloud` model names are rejected; users remain responsible
for the chosen model/backend configuration.

V1.4 **does not execute analysis commands or send prompts**. Each newly selected
finding or report starts unconfirmed in the inline preview. Reviewing and
acknowledging that exact preview enables copying or saving the prompt and
copying the command. Changing the provider, model, report, or privacy option
revokes that acknowledgement. To proceed, explicitly save `lucy-analysis.txt`
in this checkout, then manually run the displayed command from this folder.
Codex uses a read-only sandbox; Claude's preview disables its tools; Ollama's
command pins the endpoint to loopback. These controls apply to the proposed
commands; running a CLI is a separate action governed by its own configuration.

Nothing is automatically saved to an AI provider, diagnostic database, or scan
history. `var/lucy-diagnose.log` contains bounded operational error metadata,
not diagnostic reports or subprocess output. GTK caches stay under `var/cache`
and its settings backend is in memory. Explicit reports, logs/caches, and Python
bytecode are Git-ignored. The standard launcher disables bytecode writes.

## Appearance and preferences

Open the header preferences button for inline Appearance, Diagnostics, AI, and
About sections. **System is the first-launch default** and the fallback for a
missing, malformed, invalid, or removed theme preference. A valid saved theme,
including Arcanum, is restored without migration. Runtime changes take effect
immediately across cards, findings, graphs, and controls.

| Category | Built-in themes |
| --- | --- |
| System | **System (default)**, Dark, Light |
| Signature | Arcanum |
| Workstation | Slate, Ion, Verdant, Frostline |
| Creative | Ember, Nocturne, Cinder, Mauveglass, Midnight Circuit |

System follows the host libadwaita light/dark preference and accent where the
toolkit exposes it. It leaves native surface and accent colors intact and applies
no Arcanum styling. Arcanum remains the signature LUCY theme: near-black graphite,
deep purple surfaces, fuchsia primary accents, and violet secondary accents.
Dark and Light explicitly choose their respective appearance for this app only.
The theme catalog centralizes palettes; the GTK backend applies semantic CSS
tokens, with support for both legacy named colors and modern CSS properties.
No global GTK, GNOME, or NVIDIA settings are changed.

Graph guide thresholds are dashed and identified in tooltips; text and icons
identify high readings, missing data, and paused samples. CPU/GPU utilization
being busy is informational. Temperature and memory guides are not a hardware
diagnosis. Live graphs retain the 2-second cadence and memory-only history.

Only theme, graph-refresh preference, and default report privacy are persisted
in `var/preferences.json`, atomically with private permissions in a background
worker. No report data goes into preferences. First launch does not create a
preference file until a setting changes. About shows version and runtime build
information. AI consent controls link to the existing explicit preview flow;
there is no automatic-send setting.

## GNOME integration

Preview the exact files before installation:

```sh
python3 scripts/install-user.py --dry-run
python3 scripts/install-user.py
```

The installer writes exactly these two user files and refuses to overwrite
unmanaged existing files or symlinks:

- `~/.local/bin/lucy-diagnose`
- `~/.local/share/applications/io.github.lucydiagnose.LucyDiagnose.desktop`

The icon remains in `data/` inside the project. No GNOME settings, desktop cache,
system packages, services, drivers, firewall, network, bootloader, kernel, or
package sources are modified. Remove those two integration files manually to
unregister the app; the project and any explicitly saved reports remain intact.

## Development and verification

```sh
python3 -m unittest discover -v
python3 -m compileall -q lucy_diagnose tests scripts
./scripts/launch.sh --smoke-test
PYTHONDONTWRITEBYTECODE=1 python3 scripts/visual-check.py
desktop-file-validate ~/.local/share/applications/io.github.lucydiagnose.LucyDiagnose.desktop
```

The GTK smoke test requires an accessible GTK display, runs a Quick Scan,
receives live samples, exercises all 13 theme switches, preferences, export
preparation/invalidation, manual-test cancellation, and fresh AI confirmation,
verifies one application window, then exits. It uses separate smoke preferences.
The visual check uses labeled synthetic data with scans and polling disabled.
It renders each theme, compact/wide layouts, expanded cards, guidance, sharing,
preferences/selector, and JSON export; it checks the Save action without opening
an unattended file picker or writing a report. Artifacts stay under ignored
`var/`, including `v14-arcanum-dashboard.png`, `v14-theme-settings.png`, and
`v14-screen-sharing.png`. Neither QA path starts screen capture. A
sandbox can block the display, netlink, system bus, device nodes, or loopback
even when those resources are available to a normal desktop user. Test both
graceful restricted operation and the real desktop session; do not interpret
sandbox errors as driver failures.

Code is separated into collectors, pure parsers, bounded subprocess execution,
snapshot/report models, privacy filtering, AI preview preparation, and native
UI. Tests cover parser boundaries, healthy/failing/missing/permission-dependent
checks, output limits, timeout/cancellation, report grouping, privacy, partial
scan retention, scope replacement, CPU counter deltas, bounded graph history,
sharing queries that do not activate services, package/sandbox metadata,
theme defaults/restoration/persistence, graph states, sanitized structured
exports, manual sharing cancellation/consent, and non-executable guidance.

There are **176 tests**, preserving all 137 v1.3 cases. Two Debian sharing
fixtures now explicitly select Debian instead of depending on the test host. Portability fixtures cover distro families,
desktops, package formats, service states/no-systemd, sensor semantics and portal
gaps. Architecture guards enforce the Linux probe boundary and ensure placeholder
backends do not import Linux dependencies. Shared modules retain their existing
locations rather than undergoing a mechanical `core/` relocation.

The opt-in [validation tools](scripts/validation/README.md) record actual
CLI/GTK execution, image digests, missing-command behavior, explicit exports,
and per-feature limitations. No validation setup packages were installed on the
real host; disposable rootfs setup is documented separately.
