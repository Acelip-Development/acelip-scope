# Linux compatibility — LUCY Diagnose 1.4.0-dev

Validated 2026-09-26. Evidence: [V1.4-VALIDATION.md](V1.4-VALIDATION.md) and
[recorded execution data](validation/v1.4-execution.json). This is a scope matrix,
not a certification or aggregate score.

**REAL VALIDATION** means LUCY executed against the named environment's real
userspace, files and package database. It does not mean every feature passed.
**FIXTURE ONLY** means synthetic regression inputs, without that installed
system/session. **NOT TESTED** means no corresponding execution was performed.
Feature values: **PASS** (stated check passed), **PARTIAL** (limited evidence),
**UNAVAILABLE** (tool/access/session absent), **UNSUPPORTED** (backend not
implemented for that environment), **NOT TESTED**, or **FIXTURE ONLY**.

| Distribution | Desktop | Session | Environment type | UI | Core scans | Packages | Services | Audio | Sharing | Sensors | SMART | Exports | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ubuntu 26.04.1 | GNOME | Wayland | Real host | PASS | PASS¹ | PASS | PASS¹ | PARTIAL² | PARTIAL³ | PASS | UNAVAILABLE | PASS | REAL VALIDATION |
| Debian 13 | None | None | Rootless userspace | NOT TESTED | PARTIAL⁴ | PASS | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | PASS | REAL VALIDATION, container scope |
| Fedora 44 Container Image | None; GTK client on host GNOME compositor | Wayland client only | Rootless userspace | PASS⁵ | PARTIAL⁴ | PASS⁶ | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | PASS | REAL VALIDATION, container/client scope |
| Fedora Workstation | GNOME | Wayland | No installed workstation available | NOT TESTED | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | NOT TESTED | FIXTURE ONLY | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED as Workstation |
| Arch, image 20260920.0.596911 | None | None | Rootless userspace, packages updated for Python | NOT TESTED | PARTIAL⁴ | PASS⁶ | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | PASS | REAL VALIDATION, container scope |
| openSUSE Tumbleweed 20260923 | None | None | Rootless userspace | NOT TESTED | PARTIAL⁴ | PASS⁶ | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | PASS | REAL VALIDATION, container scope |
| Linux Mint | Cinnamon | X11 fixture | Synthetic fixtures | NOT TESTED | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | NOT TESTED | NOT TESTED | NOT TESTED | FIXTURE ONLY |
| EndeavourOS | KDE Plasma | Wayland fixture | Synthetic fixtures | NOT TESTED | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | NOT TESTED | NOT TESTED | NOT TESTED | FIXTURE ONLY |
| Garuda | KDE Plasma | Wayland fixture | Synthetic fixtures | NOT TESTED | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | NOT TESTED | NOT TESTED | NOT TESTED | FIXTURE ONLY |
| Rocky/Alma-style derivatives | Unknown | None | Synthetic ID_LIKE fixtures | NOT TESTED | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | NOT TESTED | NOT TESTED | NOT TESTED | FIXTURE ONLY |
| Unknown distro | Unknown | Unknown | Synthetic fixtures | NOT TESTED | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | FIXTURE ONLY | NOT TESTED | NOT TESTED | NOT TESTED | FIXTURE ONLY |

1. PASS describes diagnostic execution/normalization, not host health. The host
   reports one existing failed system unit and visible journal errors. They were
   not repaired. All seven scan modes complete; service aliases, running,
   stopped, failed, absent and inaccessible-user-session queries were exercised.
2. PipeWire/WirePlumber and `wpctl` metadata are available. Pulse compatibility
   service is running; `pactl` is absent. Playback, microphone and shared audio
   were not tested. Neither optional client is required for the other to work.
3. GNOME backend owns its portal bus name, but ScreenCast advertises **zero
   capture sources**. Actual screen capture/receiver output remains unverified.
4. Every scan executes without collector crashes; absent tools, unbooted systemd,
   private networking and empty hardware views correctly limit coverage. No
   container result establishes hardware, GPU, portals, PipeWire, a systemd user
   session, or a distribution kernel. All containers share the Ubuntu kernel.
5. Actual Fedora GTK/libadwaita/Python libraries rendered the app, with all scan
   controls, exports, graphs/gaps, themes and layouts exercised. The host Wayland
   compositor is the only desktop endpoint shared. This does **not** validate a
   Fedora Workstation desktop, GNOME session services, or a second desktop.
6. Installed Bash and absent Discord/nonexistent-package controls passed. RPM
   file verification and pacman metadata checking executed read-only and reported
   differences. Extracted ownership/modes and disposable setup affect these
   results; no clean package-integrity or fully configured image claim is made.

## Desktop/session evidence

| Desktop/session | Portal backend | PipeWire / manager | System theme | Evidence |
| --- | --- | --- | --- | --- |
| Ubuntu GNOME / Wayland | `gnome` owned; zero advertised capture sources | PipeWire running; WirePlumber running | Host dark preference available and followed | REAL VALIDATION |
| Fedora GTK on Ubuntu Wayland | No guest portal/session bus | No guest audio server/session manager | Host preference unavailable; default light fallback | REAL VALIDATION of client only |
| KDE Plasma / Wayland | `kde` selected from owned-name fixtures; no GNOME requirement | Independent audio fixtures | NOT TESTED in KDE | FIXTURE ONLY |
| Cinnamon / X11 | `xapp` selected from owned-name fixtures | Independent audio fixtures | NOT TESTED in Cinnamon | FIXTURE ONLY |
| XFCE / X11 | `gtk` selected from owned-name fixtures | No-systemd degradation fixture | NOT TESTED in XFCE | FIXTURE ONLY |

All 13 themes render on both tested GUI runtimes: System, Dark, Light, Arcanum,
Slate, Ion, Verdant, Frostline, Ember, Nocturne, Cinder, Mauveglass and Midnight
Circuit. System remains the first-launch default. Appearance following on two
independent desktops has **not** been established.

## Package and hardware scope

| Capability | Actual evidence | Remaining limit |
| --- | --- | --- |
| dpkg / apt | Ubuntu and Debian package metadata; dpkg audit and apt-mark queries | No package content-digest parity claimed |
| rpm / dnf | Fedora RPM database, native absence, read-only file verification | No healthy-workstation claim; no DNF mutation in application |
| pacman | Arch package database, absence and `-Qkk` | File/mtree metadata only; PARTIAL content integrity |
| rpm / zypper | Tumbleweed RPM database and verification; zypper discovered | Application queries RPM, never refreshes zypper repositories |
| Flatpak / Snap | Ubuntu tools return confirmed absence of Discord in queried scope | Installed Discord variants are FIXTURE ONLY |
| Discord native | Ubuntu deb 1.0.159 detected; absent on other tested images | RPM/pacman-installed Discord and manual/AppImage forms FIXTURE ONLY |
| CPU temperature | Ubuntu detailed and live `k10temp / Tctl` | Hardware not exposed in containers |
| GPU/storage temperatures | Ubuntu sensor readings and NVIDIA live query | Other GPU live implementations not claimed |
| Fan/pump/coolant | Separate Ubuntu cooling sensor kinds | No device reconfiguration |
| RAM/SPD/network temperatures | Ubuntu sensor kinds present | No vendor-wide sensor certification |
| SMART | Three Ubuntu device reads denied; missing-tool degradation exercised | Successful/unsupported-device branches FIXTURE ONLY; no elevation |

Non-systemd managers, Windows and macOS remain explicitly UNSUPPORTED. No booted
Fedora Workstation, Arch desktop, Tumbleweed desktop, Mint, KDE, Cinnamon or XFCE
installation was available. Native save-picker interaction and end-to-end screen
capture remain NOT TESTED; these limits must travel with any support claim.
