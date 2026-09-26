# LUCY Diagnose

A native GTK4/libadwaita diagnostics app for Ubuntu GNOME. The V1.1 dashboard observes system
health, explains unavailable checks, and prepares optional AI handoffs. It never
repairs the machine, changes GNOME settings, or requests elevated privileges.

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

CLI diagnostics do not need a graphical session:

```sh
./scripts/launch.sh --scan 'Quick Scan'
./scripts/launch.sh --scan 'Full Scan' --json
./scripts/launch.sh --scan GPU
```

## Dependencies

| Packages / tool | Purpose | Required? |
| --- | --- | --- |
| `python3` (3.11+), `python3-gi` | Python and GObject bindings | Yes |
| `gir1.2-gtk-4.0` (GTK 4.10+), `gir1.2-adw-1` (libadwaita 1.5+) | Native interface | For GUI |
| `python3-cairo`, `python3-gi-cairo` | Native lightweight graphs | For GUI; already installed on target host |
| `systemd`, `dpkg`, `apt`, `procps`, `util-linux` | Services, journal, packages, process and disk queries | Standard Ubuntu tools |
| `lm-sensors` | CPU / disk sensor readings | Optional |
| Existing `nvidia-smi` | NVIDIA telemetry and driver CUDA compatibility | Optional |
| `smartmontools` | ATA and NVMe SMART data through `smartctl` | Optional; permissions may restrict access |
| `iproute2`, `iputils-ping` | Interfaces, sockets, routes, reachability | Optional |
| `codex`, `claude`, `gemini`, `opencode` | Executable detection and `--version` | Optional |
| Ollama service; LM Studio / `lms` | Local AI stack detection | Optional |
| `busctl` (systemd), PipeWire, WirePlumber, xdg-desktop-portal / GNOME backend | Sharing prerequisite checks | Optional |
| Discord executable or Flatpak | Sharing application detection | Optional |
| `git`, `desktop-file-utils` | Development / desktop validation | Development only |

All required packages and optional diagnostic commands were present on the
target Ubuntu 26.04 host during implementation. `nvme-cli` is installed but is
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
  filesystem usage, failed units, dpkg audit, held packages, the last hour of
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

CPU utilization (counter deltas, not load average), CPU temperature, RAM, GPU
utilization, GPU temperature, and VRAM refresh every two seconds in one worker.
CPU/memory use `/proc`, temperatures read recognized CPU hwmon sensors, and GPU
metrics use a single bounded CSV query to `nvidia-smi` (1.5-second timeout).
The GPU graphs show the first NVIDIA GPU; detailed scans list all GPUs. Missing
readings are gaps, never fabricated zeroes. The first CPU reading waits for a
second sample. Pause freezes the visible readings and resets the CPU baseline
on resume. No overlapping live jobs are queued, and unmapped windows skip samples.
The graph buffer holds at most 60 samples in RAM; no series or scan history is
saved. Journal, SMART, network probes, and AI clients are never live-polled.
Scans use bounded background workers, and only `GLib.idle_add` callbacks update
GTK. Cancel terminates active command groups; an active local HTTP request may
take up to its 3-second socket timeout to return.

Sharing checks inspect the desktop/session type, Discord executable/process or
Flatpak presence, PipeWire/WirePlumber/portal service state, and a read-only
`ScreenCast.AvailableSourceTypes` property. D-Bus auto-start and interactive
authorization are disabled. Up to 40 visible sharing-service journal errors
from the last 24 hours are collected only on Full or Sharing scans. No screen
picker, capture session, microphone, Discord account data, or recording is
accessed. Inactive on-demand services are informational; a failed service is a
finding. Prerequisite detection cannot establish that an actual Discord share
works end to end. See the [ScreenCast portal specification](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html).

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
separate error, warning, unavailable, and information/passed groups. Copy and
Save are explicit actions. Reports can contain private data. Saved text files
use private file creation flags, and the default destination is this project.

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

V1.1 **does not execute analysis commands or send prompts**. Each newly selected
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
desktop-file-validate ~/.local/share/applications/io.github.lucydiagnose.LucyDiagnose.desktop
```

The GTK smoke test requires an accessible GNOME display, runs a Quick Scan,
receives live samples, exercises inline findings and AI confirmation, verifies
one application window, then exits. A
sandbox can block the display, netlink, system bus, device nodes, or loopback
even when those resources are available to a normal desktop user. Test both
graceful restricted operation and the real desktop session; do not interpret
sandbox errors as driver failures.

Code is separated into collectors, pure parsers, bounded subprocess execution,
snapshot/report models, privacy filtering, AI preview preparation, and native
UI. Tests cover parser boundaries, healthy/failing/missing/permission-dependent
checks, output limits, timeout/cancellation, report grouping, privacy, partial
scan retention, scope replacement, CPU counter deltas, bounded graph history,
and sharing queries that do not activate services.
