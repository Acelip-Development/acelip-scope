# LUCY Diagnose packaging (1.5.0-dev)

The offline entry points build the real GTK4/libadwaita app. They never install
host packages, invoke sudo, publish, tag, or push. The provisional project ID is
`org.lucydiagnose.LucyDiagnose`; no domain ownership or public GitHub repository
is implied. Confirm publisher identity before a public release. The application
name remains **LUCY Diagnose**.

## Prerequisites and locked inputs

- Linux x86_64, Python >=3.11 with PyGObject/GLib, Git and Flatpak CLI (validated with 1.16.6).
- The installed GNOME 50 **Platform** at the exact OSTree commit in
  `packaging/runtime-lock.json`. It supplies Python 3.13, PyGObject, Pycairo,
  GTK4, libadwaita and their dependencies. Builds refuse a different commit;
  they never download or update a runtime silently.
- AppImage additionally needs `mksquashfs` with zstd support and the official
  type-2 runtime file whose SHA-256 is locked in that same JSON file.
- Desktop integration validation: `desktop-file-validate`, `appstreamcli`.
- GUI validation: an accessible Wayland or X11 desktop; package launch needs no
  root. Flatpak needs working unprivileged namespaces. A surrounding execution
  sandbox may block its icon validator or session instance directory.

The AppImage runtime URL uses an upstream rolling release, but its accepted
**bytes are pinned**, including upstream commit identity. Fetch it explicitly
into a local tools directory and verify it before use:

```sh
mkdir -p var/packaging-tools
curl --fail --location --output var/packaging-tools/runtime-x86_64 \
  https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64
printf '%s  %s\n' \
  1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf \
  var/packaging-tools/runtime-x86_64 | sha256sum --check
```

If the upstream asset changes, stop. Obtain the locked artifact from a trusted
cache or review a lock update; do not accept a new digest automatically. The build
script independently verifies the digest. Missing dependencies produce a clear
`BLOCKED`/failure message; no placeholder packages are created.

## Build and verify

From a clean checkout at the intended source commit:

```sh
./scripts/package-all.sh
# Or build one format into its own fresh output directory:
./scripts/build-flatpak.sh --dist dist/flatpak
./scripts/build-appimage.sh --dist dist/appimage
```

`APPIMAGE_RUNTIME=/absolute/path/to/runtime-x86_64` selects an already downloaded
runtime. The default is `var/packaging-tools/runtime-x86_64`. `--dist` defaults to
`dist/`. Existing artifact names or checksum manifests are never replaced. To
repeat a build, select a new output directory. Each invocation uses a private
temporary child of `build/packaging/` and removes only that child, including after
failure. No caller-supplied directory is recursively deleted.

Artifacts are:

- `lucy-diagnose-1.5.0-dev-x86_64.flatpak`
- `lucy-diagnose-1.5.0-dev-x86_64.AppImage`
- `SHA256SUMS` (exact filenames, generated and re-read/verified after building)

```sh
(cd dist && sha256sum --check SHA256SUMS)
python3 scripts/package.py checksums --dist dist
```

The last command also refuses to rewrite a changed checksum manifest. Generated
artifacts, temporary source trees and caches are covered by existing `dist/`,
`build/`, and `var/` Git ignores. Only x86_64 is currently locked and validated;
other architectures fail rather than using incompatible runtime bytes.

## Reproducibility and provenance

Both builders normalize file times to `SOURCE_DATE_EPOCH`, defaulting to the
source Git commit timestamp. Flatpak export uses that timestamp; SquashFS uses
fixed uid/gid, timestamps, compressor and thread count. Flatpak 1.16.6 adds a
separate OSTree bundle-generation timestamp that ignores SOURCE_DATE_EPOCH;
the builder parses the unsigned superblock with GLib and normalizes only that
field, preserving all other serialized children and the content commit. Unknown
layouts are rejected. This happens before artifact checksumming or future signing. Build scripts operate
without network access. The AppImage copies the complete pinned GNOME Platform,
including its license notices, instead of relying on the host Python/GTK ABI.
Reproduction requires the same source, runtime bytes, epoch and tool versions;
validation records whether repeated builds actually matched.

About (header info button) and `--build-info` show version, development/release
build type, full Git commit, clean/modified source state, packaging format,
GNOME/host runtime, platform backend and host access. No build directory, user
name or personal filesystem path is embedded in this record. A package built
from uncommitted edits says **Modified**. An unstamped checkout does not invent
a commit. Python safe-path mode prevents importing a nearby checkout when an
AppImage is launched from a source directory.

## Flatpak build and manifest

The canonical offline builder uses `flatpak build-init`, `build-finish`,
`build-export` and `build-bundle`. This pure Python project needs no compilation,
so the installed Platform also serves as the build environment. **No SDK or
flatpak-builder installation is needed for this path.**

`packaging/flatpak/org.lucydiagnose.LucyDiagnose.json` is a conventional
flatpak-builder manifest with `org.gnome.Sdk//50` for environments that already
have it. Its alternate SDK/builder route is not the pinned/reproduced route in
this validation. Export a source tree with `LUCY_BUILD_COMMIT` and
`SOURCE_DATE_EPOCH` explicitly supplied when Git metadata is unavailable.
The command, application data, metadata and permission list are shared with the
canonical build. No host diagnostic tools are prerequisites for app startup.

Flatpak supplies the GNOME runtime as a Flatpak dependency at installation; the
small single-file bundle does not contain that runtime. Standard Flatpak runtime
installation is distinct from installing distribution packages on the host.
For offline installation the runtime must already be available. The bundle
includes a Flathub runtime-repository reference; no application remote is
published or added by the build.

## Flatpak permissions and host coverage

The shipped permissions are **Wayland**, **fallback X11**, and **IPC** for X11
shared-memory rendering, plus `GTK_USE_PORTAL=1`. There is **no** host/home
filesystem grant, device grant, network sharing, system bus, unrestricted session
bus, service-manager permission, direct PipeWire/Pulse socket, or `flatpak-spawn`
escape. Fallback X11 has the usual weaker desktop isolation when used; prefer
Wayland. No DRI permission is needed with the process-local Cairo renderer.

| Capability | Packaged behavior |
|---|---|
| `/proc` | Aggregate CPU/memory counters may be visible; private process namespace. Observations explicitly PARTIAL, never complete host process coverage. |
| `/sys`, `/sys/class/hwmon` | Read only what is exposed. Visible sensor readings are PARTIAL; hidden sensors are UNAVAILABLE. No device grants added. |
| OS identity | Runtime OS is labeled as runtime, not mistaken for the host distribution. |
| System/user services, journal | UNAVAILABLE with Flatpak restriction evidence; no false failed-service reports. |
| Package databases, AI executables/services, Discord packages | UNAVAILABLE; runtime absence is not proof a host package is absent. |
| Mounts, block devices, SMART | UNAVAILABLE; no raw-device or host filesystem access, no escalation. |
| GPU telemetry/device nodes | UNAVAILABLE under this profile; desktop rendering still works. |
| Network interfaces/reachability | UNAVAILABLE; no network permission, so host connectivity is not inferred. |
| PipeWire/WirePlumber/audio clients | Host service/socket/backend inspection restricted. No automatic playback or socket activation. |
| Desktop portals | Read-only ScreenCast property query with NO_AUTO_START. A visible property proves only advertised capability, not capture. Host implementation names may be hidden. |
| Saving reports | Gtk.FileDialog delegates to the desktop FileChooser portal. Only explicitly selected destinations are granted. |
| Capture | LUCY does not capture frames. Its existing consent/manual verification flow remains intact. Actual ScreenCast use belongs to the user's sharing application. |

Linux owns the restriction policy. Shared core and Windows/macOS placeholders
remain independent of Linux probes. Restricted probes produce normalized
UNAVAILABLE/PARTIAL coverage with "This diagnostic is restricted by the Flatpak
sandbox." They do not manufacture health ERRORs or recommend privilege changes.
User permission overrides are not treated as a promise of full host inspection;
the package intentionally retains conservative coverage.

## AppImage behavior and limitations

The type-2 AppImage mounts or extracts without installing LUCY system-wide. It
bundles the pinned Python, GTK/libadwaita libraries, GI typelibs, data and all 13
themes. A bundled ELF loader applies only to the application interpreter; native
diagnostic subprocesses retain host PATH/libraries. Optional native tools such
as `smartctl`, `sensors`, `wpctl`, `pactl` and `nvidia-smi` are deliberately not
replaced by copies from a foreign userspace. Missing tools yield ordinary
UNAVAILABLE results. SMART uses normal user permissions with no escalation.

The package uses host fonts/fontconfig configuration and the host compositor.
It defaults to Cairo rendering to avoid coupling bundled Mesa with host GPU
drivers. It is intentionally large because the complete Platform is bundled.
FUSE support is normally needed for direct mounting; upstream's supported
`--appimage-extract-and-run` option works without FUSE, requires temporary disk
space, and is slower. An AppImage is **not a sandbox**. Its own read-only FUSE mount is identified
as application storage, so its expected 100% occupancy is not a host disk error.
Other filesystems retain normal capacity checks.

Packaged preferences use `$XDG_CONFIG_HOME/lucy-diagnose`, logs use
`$XDG_STATE_HOME/lucy-diagnose`, and cache settings respect XDG. Flatpak remaps
these into the app's private data. The native checkout retains its prior `var/`
preferences behavior. No app state is written beside a read-only package.

Only the actual tested environments in `V1.5-VALIDATION.md` are claimed. A
rootless Fedora userspace sharing the Ubuntu compositor is not an independent
Fedora desktop session, service manager, audio stack or kernel.

## Save safety, privacy and desktop metadata

Saving requires an explicit preview and destination. Creation is exclusive.
Existing destinations require an additional explicit replacement response;
replacement uses an etag to reject concurrent edits. Cancellation writes
nothing. Permission and invalid-destination failures stay visible in the UI.
Export preparation/privacy filtering and fresh AI consent remain unchanged.
The optional AI command handoff still does not execute or transmit anything.

The desktop entry, AppStream XML and scalable project-owned SVG are under
`data/`. SVG supplies all requested desktop icon sizes without external assets.
Desktop metadata validates. AppStream has a deliberately documented
`url-homepage-missing` warning and `developer-info-missing` informational issue:
there is no public URL or settled publisher to truthfully put there. XML and
required metadata are regression-tested. Do not mask these release-readiness
items with fabricated links.

`metadata_license` covers the new XML as CC0-1.0. The application currently has
no explicit redistribution license; `LicenseRef-proprietary` is a conservative
placeholder, **not** a new open-source license grant. Publisher, application
license and public URLs must be settled before public distribution. Bundled
third-party runtime notices are retained. No GitHub Release is created here.

Packaging adds no telemetry, credential collection, automatic reports, AI
transmission, privileges or host settings writes. AppImage preserves the
pre-existing scan network behavior: limited ICMP to the gateway/1.1.1.1 and
local Ollama discovery in relevant scans. Flatpak's profile blocks network
access entirely. Runtime download/build tooling does not run at app launch.

## Explicit integration validation

Every package includes the opt-in acceptance harness. It saves reports and
renders widget screenshots only when invoked with an explicit empty QA directory:

```sh
./dist/lucy-diagnose-1.5.0-dev-x86_64.AppImage --smoke-test
./dist/lucy-diagnose-1.5.0-dev-x86_64.AppImage --package-smoke \
  --output /absolute/path/to/empty-qa-directory --label appimage
# From an explicitly installed Flatpak:
flatpak run org.lucydiagnose.LucyDiagnose --smoke-test
flatpak run --command=python3 org.lucydiagnose.LucyDiagnose -P \
  /app/share/lucy-diagnose/validation/package-smoke.py \
  --output /var/data/empty-qa-directory --label flatpak
```

The harness tests all scan modes, themes/persistence, export previews and real
Gio writes, replacement cancellation/confirmation, etag conflicts, invalid and
unwritable destinations, pause/resume, consent, compact/wide layouts and About.
It opens/cancels the real FileChooser programmatically; successful manual picker
selection and end-to-end capture must be reported separately. Neither CI
fixtures nor this cancellation check establish those unperformed interactions.

Primary specifications:
[Flatpak bundles](https://docs.flatpak.org/en/latest/single-file-bundles.html),
[Flatpak dependencies](https://docs.flatpak.org/en/latest/dependencies.html),
[AppImage architecture](https://docs.appimage.org/reference/architecture.html).
