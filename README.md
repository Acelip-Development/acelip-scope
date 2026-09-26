# LUCY Diagnose

A native GTK4/libadwaita diagnostics app for Ubuntu GNOME. V1 observes system
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
| `systemd`, `dpkg`, `apt`, `procps`, `util-linux` | Services, journal, packages, process and disk queries | Standard Ubuntu tools |
| `lm-sensors` | CPU / disk sensor readings | Optional |
| Existing `nvidia-smi` | NVIDIA telemetry and driver CUDA compatibility | Optional |
| `smartmontools` | ATA and NVMe SMART data through `smartctl` | Optional; permissions may restrict access |
| `iproute2`, `iputils-ping` | Interfaces, sockets, routes, reachability | Optional |
| `codex`, `claude`, `gemini`, `opencode` | Executable detection and `--version` | Optional |
| Ollama service; LM Studio / `lms` | Local AI stack detection | Optional |
| `git`, `desktop-file-utils` | Development / desktop validation | Development only |

All required packages and optional diagnostic commands were present on the
target Ubuntu 26.04 host during implementation. `nvme-cli` is installed but is
not required: `smartctl --all --json` covers NVMe health. Tests use Python's
built-in `unittest`; pytest is not required. The app never installs packages.

## Scans and coverage

- **Quick Scan:** OS, kernel, uptime, CPU model/load/temperature, RAM/swap,
  NVIDIA name/driver/temperature/utilization/VRAM/power/fan, CUDA compatibility,
  filesystem usage, failed units, dpkg audit, held packages, the last hour of
  visible journal errors, and visible recent OOM events.
- **Full Scan:** Quick Scan plus storage, networking, and AI stack. Journal
  errors cover the last 24 hours. Queries are bounded to 100 error entries and
  50 OOM matches. Kernel OOM visibility is current boot only, up to 7 days back.
- **GPU, Network, Storage, AI Stack:** focused scans for their section.

Every scan is on demand. There is no background polling, startup scan, scan
scheduler, or persistent diagnostic history. A new scan replaces the prior
snapshot; sections outside its scope explicitly say they were not scanned.
Scans use bounded background workers, and only `GLib.idle_add` callbacks update
GTK. Cancel terminates active command groups; an active local HTTP request may
take up to its 3-second socket timeout to return.

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

The Reports page displays the latest **raw local report**, with timestamps and
separate error, warning, unavailable, and information/passed groups. Copy and
Save are explicit actions. Reports can contain private data. Saved text files
use private file creation flags, and the default destination is this project.

**Analyze with Codex** and **Analyze with Claude** are visibly labeled
**External · sanitized**. `privacy.py` creates a new filtered string before any
external preview or handoff. It masks current username/home/hostname, other home
paths, non-global IPs, MAC addresses, UUIDs, machine IDs, serial/device IDs,
email addresses, common API keys, credentials, private keys, and known secret
fields. Raw snapshots are never changed. Free-form text may contain additional
identifiers: filtering is best effort and the preview must be reviewed.

**Analyze with Ollama** is labeled **Local · loopback**. It keeps raw data by
default, with a checkbox to redact it too. Choose an already installed local
model. Obvious `:cloud`/`-cloud` model names are rejected; users remain responsible
for the chosen model/backend configuration.

V1 **does not execute analysis commands or send prompts**. Each dialog starts
unconfirmed. Reviewing and acknowledging the exact preview enables copying or
saving the prompt and copying the command. Changing the model or privacy option
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
exercises each section and the external preview confirmation, then exits. A
sandbox can block the display, netlink, system bus, device nodes, or loopback
even when those resources are available to a normal desktop user. Test both
graceful restricted operation and the real desktop session; do not interpret
sandbox errors as driver failures.

Code is separated into collectors, pure parsers, bounded subprocess execution,
snapshot/report models, privacy filtering, AI preview preparation, and native
UI. Tests cover parser boundaries, healthy/failing/missing/permission-dependent
checks, output limits, timeout/cancellation, report grouping, and privacy.
