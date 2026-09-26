# Dependency inventory

No application dependency is fetched at launch. No unused Python dependency was
found in the declared application requirements. Packaging-only tools and test
helpers remain separate from runtime modules; project-memory tooling is external
development infrastructure and never a Acelip Scope runtime dependency.

| Class | Dependency | Requirement / reason |
|---|---|---|
| Required core | Python >=3.11, standard library | Models, scans, privacy, reports; no PyPI runtime service/client dependency |
| GUI runtime | PyGObject, Pycairo, GTK >=4.10, libadwaita >=1.5 | Native UI, asynchronous save dialogs, graphs; GLib/Gio transitively |
| Optional host probes | systemctl/journalctl, dpkg/rpm/pacman, ps/findmnt/lsblk, ip/ping/resolvectl/ss | Capability-specific Linux observations; absence is normalized |
| Optional hardware/audio | sensors, smartctl, nvidia-smi, wpctl or pactl | Read only; ordinary permissions; no automatic playback |
| Optional desktop integration | Session bus, desktop portals, PipeWire/WirePlumber | Export chooser and sharing prerequisites; no autonomous capture |
| Optional AI tools | Installed external clients or loopback Ollama | Detection and reviewed handoff only; no inference dependency |
| Source wheel build only | setuptools >=77 (PEP 639 SPDX metadata) | pyproject backend; canonical package builds copy source and do not invoke pip/setuptools |
| Packaging only | Flatpak CLI, exact GNOME 50 Platform, mksquashfs, readelf | Locked runtime, deterministic bundles, retained ELF dependency checks |
| AppImage runtime only | Checksum-pinned type-2 runtime | Mount/extract and execute bundled application; independent of host Python/GTK |
| Development only | unittest, Git, desktop-file-validate, appstreamcli, optional actionlint | Tests, metadata, CI checks; actionlint download is checksum-pinned |
| Optional GUI CI | Xvfb, dbus-run-session | Headless smoke, never claimed as real desktop validation |

The exact GNOME runtime and AppImage inputs are in `packaging/runtime-lock.json`.
Its retained `manifest.json`, Python distribution metadata and `share/licenses/`
provide component/version/source notices. `docs/validation/v1.6-runtime-size.json`
records the input inventory. No dependency upgrades were made to chase newer
versions. Only the explicit AppImage prune manifest removes reviewed unused
WebKit/JavaScriptCore/Yelp families; all retained ELF consumers are checked.

The repository security check is not a vulnerability database scan. There are no
pip-installed application dependencies to meaningfully audit with a requirements
file; stdlib/GI/native runtime CVEs require GNOME/freedesktop and distribution
advisory review. Bundled ancillary Python/native components still need that
review before public release. No claim of a vulnerability-free runtime is made.
Do not change runtime locks without repeating reproducibility and compatibility
checks. Public redistribution/source obligations are in LICENSING-NOTES.md.
