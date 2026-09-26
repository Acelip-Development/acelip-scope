# RC1 Apache-2.0 license validation

Current status (2026-09-26): **RC1 PUBLICATION COMPLETE** for source + Flatpak.
The repository/homepage/Issues are public, private vulnerability reporting is
enabled, and all three required remote workflows passed at the release commit.
AppImage remains withheld. See [RC1-PUBLICATION.md](RC1-PUBLICATION.md).
The validation results, hashes and blockers below are historical evidence for
the named milestone, not the current public release state.

Current namespace and artifact evidence: [NAMESPACE-VALIDATION.md](NAMESPACE-VALIDATION.md).
This document preserves its earlier checkpoint; namespace/URL blockers below
describe the state at that time, not the newly approved namespace target.

Version remains **1.0.0-rc1**, branch `codex/rc1-release-prep`.
Baseline: `1ad52a4d5030d21fbf9112558167069e08ba86ac` (clean), with 274 regression
and 4 Gio integration tests reverified before edits.

**Application license: PASS — Apache-2.0.**
**Copyright 2026 Acelip Development.**
**Dependency redistribution clearance: BLOCKED. Publication: BLOCKED.**

Root LICENSE is byte-identical to the official Apache standard text. Project
NOTICE contains verified attribution and the unmodified pinned CUPS notice.
Source/package metadata, AppStream, About/preferences/build information and
README now declare Apache-2.0; third-party licenses remain separate. AppStream's
CC0-1.0 metadata license is unchanged. No mass source-header changes were made.

288 regression and 4 Gio integration tests pass. New tests cover the exact license
bytes, SPDX/copyright, AppStream, Python metadata, About, README, license gate,
absence of current unresolved-license placeholders, CUPS notice integrity,
package staging/provenance and relocatable runtime license links.

A local wheel built offline with setuptools 78.1.1 reports License-Expression
Apache-2.0 and contains byte-identical LICENSE and NOTICE. No host package was
installed. The minimum source wheel backend is setuptools 77 for PEP 639 support.

AppStream raw validation exits 3 for `url-homepage-missing` (warning) and
`developer-id-missing` (information), with no application-license finding.
Development metadata validation, desktop validation, actionlint 1.7.12,
Python/shell syntax and current-tree privacy audit pass.

## Rebuilt packages

Both formats were rebuilt because their embedded license metadata and files
changed. Artifact source is clean commit
`3b9642d70a1d58a48065fa60dbe6a52706530870`, epoch `1790424764`.
The subsequent documentation commit is identified as final HEAD in the task
handoff; artifacts accurately name their earlier build source.

Both formats built twice with byte-identical package files and `SHA256SUMS`.
SHA-256 was regenerated and independently verified. Prior RC1 packages and their
manifest were preserved under ignored `var/pre-license-rc1-artifacts/`.
Current `dist/` contains only the licensed packages and their manifest.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `acelip-scope-1.0.0-rc1-x86_64.AppImage` | 261,540,344 | `cc4d568e73ab1c2541002edd59be1177458f0315627c8de5ddf347da20fdcca3` |
| `acelip-scope-1.0.0-rc1-x86_64.flatpak` | 69,176 | `fbd7181b8fb0c3aa6e85bcf73614ac953aff0a12879211ebeb1517885914710b` |

- Flatpak: isolated project-local install, default launcher/build-info and full
  packaged GTK acceptance PASS with unchanged sandbox permissions.
- AppImage: extracted-and-run from an unrelated directory using its bundled
  runtime; build-info and full packaged GTK acceptance PASS.
- Both runs asserted Apache-2.0 and the approved copyright in the actual About
  dialog. Widget screenshots were visually inspected. All seven scans, 13 themes,
  preference migration, privacy/AI consent and existing Gio write guards passed.
- Actual installed Flatpak and extracted AppImage inspection confirmed the
  project LICENSE/NOTICE bytes, AppStream project license, identity and build
  provenance. All 2,918 runtime license-tree entries retain identical upstream
  bytes; all 1,453 links now resolve inside the relocated AppImage runtime.
  The launcher license and four upstream NOTICE files are unchanged. The two
  supplemental setuptools NOTICE files describe vendored MPL-2.0/BSD-3-Clause
  code; setuptools's primary MIT license is not applied to that code.

The [execution evidence](validation/rc1-license-execution.json) records separate
package runs and notice verification. These are local automated GUI/write tests;
no new manual picker selection, hardware permission, audio playback or screen
capture claim is made. Historical RC1 limits remain unchanged.

Logs and private screenshots are in ignored `var/license-*`; reproduced builds
are in `var/license-reproduction/`. No application data or host packages were
modified outside the dedicated acceptance-test directories. Runtime notices were
changed only in the copied AppImage tree, not in the installed system runtime.

See [LICENSING-NOTES.md](LICENSING-NOTES.md) and the
[notice inventory](validation/rc1-license-inventory.json) for actual evidence,
selected component versions/licenses and unresolved redistribution questions.
The inventory covers 303 notice groups (286 matched manifest versions), 1,453
absolute links and four NOTICE files across the whole runtime.
Retained texts are not a full SBOM or corresponding-source/attribution clearance.
The FreeType overview references license texts absent from its notice subtree;
that gap remains explicitly unresolved.

Remaining publication gates: dependency redistribution/source/relinking/attribution
clearance and runtime advisory review; final application/developer namespace;
repository/homepage/support URLs; security contact; remote GitHub CI; Git-history
publication review; and explicit publication authorization. The application
license blocker alone is cleared.

The Book remains external development infrastructure. Completion checkpoint and
final clean HEAD are recorded in the task handoff. No push, tag, publication or
GitHub Release is authorized or performed.

## Final verification commands

```sh
python3 -m unittest discover -s tests
python3 -W ignore::DeprecationWarning -m unittest discover -s tests/integration
python3 scripts/check-source.py
python3 scripts/audit-public.py
python3 scripts/render-metadata.py --check
python3 scripts/check-metadata.py
var/v16-tools/actionlint
python3 scripts/package.py checksums
cmp dist/SHA256SUMS var/license-reproduction/SHA256SUMS
```

Application license selection alone changes from BLOCKED to PASS in the current
release checklist. Dependency, namespace/URL/contact, remote CI, Git history and
publication gates remain separate and blocked. Historical checkpoint documents
and execution JSON retain their original pre-approval facts.
