# RC1 final namespace preparation

Current status (2026-09-26): **RC1 PUBLICATION COMPLETE** for source + Flatpak.
The repository/homepage/Issues are public, private vulnerability reporting is
enabled, and all three required remote workflows passed at the release commit.
AppImage remains withheld. See [RC1-PUBLICATION.md](RC1-PUBLICATION.md).
The validation results, hashes and blockers below are historical evidence for
the named milestone, not the current public release state.

Product **Acelip Scope**, publisher **Acelip Development**.
Version **1.0.0-rc1**, license **Apache-2.0**, branch `codex/rc1-release-prep`.
Baseline `c0015975a2a0ac542c9b886f91f90d64d532a50d` was clean; all 288 regression
and 4 Gio integration tests were reverified before editing.

## Approved targets versus live services

| Field | Approved target / current state |
|---|---|
| Application ID | `io.github.acelip_development.acelip-scope` — PASS |
| Developer ID | `io.github.acelip_development` — PASS |
| GitHub namespace | `Acelip-Development/acelip-scope` — PASS as a target only |
| Repository URL target | `https://github.com/Acelip-Development/acelip-scope` |
| Homepage strategy | Use that repository after creation/reachability verification |
| Support strategy | GitHub Issues, derived as repository target plus `/issues` |
| Security strategy | GitHub private vulnerability reporting if available and enabled after creation |
| Remote repository created | BLOCKED — not created in this change |
| Homepage/support reachable | BLOCKED — not yet created or verified |
| Security reporting configured | BLOCKED — no contact/route advertised |

The organization and repository are not represented as existing. No separate
website, personal email or organization email was invented. `identity.json`
contains the approved repository target and the homepage/support/security
strategies; `planned_urls()` derives the future routes. `public_urls()` requires
separate remote-created and reachability flags before outputting public links.
These flags are false. AppStream omits all target URLs until the appropriate
remote checks pass. Approved namespace is not proof of remote ownership/existence.

Desktop, AppStream, icon exports, Flatpak manifest filename/ID, GTK application
ID and package provenance use the final ID. Internal Python modules stay stable.
AppStream's developer field now includes the approved developer ID and name;
Apache-2.0 remains the project license, with CC0-1.0 for metadata only.

## Validation scope

**311 regression + 4 Gio integration tests pass (315 total)**; all 288 + 4
baseline tests are preserved, with 23 new regression tests.
New coverage checks ID validity, AppStream developer/launchable identity,
manifest/desktop/icon alignment, staged package absence of obsolete IDs, target
URL generation and gating, and complete preference-transfer chains/failure cases.
Native GTK smoke, both package launches, all 13 themes, preference reloads and
Markdown/JSON export acceptance passed. Local actionlint 1.7.12, Python/shell
syntax, metadata consistency and the current-tree privacy audit passed.
Remote CI remains unverified.

AppStream now reports only `url-homepage-missing` (warning), raw exit 3.
`developer-id-missing` is resolved; project license and final IDs validate.
The warning is retained rather than masked with a nonexistent homepage.

## Preference continuity

Native `var/` and AppImage XDG preferences remain at their existing locations.
The final Flatpak ID has a new sandbox config root. Before first launch, close
both apps and run `python3 scripts/migrate-flatpak-preferences.py` on the host.
This explicit helper copies only validated preferences when the destination is
absent, preserves old-install preferences, rejects unsafe/invalid sources and
never broadens package permissions. Fresh installs retain System defaults. It is
not a silent automatic cross-sandbox migration; see
[PREFERENCE-MIGRATION.md](PREFERENCE-MIGRATION.md) for commands and precedence.
There is no persisted AI consent; fresh per-preview consent remains required.

## Obsolete-ID audit

Searched the current tracked/nonignored tree for the old application/desktop/
Flatpak ID `org.lucydiagnose.LucyDiagnose` and provisional-namespace statements.

- Current runtime and generated package metadata: old ID removed; final ID used.
- Host preference migration helper: intentional historical source ID only;
  this script is not copied into packages.
- Migration documentation/tests: explicit old-to-provisional-to-final lineage.
- Historical RC1/license/V1.2–V1.6 reports, inventory/execution snapshots and
  file lists: retained as evidence of what was built at that time. Updated
  historical report banners point to this current namespace report.
- Existing ignored artifacts/QA directories: historical private outputs, not
  current package contents. New artifacts replace `dist/` only after preserving
  prior files and hashes in a separate ignored archive.

The generic internal module name `lucy_diagnose` is not an application ID and
remains unchanged. No old-ID desktop/manifest resource remains in `data/` or the
active Flatpak manifest. No Git history or author identity was rewritten.

## Remaining publication gates

Remote organization/repository creation; homepage and Issues reachability;
private security configuration; remote GitHub CI; Git-history publication review;
dependency redistribution/source/relinking/attribution clearance (including the
recorded FreeType license-text question) and runtime advisory review; publication
authorization. The approved IDs, publisher/name/tagline, namespace target and
Apache-2.0 license do not clear those independent gates.

No Git remote was configured, no push/tag/release/publication performed, and no
GitHub organization or repository was created. The Book remains development
backup only; completion checkpoint and final HEAD are reported in the task handoff.

## Final packages and reproducibility

**NAMESPACE PREPARATION READY. RC BUILD READY. PUBLICATION BLOCKED.**

Both formats built twice from clean source
`b0f72aae3080217b0275ecd380e0fd97bc443554`, epoch `1790425742`, using unchanged
runtime locks. Final HEAD includes a later documentation-only evidence commit;
packages correctly report their actual earlier build source.

| Current artifact | Bytes | SHA-256 |
|---|---:|---|
| `acelip-scope-1.0.0-rc1-x86_64.AppImage` | 261,540,344 | `8af98e4a3cf8a059034fde0af2271684e111608c816d1d5a041027ff8c670593` |
| `acelip-scope-1.0.0-rc1-x86_64.flatpak` | 69,808 | `eb9f9dbb3b55860e0fd6841905c7ae980515112db3c906dfc20265ebd881958d` |

Direct `cmp` passed for both package files and their checksum manifests against
`var/namespace-reproduction/`. `dist/SHA256SUMS` was generated and verified from
the new files. The prior licensed RC1 artifacts and checksums were preserved
under `var/pre-namespace-rc1-artifacts/`, outside the current `dist/`.

The final-ID Flatpak was installed in an isolated project-local store. Its
default launcher/build-info succeeded under the shipped minimal sandbox profile.
AppImage launched using its bundled runtime via extraction-and-run from an
unrelated working directory; no fresh FUSE-mount-path validation is claimed.
Both real packaged GTK harnesses passed all seven scans, 13 themes and saved
preferences, fresh System default, live samples, pause/resume, privacy/fresh AI
consent, Markdown/JSON previews and real Gio writes, cancel/overwrite/etag and
invalid/unwritable safeguards, and current About/build identity. Final About
widget screenshots were visually inspected. Hardware/manual limits from prior
reports remain unchanged; no new manual picker/capture/playback claim is made.

Actual installed Flatpak and extracted AppImage contents were checked for
manifest/desktop/metainfo/icon/launchable alignment, final developer ID,
Apache-2.0, intact project LICENSE/NOTICE, clean provenance and absent obsolete
IDs throughout the application payload/resources. AppImage top-level desktop,
SVG and `.DirIcon` also match. Flatpak's exported desktop launcher and metadata
use the final ID. No migration filesystem/device/network permission was added.
These checks inspected actual artifacts, not only source fixtures.

## Executed transfer and privacy evidence

An isolated home fixture began with the old working-name preference file.
Runtime migration produced the provisional Acelip preference file; the host
helper then copied it into the final-ID config location. Non-default theme,
local-report privacy and disabled live graphs were preserved. Repeated execution
left the destination unchanged and retained the provisional install's file.
The actual final-ID Flatpak then loaded all transferred preferences successfully.
Its test process selected a dedicated synthetic XDG root before importing settings
(Flatpak controls its initial XDG environment). This proves the packaged settings
reader consumes the transfer; it does not claim that production user settings
were changed, or that the sandbox automatically reads another app's data.

Unit tests additionally cover direct old-to-final transfer, newer-source
precedence, existing destination precedence, invalid newer data, dry run,
missing stores/System defaults, failed writes, concurrent destination creation,
symlink rejection and discarding unknown/standing-consent fields. Native and
AppImage config locations remain independent of GTK ID.

The current-tree privacy audit has zero findings. No personal identifiers,
private service endpoints or project-backup data were introduced. The only
current source literal for the old app ID is the explicit, unshipped host helper;
historical documents and transfer examples are classified above. No production
preference files, old app installation, host settings or runtime locks were altered.
Private QA output remains under ignored `var/namespace-*` and dedicated Flatpak
test-data directories. The new [execution record](validation/rc1-namespace-execution.json)
contains path-free package and transfer outcomes.

## Verification commands

```sh
python3 -m unittest discover -s tests
python3 -W ignore::DeprecationWarning -m unittest discover -s tests/integration
python3 scripts/check-source.py
python3 scripts/audit-public.py
python3 scripts/render-metadata.py --check
python3 scripts/check-metadata.py
var/v16-tools/actionlint
python3 scripts/package.py checksums
cmp dist/SHA256SUMS var/namespace-reproduction/SHA256SUMS
```

Build logs: `var/namespace-build.log`, `var/namespace-reproduction.log`.
Package runs: `var/namespace-flatpak-qa.log`, `var/namespace-appimage-qa.log`.
Native smoke: `var/namespace-native-smoke.log`. Readiness flags never infer remote
existence from a prepared URL; remote creation/configuration requires a later
explicitly authorized task.
