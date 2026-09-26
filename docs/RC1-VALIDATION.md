# Acelip Scope RC1 identity-migration validation (historical snapshot)

Current status (2026-09-26): **RC1 PUBLICATION COMPLETE** for source + Flatpak.
The repository/homepage/Issues are public, private vulnerability reporting is
enabled, and all three required remote workflows passed at the release commit.
AppImage remains withheld. See [RC1-PUBLICATION.md](RC1-PUBLICATION.md).
The validation results, hashes and blockers below are historical evidence for
the named milestone, not the current public release state.

Current namespace and artifact evidence: [NAMESPACE-VALIDATION.md](NAMESPACE-VALIDATION.md).
This document preserves its earlier checkpoint; namespace/URL blockers below
describe the state at that time, not the newly approved namespace target.

This records the pre-license-approval identity milestone. The application license
is now **Apache-2.0**, and its blocker is cleared. Current licensed artifacts,
checksums and remaining gates are in [LICENSE-VALIDATION.md](LICENSE-VALIDATION.md).
The old license/blocker statements below describe that earlier checkpoint only.

**Acelip Scope** · **Acelip Development** · **System diagnostics, made clear.**

**RC BUILD READY — PASS. PUBLICATION READY — BLOCKED.**

Branch: `codex/rc1-release-prep`. Previous name: **LUCY Diagnose**.
Baseline: `ab1c24c07b5b3a09c957ad5934d3befa147227fc`, version `1.6.0-dev`.
All 254 baseline regression tests and 4 Gio integration tests were re-run and
passed before identity changes. The original package hashes were verified and
the existing development project checkpoint lineage was preserved.

## Acceptance and version transition

**274 regression tests + 4 Gio integration tests passed (278 total)**; none of
the original tests was removed. The 20 additional tests cover canonical identity,
namespace/URL blockers, CLI and desktop wrapper, README/workflow identity,
About/provenance, current UI old-name rejection and safe preference migration.
Existing metadata, artifact, report and packaging tests now assert the approved
identity. Packaged GTK tests also assert actual window/title/tagline, About,
Markdown/JSON branding, filename, publisher and migrated preferences.

Before version promotion, both renamed `1.6.0-dev` packages launched successfully,
passed GTK acceptance, built twice with identical bytes and verified checksums
from clean source `f431518c78c3da057ef0b114f58b08407ab84fac`.
See [preflight evidence](validation/rc1-preflight.json). Code/identity, preference,
AppStream exception, privacy and clean-tree gates passed before setting RC1.
One export fixture still asserted the literal development version; it was updated
to the canonical version and the full RC1 suite re-passed before final builds.
A separate short-name field stays null because no abbreviated brand was approved.

## Final artifacts and provenance

Both final packages use clean source **`43a4d6340b1787b4d476cd808f6ccda9c3ff2b46`**.
The final documentation commit follows that build source; final HEAD and the
completion checkpoint ID are supplied in the task handoff. Neither package
claims to include the later documentation commit. Build epoch is recorded in
the machine-readable [execution evidence](validation/rc1-execution.json).

| Artifact in `dist/` | Bytes | SHA-256 |
|---|---:|---|
| `acelip-scope-1.0.0-rc1-x86_64.AppImage` | 261,540,344 | `528a9aa9e3812fe3dd1fb36fc5c3288254246290ae59c100e60bd51799262ca8` |
| `acelip-scope-1.0.0-rc1-x86_64.flatpak` | 64,060 | `d7d241144ae9550276697f8f854dcb731e17565b4bbfabf53c9da5424cc5925a` |

Each format was built twice from the same clean source with the unchanged exact
GNOME 50 and AppImage runtime locks. `cmp` passed for both package files and
`SHA256SUMS`, and hashes were independently re-read and verified. This is byte
reproducibility with the recorded source/toolchain, not a claim about all future
tool versions. Independent outputs are in `var/rc1-final-reproduction/`.
Old `lucy-diagnose-*` packages and their manifest were safely moved from `dist/`
to ignored `var/pre-rename-v16-artifacts/`; intermediate version builds are
separate under `var/`. Current `dist/` contains only the two RC1 artifacts and
`SHA256SUMS`. No historical source document or Git commit was deleted or rewritten.

## Executed launch and UI checks

- Native GTK smoke: PASS on the current Ubuntu/GNOME Wayland desktop before
  promotion; all UI code is unchanged in final packages. The actual generated
  `acelip-scope` native wrapper also reports `Acelip Scope 1.0.0-rc1`, including
  when installed into a temporary path containing spaces.
- Final Flatpak: PASS in an isolated project-local installation with unchanged
  restricted permissions. Default launcher `--version` passed, followed by the
  complete real packaged GTK harness.
- Final AppImage: PASS with its bundled runtime using extraction-and-run from
  an unrelated working directory. Launcher `--version` and complete packaged
  GTK harness passed. This run does not claim a fresh FUSE-mount-path test.
- Both harnesses verified import origin and clean build provenance, all seven
  scan modes, all 13 themes and reloads, first-run System default, live samples,
  privacy/fresh AI consent, manual-sharing cancellation, pause/resume, compact
  and wide layouts, About, real Markdown/JSON Gio writes, cancellation,
  overwrite/etag guards and invalid/unwritable destinations.
- Packaged preference migration: PASS for non-default theme, disabled live
  graphs and local-report preference; old file retired after successful write.
  The automated tests separately cover new-file precedence, absence, invalid
  files, unknown fields, symlinks, write failures/retry and concurrent creation.
  See [PREFERENCE-MIGRATION.md](PREFERENCE-MIGRATION.md).

Screenshots render the app widget tree only. The final About and dashboard views
were visually inspected; they show the approved name, tagline and publisher.
Private QA output stays in ignored `var/rc1-final-*-qa/` and Flatpak private data.
No automatic standing AI consent, upload, privilege elevation or host configuration
change was introduced. Sandbox restrictions and missing/denied host tools remain
coverage limits, not a product test failure. SMART access remained restricted.

The sandbox initially blocked namespaces/display access; only authorized local
build and GUI checks ran outside it. No host package installation was performed.
This phase adds no independent second-distro desktop certification. Historical
v1.6 native picker and Flatpak Markdown selection evidence remains historical;
final RC1 automated file writes are not new manual picker selections. Frame
capture/receiver output, audio playback and successful hardware SMART reads
remain unverified as documented in V1.6-VALIDATION.md.

## Metadata, privacy and source audit

Desktop validation, generated metadata consistency, Python/shell syntax and
**actionlint 1.7.12 passed**. Workflows retain pinned actions and read-only
repository permissions; artifact naming now uses `acelip-scope`. GitHub CI is
**unverified** because no push or repository creation occurred.

Raw `appstreamcli validate --no-net` returns **3**, with exactly:

- `url-homepage-missing` — warning; homepage not approved.
- `developer-id-missing` — informational; no approved developer namespace.

Approved developer display name, product name, summary, descriptions, categories,
keywords, icon/desktop association and release version are present. There are
**no avoidable identity errors**. Development metadata checking permits the
known missing-homepage warning; strict public-release metadata remains BLOCKED.
`LicenseRef-proprietary` is the existing conservative AppStream placeholder,
not a selected application license or redistribution grant.

The old-name source audit is documented in [IDENTITY-AUDIT.md](IDENTITY-AUDIT.md).
Current visible UI and new reports contain no former product branding. Retained
matches are internal modules/classes/CSS, deliberate migration compatibility,
provisional ID/generated metadata, synthetic tests or historical documentation.
The current-tree privacy auditor reports **zero findings**; source review found
no personal hostname attribution, personal home/checkout paths, private IP/MAC,
credentials, tokens, Book endpoints or NAS locations introduced into public text.
Hostname-word overlaps in old branding and synthetic tests were classified by
context rather than deleting valid historical product references. Git-history
and author publication review remain separate unresolved gates.

## Remaining publication blockers

Application license (BLOCKED / NOT SELECTED); final application ID / namespace
and developer identifier; repository, homepage and support URLs; security contact;
dependency redistribution, exact-runtime advisory and corresponding-source
clearance; remote GitHub CI; Git-history/author publication review; and explicit
publication authorization. No account, domain, email, legal entity or public link
was invented. The likely repository name is `acelip-scope` only.

The application ID is centralized and explicitly provisional. The local checkout
path and internal Python modules remain stable. The Book is external development
infrastructure only; no runtime feature, endpoint or dependency was added.

## Git and durable checkpoints

The stable development project was reused. Pre-rename checkpoint:
`203a51dc-88ec-4db4-b73f-430ccbeeef07`, read back successfully. It references the
existing v1.6 completion checkpoint `34ca229b-f8a0-41d8-84ca-965f2f4afacf`.
After the final documentation commit, the completion checkpoint records exact
final HEAD, test counts, artifacts/hashes, migration, AppStream, privacy,
readiness, blockers and clean Git status; its verified ID is in the task handoff.
Nothing was pushed, tagged, published or made into a repository/GitHub Release.

## Reproduction commands

```sh
python3 -m unittest discover -s tests
python3 -W ignore::DeprecationWarning -m unittest discover -s tests/integration
python3 scripts/check-source.py
python3 scripts/audit-public.py
python3 scripts/render-metadata.py --check
python3 scripts/check-metadata.py
var/v16-tools/actionlint
python3 scripts/package.py checksums
cmp dist/SHA256SUMS var/rc1-final-reproduction/SHA256SUMS
```

Build logs: `var/rc1-final-build.log`, `var/rc1-final-reproduction.log`.
Execution logs: `var/rc1-final-flatpak-qa.log`, `var/rc1-final-appimage-qa.log`.
Use a fresh output directory for any new package build; overwrite protection is
unchanged. The test installation and QA directories are private local evidence.

## Files changed from the supplied baseline

- `.github/workflows/package.yml`
- `CHANGELOG.md`
- `README.md`
- `SECURITY.md`
- `SUPPORT.md`
- `data/acelip-scope-symbolic.svg`
- `data/org.lucydiagnose.LucyDiagnose.desktop`
- `data/org.lucydiagnose.LucyDiagnose.metainfo.xml`
- `docs/DEPENDENCIES.md`
- `docs/IDENTITY-AUDIT.md`
- `docs/LICENSING-NOTES.md`
- `docs/LINUX-COMPATIBILITY.md`
- `docs/PACKAGING.md`
- `docs/PREFERENCE-MIGRATION.md`
- `docs/RC1-VALIDATION.md`
- `docs/RELEASE-CHECKLIST.md`
- `docs/validation/rc1-execution.json`
- `docs/validation/rc1-preflight.json`
- `docs/validation/rc1-release-facts.json`
- `lucy_diagnose/__init__.py`
- `lucy_diagnose/__main__.py`
- `lucy_diagnose/exports.py`
- `lucy_diagnose/identity.json`
- `lucy_diagnose/identity.py`
- `lucy_diagnose/platform/linux/analysis_commands.py`
- `lucy_diagnose/platform/linux/guidance.py`
- `lucy_diagnose/platform/linux/sandbox.py`
- `lucy_diagnose/platform/linux/sharing.py`
- `lucy_diagnose/runtime.py`
- `lucy_diagnose/settings.py`
- `lucy_diagnose/sharing_test.py`
- `lucy_diagnose/ui/analysis_panel.py`
- `lucy_diagnose/ui/preferences.py`
- `lucy_diagnose/ui/sharing_panel.py`
- `lucy_diagnose/ui/window.py`
- `packaging/appimage/AppRun`
- `packaging/flatpak/manifest-template.json`
- `packaging/flatpak/org.lucydiagnose.LucyDiagnose.json`
- `pyproject.toml`
- `scripts/check-metadata.py`
- `scripts/install-user.py`
- `scripts/package.py`
- `scripts/release-checklist.py`
- `scripts/render-metadata.py`
- `scripts/validation/manual-acceptance.py`
- `scripts/validation/package-smoke.py`
- `scripts/validation/validate-gui.py`
- `scripts/validation/validate-linux.py`
- `scripts/visual-check.py`
- `tests/test_exports.py`
- `tests/test_hardening.py`
- `tests/test_identity_migration.py`
- `tests/test_linux_v14.py`
- `tests/test_packaging.py`
